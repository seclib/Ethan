"""Tests Core — Projects : conversations rattachées, contexte, isolation.

Couvre les 12 scénarios de validation du système Projects :

1.  création d'un Project ;
2.  modification (instructions, agent, provider, modèle…) ;
3.  suppression (conversations conservées — orphan-safe) ;
4.  ajout de fichier (pipeline RAG Core, pas de second indexeur) ;
5.  nouvelle conversation rattachée au projet ;
6.  plusieurs conversations indépendantes dans un même projet ;
7.  héritage du contexte projet (instructions injectées, sans fusion
    d'historiques) ;
8.  sélection du modèle (défaut projet vs requête explicite) ;
9.  sélection de l'agent (défaut projet vs requête explicite) ;
10. isolation entre Projects (conversations + documents) ;
11. persistance après redémarrage applicatif (re-instanciation des
    managers sur le même store durable) ;
12. permissions utilisateur (scope par user_id).

Aucune infra externe : CoreRecordStore mémoire + doubles de test pour le
ProviderManager / AgentManager / ingestion RAG.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from core.chat.pipeline import ChatPipeline
from core.projects import ProjectManager
from core.state import CoreRecordStore
from core.state.chats import ChatStore


# ── Doubles de test (aucun appel réseau) ────────────────────────────────


class _FakeLLMResult:
    def __init__(self, content: str) -> None:
        self.content = content
        self.provider = "fake"
        self.model = "fake-model"
        self.usage: dict[str, Any] = {}


class _FakeProvider:
    """Provider minimal — capture le modèle réellement demandé."""

    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id
        self.calls: list[dict[str, Any]] = []

    async def chat(self, messages: list[Any], model: str | None = None, **_: Any) -> _FakeLLMResult:
        self.calls.append({"messages": list(messages), "model": model})
        return _FakeLLMResult("ok")


class _FakeRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, _FakeProvider] = {}

    def get_provider(self, provider_id: str) -> _FakeProvider | None:
        return self._providers.get(provider_id)


class _FakeProviderManager:
    """Double du ProviderManager : registre de providers factices."""

    def __init__(self, provider_ids: list[str] | None = None) -> None:
        self._registry = _FakeRegistry()
        self._providers_config: dict[str, dict[str, Any]] = {}
        self.chat_calls: list[dict[str, Any]] = []
        for provider_id in provider_ids or []:
            self._registry._providers[provider_id] = _FakeProvider(provider_id)

    def provider(self, provider_id: str) -> _FakeProvider:
        return self._registry._providers[provider_id]

    async def chat(self, messages: list[Any], requirements: Any = None, **_: Any) -> _FakeLLMResult:
        preferred = list(getattr(requirements, "preferred_providers", None) or [])
        self.chat_calls.append({"messages": list(messages), "provider": preferred[0] if preferred else None})
        return _FakeLLMResult("auto")


class _FakeAgentManager:
    def __init__(self, agents: list[SimpleNamespace]) -> None:
        self._agents = {agent.id: agent for agent in agents}

    async def get(self, agent_id: str) -> SimpleNamespace | None:
        return self._agents.get(agent_id)


class _FakeIngestion:
    """Double de RAGPipeline.ingest / delete_document."""

    def __init__(self) -> None:
        self.ingested: list[str] = []
        self.deleted: list[str] = []

    async def ingest(
        self,
        *,
        content: str,
        title: str,
        source: str,
        metadata: dict[str, Any],
        document_id: str,
    ) -> SimpleNamespace:
        self.ingested.append(document_id)
        return SimpleNamespace(chunks=[object(), object(), object()])

    async def delete_document(self, doc_id: str) -> None:
        self.deleted.append(doc_id)


# ── Fakes / fixtures ────────────────────────────────────────────────────


def _fake_agent(agent_id: str, name: str, **kw: Any) -> SimpleNamespace:
    return SimpleNamespace(
        id=agent_id,
        name=name,
        description=kw.get("description", ""),
        provider=kw.get("provider"),
        model=kw.get("model"),
        skill_ids=kw.get("skill_ids", []),
        metadata=kw.get("metadata", {}),
    )


@pytest.fixture()
def store() -> CoreRecordStore:
    return CoreRecordStore()


@pytest.fixture()
def projects(store: CoreRecordStore) -> ProjectManager:
    return ProjectManager(store=store)


@pytest.fixture()
def chats(store: CoreRecordStore) -> ChatStore:
    return ChatStore(store=store)



# ── 1-3. Cycle de vie du Project ────────────────────────────────────────


@pytest.mark.asyncio
async def test_project_crud_lifecycle(projects: ProjectManager):
    """Création, lecture, modification puis suppression d'un Project."""
    # 1. Création — le nom est requis et unique.
    with pytest.raises(ValueError, match="name is required"):
        await projects.create_project(user_id="alice", name="   ")

    project = await projects.create_project(
        user_id="alice",
        name="Recon",
        description="Projet OSINT",
    )
    assert project["id"]
    assert project["user_id"] == "alice"

    with pytest.raises(ValueError, match="already exists"):
        await projects.create_project(user_id="alice", name="recon")

    # 2. Modification — instructions, agent, provider, modèle.
    updated = await projects.update_project(
        project["id"],
        "alice",
        {
            "instructions": "Réponds de façon concise.",
            "agent_id": "agent-1",
            "provider_id": "fake-provider",
            "model": "fake-model-x",
        },
    )
    assert updated["instructions"] == "Réponds de façon concise."
    assert updated["agent_id"] == "agent-1"
    assert updated["model"] == "fake-model-x"

    # 3. Suppression — le record disparaît.
    assert await projects.delete_project(project["id"], user_id="alice") is True
    assert await projects.get_project(project["id"], user_id="alice") is None

    # Le projet virtuel « general » est protégé.
    assert await projects.delete_project("general") is False


@pytest.mark.asyncio
async def test_general_project_fallback(projects: ProjectManager):
    """« general » est un snapshot virtuel — jamais persisté, jamais modifié."""
    general = await projects.get_project("general", user_id="alice")
    assert general is not None
    assert general["id"] == "general"
    assert general["user_id"] == "alice"

    patched = await projects.update_project("general", "alice", {"instructions": "x"})
    assert patched["instructions"] == "x"
    # Aucune écriture : un nouveau manager relit le snapshot vierge.


# ── 4. Documents du projet (pipeline RAG Core) ──────────────────────────


@pytest.mark.asyncio
async def test_project_document_upload_and_delete(projects: ProjectManager):
    """Upload délégué au pipeline Core, suppression purge l'index."""
    ingestion = _FakeIngestion()
    projects._ingestion = ingestion
    project = await projects.create_project(user_id="alice", name="Docs")

    doc = await projects.record_document_upload(
        project_id=project["id"],
        file_id="/tmp/brief.md",
        filename="brief.md",
        mime_type="text/markdown",
        size_bytes=42,
        user_id="alice",
        contents=b"# Brief\n\nContenu du projet.",
    )
    assert doc["status"] == "ready"
    assert doc["chunk_count"] == 3
    assert ingestion.ingested == [doc["id"]]

    docs = await projects.list_project_documents(project["id"], user_id="alice")
    assert [d["id"] for d in docs] == [doc["id"]]

    assert await projects.delete_project_document(project["id"], doc["id"], user_id="alice") is True
    assert ingestion.deleted == [doc["id"]]
    assert await projects.list_project_documents(project["id"], user_id="alice") == []


@pytest.mark.asyncio
async def test_project_documents_isolated_between_projects(projects: ProjectManager):
    """Un document appartient à un seul projet (scope strict)."""
    pa = await projects.create_project(user_id="alice", name="A")
    pb = await projects.create_project(user_id="alice", name="B")
    await projects.record_document_upload(
        project_id=pa["id"],
        file_id="/tmp/a.txt",
        filename="a.txt",
        mime_type="text/plain",
        user_id="alice",
    )
    assert len(await projects.list_project_documents(pa["id"], user_id="alice")) == 1
    assert await projects.list_project_documents(pb["id"], user_id="alice") == []


# ── 5-6. Conversations rattachées au projet ─────────────────────────────


@pytest.mark.asyncio
async def test_conversation_created_in_project(chats: ChatStore, projects: ProjectManager):
    """Une conversation créée avec `project_id` reste rattachée au projet."""
    project = await projects.create_project(user_id="alice", name="Chats")

    chat = await chats.create_chat("Première", user_id="alice", project_id=project["id"])
    assert chat["project_id"] == project["id"]

    # Relecture Core : le rattachement est persisté.
    record = await chats.get_chat(chat["id"])
    assert record is not None
    assert record["project_id"] == project["id"]

    # Une conversation orpheline peut être rattachée (binding explicite).
    orphan = await chats.create_chat("Orpheline", user_id="alice")
    bound = await chats.update_chat(orphan["id"], {"project_id": project["id"]})
    assert bound is not None
    assert bound["project_id"] == project["id"]


@pytest.mark.asyncio
async def test_multiple_conversations_are_independent(chats: ChatStore, projects: ProjectManager):
    """Deux conversations d'un même projet ont des historiques séparés."""
    project = await projects.create_project(user_id="alice", name="Multi")
    chat_a = await chats.create_chat("A", user_id="alice", project_id=project["id"])
    chat_b = await chats.create_chat("B", user_id="alice", project_id=project["id"])

    await chats.add_message(chat_a["id"], "user", "message A", user_id="alice")
    await chats.add_message(chat_b["id"], "user", "message B", user_id="alice")

    messages_a = await chats.list_messages(chat_a["id"])
    messages_b = await chats.list_messages(chat_b["id"])
    assert [m["content"] for m in messages_a] == ["message A"]
    assert [m["content"] for m in messages_b] == ["message B"]


# ── 10. Isolation entre Projects ────────────────────────────────────────


@pytest.mark.asyncio
async def test_conversations_isolated_between_projects(chats: ChatStore, projects: ProjectManager):
    """L'historique d'un projet ne fuit jamais vers un autre projet."""
    pa = await projects.create_project(user_id="alice", name="Alpha")
    pb = await projects.create_project(user_id="alice", name="Beta")

    chat_a = await chats.create_chat("Alpha 1", user_id="alice", project_id=pa["id"])
    await chats.add_message(chat_a["id"], "user", "secret alpha", user_id="alice")
    chat_b = await chats.create_chat("Beta 1", user_id="alice", project_id=pb["id"])

    chats_a = await chats.list_chats(user_id="alice", project_id=pa["id"])
    chats_b = await chats.list_chats(user_id="alice", project_id=pb["id"])
    assert [c["id"] for c in chats_a] == [chat_a["id"]]
    assert [c["id"] for c in chats_b] == [chat_b["id"]]


@pytest.mark.asyncio
async def test_unassigned_scope_excludes_project_chats(chats: ChatStore, projects: ProjectManager):
    """Le scope par défaut (hors projet) n'expose pas les conversations de projet."""
    project = await projects.create_project(user_id="alice", name="Scope")
    in_project = await chats.create_chat("Projet", user_id="alice", project_id=project["id"])
    orphan = await chats.create_chat("Défaut", user_id="alice")

    unassigned = await chats.list_chats(user_id="alice", unassigned=True)
    assert [c["id"] for c in unassigned] == [orphan["id"]]

    # Sans filtre (rétro-compatibilité : recherche, historique), tout remonte.
    all_chats = await chats.list_chats(user_id="alice")
    assert {c["id"] for c in all_chats} == {in_project["id"], orphan["id"]}



# ── 7-9. Contexte projet dans le ChatPipeline ───────────────────────────


def _pipe(
    chats: ChatStore,
    projects: ProjectManager,
    *,
    providers: list[str] | None = None,
    agents: list[SimpleNamespace] | None = None,
) -> tuple[ChatPipeline, _FakeProviderManager]:
    """Pipeline Core branché sur le vrai ProjectManager + doubles LLM/agent."""
    pipeline = ChatPipeline(chat_store=chats)
    pipeline.set_project_manager(projects)
    manager = _FakeProviderManager(providers or [])
    pipeline.set_provider_manager(manager)
    if agents:
        pipeline.set_agent_manager(_FakeAgentManager(agents))
    return pipeline, manager


def _system_prompt(manager: _FakeProviderManager) -> str:
    """Premier message système capturé (provider ou fallback manager.chat)."""
    for provider in manager._registry._providers.values():
        if provider.calls:
            return provider.calls[-1]["messages"][0].content
    return manager.chat_calls[-1]["messages"][0].content


@pytest.mark.asyncio
async def test_pipeline_inherits_project_context(chats: ChatStore, projects: ProjectManager):
    """7. Les instructions projet sont injectées sans fusionner l'historique."""
    project = await projects.create_project(user_id="alice", name="Contexte")
    project = await projects.update_project(
        project["id"],
        "alice",
        {
            "instructions": "Toujours répondre en français.",
            "provider_id": "fake-provider",
            "model": "fake-model-x",
            "knowledge_ids": ["k1"],
            "skill_ids": ["s1"],
            "tool_ids": ["t1"],
        },
    )
    pipeline, manager = _pipe(chats, projects, providers=["fake-provider"])

    result = await pipeline.run(message="Bonjour", user_id="alice", project_id=project["id"])

    # Rattachement : conversation + message portent le projet.
    assert result["user_message"]["metadata"]["project_id"] == project["id"]
    chat_record = await chats.get_chat(result["chat_id"])
    assert chat_record is not None
    assert chat_record["project_id"] == project["id"]

    # Les instructions vivent dans le prompt système — jamais dans l'historique.
    system = _system_prompt(manager)
    assert "[Contexte du projet « Contexte »]" in system
    assert "Toujours répondre en français." in system
    messages = await chats.list_messages(result["chat_id"])
    assert [m["content"] for m in messages] == ["Bonjour", "ok"]

    # 8. Le modèle par défaut du projet est réellement utilisé.
    assert manager.provider("fake-provider").calls[-1]["model"] == "fake-model-x"


@pytest.mark.asyncio
async def test_pipeline_request_overrides_project_defaults(chats: ChatStore, projects: ProjectManager):
    """8. L'appel explicite du chat gagne sur les défauts du projet."""
    project = await projects.create_project(user_id="alice", name="Défauts")
    project = await projects.update_project(
        project["id"], "alice", {"provider_id": "fake-provider", "model": "fake-model-x"}
    )
    pipeline, manager = _pipe(chats, projects, providers=["fake-provider", "request-provider"])

    await pipeline.run(
        message="Salut",
        user_id="alice",
        project_id=project["id"],
        provider_id="request-provider",
        model="request-model",
    )

    call = manager.provider("request-provider").calls[-1]
    assert call["model"] == "request-model"
    # Le provider par défaut du projet n'a pas été appelé.
    assert manager.provider("fake-provider").calls == []



@pytest.mark.asyncio
async def test_pipeline_keeps_conversation_project(chats: ChatStore, projects: ProjectManager):
    """10. Une conversation garde son projet — jamais de réassignation."""
    pa = await projects.create_project(user_id="alice", name="Alpha")
    pa = await projects.update_project(pa["id"], "alice", {"instructions": "Règle Alpha."})
    pb = await projects.create_project(user_id="alice", name="Beta")
    pb = await projects.update_project(pb["id"], "alice", {"instructions": "Règle Beta."})

    pipeline, manager = _pipe(chats, projects)
    chat = await chats.create_chat("Alpha chat", user_id="alice", project_id=pa["id"])

    # Sans project_id dans la requête : le projet de la conversation s'applique.
    await pipeline.run(message="m1", user_id="alice", chat_id=chat["id"])
    assert "Règle Alpha." in _system_prompt(manager)

    # Avec un project_id différent : le rattachement existant prime.
    await pipeline.run(message="m2", user_id="alice", chat_id=chat["id"], project_id=pb["id"])
    system = _system_prompt(manager)
    assert "Règle Alpha." in system
    assert "Règle Beta." not in system

    record = await chats.get_chat(chat["id"])
    assert record is not None
    assert record["project_id"] == pa["id"]


@pytest.mark.asyncio
async def test_pipeline_binds_orphan_chat(chats: ChatStore, projects: ProjectManager):
    """5. Une conversation orpheline est rattachée au projet de la requête."""
    project = await projects.create_project(user_id="alice", name="Rattachement")
    project = await projects.update_project(project["id"], "alice", {"instructions": "Règle P."})

    pipeline, manager = _pipe(chats, projects)
    chat = await chats.create_chat("Orpheline", user_id="alice")
    assert chat["project_id"] is None

    result = await pipeline.run(
        message="m", user_id="alice", chat_id=chat["id"], project_id=project["id"]
    )

    record = await chats.get_chat(chat["id"])
    assert record is not None
    assert record["project_id"] == project["id"]
    assert result["user_message"]["metadata"]["project_id"] == project["id"]
    assert "Règle P." in _system_prompt(manager)


@pytest.mark.asyncio
async def test_pipeline_agent_default_from_project(chats: ChatStore, projects: ProjectManager):
    """9. L'agent par défaut du projet est résolu ; la requête peut le remplacer."""
    agents = [
        _fake_agent("agent-1", "Researcher", description="Cherche et cite ses sources."),
        _fake_agent("agent-2", "Writer", description="Rédige des synthèses."),
    ]
    pipeline, manager = _pipe(chats, projects, agents=agents)

    project = await projects.create_project(user_id="alice", name="Agents")
    project = await projects.update_project(project["id"], "alice", {"agent_id": "agent-1"})

    await pipeline.run(message="m", user_id="alice", project_id=project["id"])
    assert "Tu es l'agent « Researcher »." in _system_prompt(manager)

    # La requête explicite gagne sur le défaut du projet.
    await pipeline.run(message="m2", user_id="alice", project_id=project["id"], agent_id="agent-2")
    assert "Tu es l'agent « Writer »." in _system_prompt(manager)



# ── 11. Persistance après redémarrage applicatif ────────────────────────


@pytest.mark.asyncio
async def test_persistence_across_manager_restart(store: CoreRecordStore):
    """Les records survivent à la reconstruction des managers (store durable)."""
    projects_1 = ProjectManager(store=store)
    chats_1 = ChatStore(store=store)
    project = await projects_1.create_project(user_id="alice", name="Durable")
    chat = await chats_1.create_chat("Durable chat", user_id="alice", project_id=project["id"])
    await chats_1.add_message(chat["id"], "user", "persisté", user_id="alice")
    await projects_1.record_document_upload(
        project_id=project["id"],
        file_id="/tmp/durable.txt",
        filename="durable.txt",
        mime_type="text/plain",
        user_id="alice",
    )

    # « Redémarrage » : nouveaux managers sur le même store (PG/Redis en prod).
    projects_2 = ProjectManager(store=store)
    chats_2 = ChatStore(store=store)

    record = await projects_2.get_project(project["id"], user_id="alice")
    assert record is not None
    assert record["name"] == "Durable"
    docs = await projects_2.list_project_documents(project["id"], user_id="alice")
    assert [d["filename"] for d in docs] == ["durable.txt"]

    chat_record = await chats_2.get_chat(chat["id"])
    assert chat_record is not None
    assert chat_record["project_id"] == project["id"]
    messages = await chats_2.list_messages(chat["id"])
    assert [m["content"] for m in messages] == ["persisté"]


# ── 12. Permissions utilisateur ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_user_isolation_and_permissions(projects: ProjectManager, chats: ChatStore):
    """Chaque utilisateur ne voit et ne modifie que ses propres projets."""
    alice_project = await projects.create_project(user_id="alice", name="Alice Project")
    bob_project = await projects.create_project(user_id="bob", name="Bob Project")

    # Lecture : la liste est filtrée par utilisateur.
    assert [p["id"] for p in await projects.list_projects(user_id="alice")] == [alice_project["id"]]
    assert await projects.get_project(bob_project["id"], user_id="alice") is None

    # Écriture croisée refusée.
    with pytest.raises(ValueError, match="not found"):
        await projects.update_project(bob_project["id"], "alice", {"name": "Hack"})
    assert await projects.delete_project(bob_project["id"], user_id="alice") is False

    # Documents : scope vérifié avant lecture.
    with pytest.raises(ValueError, match="access denied"):
        await projects.list_project_documents(bob_project["id"], user_id="alice")

    # Conversations : filtre utilisateur + projet.
    await chats.create_chat("Alice chat", user_id="alice", project_id=alice_project["id"])
    assert await chats.list_chats(user_id="bob", project_id=alice_project["id"]) == []
    assert len(await chats.list_chats(user_id="alice", project_id=alice_project["id"])) == 1

    # Le fallback « general » reste accessible à tout utilisateur authentifié.
    assert (await projects.get_project("general", user_id="bob"))["id"] == "general"


@pytest.mark.asyncio
async def test_resolve_context_fail_safe(projects: ProjectManager):
    """resolve_context est tolérant : inconnu/None → None (jamais d'exception)."""
    project = await projects.create_project(user_id="alice", name="Contexte")

    context = await projects.resolve_context(project["id"])
    assert context is not None
    assert context["id"] == project["id"]
    assert context["instructions"] == ""
    assert context["folder_ids"] == []

    assert await projects.resolve_context(None) is None
    assert await projects.resolve_context("does-not-exist") is None

    assert (await projects.get_project("general"))["instructions"] == ""
