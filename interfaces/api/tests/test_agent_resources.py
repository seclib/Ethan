"""Tests API — sélection explicite des ressources d'un Agent (v1.py).

Exécute les vrais managers Core (stores mémoire) via le router v1 : création
d'agents avec resources typées (folder_ids, knowledge_ids, tool_ids,
knowledge_collection_ids), validation 422 des ressources inconnues, et
endpoint GET /agents/{id}/resources (arbre résolu par le Core).
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from routers import v1
from interfaces.api.routers.folders import set_folder_manager
from core.agents import AgentManager
from core.folders import FolderManager
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


class _FakeToolManager:
    def __init__(self, tools: dict[str, dict]) -> None:
        self._tools = tools

    def get_tool(self, tool_id: str):
        return self._tools.get(tool_id)

    def list_tools(self):
        return list(self._tools.values())


TOOLS = {
    "tool-web": {
        "id": "tool-web", "name": "web_search",
        "description": "Recherche web", "provider": "builtin",
    },
}


@pytest.fixture(autouse=True)
def real_services():
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    knowledge = KnowledgeManager(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    folders = FolderManager(
        store=store, knowledge=knowledge, collections=collections
    )
    tool_manager = _FakeToolManager(TOOLS)

    v1.set_core_domain_services(v1.CoreDomainServices(
        agents=AgentManager(store=store), knowledge=knowledge, rag=rag,
    ))
    v1.set_knowledge_collections(collections)
    set_folder_manager(folders)
    v1.set_tool_manager(tool_manager)
    yield {"folders": folders, "knowledge": knowledge, "collections": collections}

    v1.set_core_domain_services(v1.CoreDomainServices())
    v1.set_knowledge_collections(None)
    set_folder_manager(None)
    v1.set_tool_manager(None)


# ── (SUITE) ──────────────────────────────────────────────────────────────────

def test_create_agent_with_explicit_resource_selection():
    """POST /agents : les ressources sélectionnées sont persistées typées."""
    folder_id = asyncio.run(_create_folder())
    agent = asyncio.run(v1.create_agent({
        "name": "Scoped Agent", "provider": "fake",
        "knowledge_ids": [], "tool_ids": ["tool-web"], "folder_ids": [folder_id],
    }))
    assert agent["tool_ids"] == ["tool-web"]
    assert agent["folder_ids"] == [folder_id]
    assert agent["knowledge_ids"] == []


async def _create_folder():
    folder = await v1.get_folder_manager().create_folder("Kit")
    return folder["id"]


def test_create_agent_rejects_unknown_resources():
    """Knowledge ou tool inconnu → 422 (validation stricte)."""
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_agent({
            "name": "Bad Knowledge", "knowledge_ids": ["ghost-node"],
        }))
    assert exc.value.status_code == 422

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_agent({
            "name": "Bad Tool", "tool_ids": ["ghost-tool"],
        }))
    assert exc.value.status_code == 422

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_agent({
            "name": "Bad Folder", "folder_ids": ["ghost-folder"],
        }))
    assert exc.value.status_code == 422


def test_agent_resources_endpoint_shows_effective_tree():
    """GET /agents/{id}/resources : deux agents, deux arbres différents —
    l'un via dossier (contenu inclus), l'autre via sélection explicite."""
    folders = v1.get_folder_manager()
    knowledge = v1._domains.knowledge
    collections = v1.get_knowledge_collections()
    rag = v1._domains.rag

    folder = asyncio.run(folders.create_folder("Recon Kit", user_id="alice"))
    node = asyncio.run(knowledge.create("Protocole", content="Étapes de recon."))
    doc = asyncio.run(rag.ingest("DNS et certificats.", title="Recon"))
    col = asyncio.run(collections.create_collection("Recon Docs", user_id="alice"))
    asyncio.run(collections.add_document(col["id"], doc.id))
    asyncio.run(folders.attach_resource(folder["id"], "knowledge", node.id))
    asyncio.run(folders.attach_resource(folder["id"], "collection", col["id"]))

    agent_a = asyncio.run(v1.create_agent({
        "name": "Folder Agent", "folder_ids": [folder["id"]],
    }))
    agent_b = asyncio.run(v1.create_agent({
        "name": "Explicit Agent",
        "knowledge_ids": [node.id],
        "tool_ids": ["tool-web"],
    }))

    tree_a = asyncio.run(v1.get_agent_resources(agent_a["id"]))
    assert [f["name"] for f in tree_a["folders"]] == ["Recon Kit"]
    assert [k["name"] for k in tree_a["knowledge"]] == ["Protocole"]
    assert [c["id"] for c in tree_a["collections"]] == [col["id"]]
    assert tree_a["tools"] == []
    assert all(k["source"].startswith("folder:") for k in tree_a["knowledge"])

    tree_b = asyncio.run(v1.get_agent_resources(agent_b["id"]))
    assert tree_b["folders"] == []
    assert [k["id"] for k in tree_b["knowledge"]] == [node.id]
    assert all(k["source"] == "explicit" for k in tree_b["knowledge"])
    assert [t["id"] for t in tree_b["tools"]] == ["tool-web"]
    assert tree_b["collections"] == []

    # Ressource existante non sélectionnée : jamais dans l'arbre d'un agent.
    assert tree_b["collections"] != tree_a["collections"]

    # Agent inconnu → 404
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.get_agent_resources("ghost"))
    assert exc.value.status_code == 404


def test_update_agent_resource_fields():
    """PUT /agents/{id} : ajout puis retrait de ressources autorisées."""
    agent = asyncio.run(v1.create_agent({"name": "Editable"}))
    updated = asyncio.run(v1.update_agent(agent["id"], {
        "tool_ids": ["tool-web"],
    }))
    assert updated["tool_ids"] == ["tool-web"]

    cleared = asyncio.run(v1.update_agent(agent["id"], {"tool_ids": []}))
    assert cleared["tool_ids"] == []
