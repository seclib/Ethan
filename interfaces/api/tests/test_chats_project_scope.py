"""Tests API — scope Project des conversations (/chats + chat/completions).

Vérifie que le Project est un vrai conteneur de conversations :
- création d'une conversation rattachée (`POST /chats`) ;
- filtrage de la liste par `project_id` ;
- rattachement d'une conversation orpheline (`PUT /chats/{id}`) ;
- rattachement au moment du streaming SSE, et priorité du projet existant
  (une conversation ne change jamais de projet — isolation des historiques).

Handlers appelés directement (pattern du dépôt), vrai ChatStore + vrai
ProjectManager sur CoreRecordStore mémoire — aucun mock du domaine.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from core.chat import ChatPipeline
from core.projects import ProjectManager
from core.state import CoreRecordStore
from core.state.chats import ChatStore
from interfaces.api.routers import domains as domains_module
from interfaces.api.routers import v1 as v1_router
from interfaces.api.routers.domains import set_domain_managers
from interfaces.api.routers.projects import set_project_manager


def _request(user: str | None = "alice") -> SimpleNamespace:
    """Stub minimal de ``Request`` : ``request.state.user`` est lu."""
    return SimpleNamespace(state=SimpleNamespace(user=user))


async def _consume(response) -> str:
    """Consomme une StreamingResponse et retourne le corps SSE brut."""
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    if chunks and isinstance(chunks[0], str):
        return "".join(chunks)
    return b"".join(chunks).decode("utf-8", errors="replace")


@pytest.fixture()
def services():
    """Vrais managers Core injectés dans les routers (nettoyés après le test)."""
    store = CoreRecordStore()
    chat_store = ChatStore(store=store)
    project_manager = ProjectManager(store=store)
    set_domain_managers(chats=chat_store)
    set_project_manager(project_manager)
    yield chat_store, project_manager
    set_domain_managers(chats=None)
    set_project_manager(None)


def test_create_chat_attaches_project(services):
    """POST /chats accepte `project_id` et le persiste (ChatStore Core)."""
    chat_store, project_manager = services

    async def scenario():
        project = await project_manager.create_project(user_id="alice", name="API")
        chat = await domains_module.create_chat(
            {"title": "Conversation API", "project_id": project["id"]},
            _request("alice"),
        )
        assert chat["project_id"] == project["id"]
        stored = await chat_store.get_chat(chat["id"])
        assert stored is not None
        assert stored["project_id"] == project["id"]

    asyncio.run(scenario())


def test_list_chats_filters_by_project(services):
    """GET /chats?project_id=… n'expose que les conversations du projet."""
    chat_store, project_manager = services

    async def scenario():
        pa = await project_manager.create_project(user_id="alice", name="Alpha")
        pb = await project_manager.create_project(user_id="alice", name="Beta")
        chat_a = await chat_store.create_chat("A", user_id="alice", project_id=pa["id"])
        await chat_store.create_chat("B", user_id="alice", project_id=pb["id"])

        listing = await domains_module.list_chats(
            user_id="alice", folder_id=None, archived=None, project_id=pa["id"]
        )
        assert [c["id"] for c in listing] == [chat_a["id"]]

    asyncio.run(scenario())


def test_list_chats_unassigned_scope(services):
    """GET /chats?unassigned=true n'expose que les conversations hors projet."""
    chat_store, project_manager = services

    async def scenario():
        project = await project_manager.create_project(user_id="alice", name="Scope")
        await chat_store.create_chat("Projet", user_id="alice", project_id=project["id"])
        orphan = await chat_store.create_chat("Défaut", user_id="alice")

        listing = await domains_module.list_chats(
            user_id="alice", folder_id=None, archived=None, unassigned=True
        )
        assert [c["id"] for c in listing] == [orphan["id"]]

    asyncio.run(scenario())


def test_update_chat_binds_orphan_project(services):
    """PUT /chats/{id} rattache une conversation orpheline à un projet."""
    chat_store, project_manager = services

    async def scenario():
        project = await project_manager.create_project(user_id="alice", name="Binding")
        chat = await chat_store.create_chat("Orpheline", user_id="alice")
        updated = await domains_module.update_chat(chat["id"], {"project_id": project["id"]})
        assert updated["project_id"] == project["id"]

    asyncio.run(scenario())


def test_stream_attaches_project_to_new_chat(services):
    """Le streaming SSE crée la conversation rattachée au projet demandé."""
    chat_store, project_manager = services

    async def scenario():
        project = await project_manager.create_project(user_id="alice", name="SSE")
        pipeline = ChatPipeline(chat_store=chat_store)
        pipeline.set_project_manager(project_manager)
        v1_router.set_chat_pipeline(pipeline)
        try:
            response = await v1_router.chat_completions_stream(
                {"message": "Bonjour", "user_id": "alice", "project_id": project["id"]}
            )
            await _consume(response)
        finally:
            v1_router.set_chat_pipeline(None)

        chats = await chat_store.list_chats(user_id="alice", project_id=project["id"])
        assert len(chats) == 1
        branch = await chat_store.get_branch(chats[0]["id"])
        assert branch[0]["metadata"]["project_id"] == project["id"]

    asyncio.run(scenario())


def test_stream_existing_chat_keeps_its_project(services):
    """Une conversation existante garde son projet même si la requête en vise un autre."""
    chat_store, project_manager = services

    async def scenario():
        pa = await project_manager.create_project(user_id="alice", name="Alpha")
        pb = await project_manager.create_project(user_id="alice", name="Beta")
        chat = await chat_store.create_chat("Alpha", user_id="alice", project_id=pa["id"])

        pipeline = ChatPipeline(chat_store=chat_store)
        pipeline.set_project_manager(project_manager)
        v1_router.set_chat_pipeline(pipeline)
        try:
            response = await v1_router.chat_completions_stream(
                {
                    "message": "Suite",
                    "user_id": "alice",
                    "chat_id": chat["id"],
                    "project_id": pb["id"],
                }
            )
            await _consume(response)
        finally:
            v1_router.set_chat_pipeline(None)

        record = await chat_store.get_chat(chat["id"])
        assert record is not None
        assert record["project_id"] == pa["id"]

    asyncio.run(scenario())
