"""Tests Core — ressources effectivement autorisées aux Agents.

Chaîne réelle bout en bout (managers Core réels) : FolderManager,
KnowledgeManager, KnowledgeCollectionManager, RAGPipeline ; seuls le provider
LLM (fake capturant les messages) et le ToolManager (fake minimal) sont
simulés — l'objet testé est la résolution sélection → ressources injectées.

Invariants vérifiés avec plusieurs agents :
- aucun agent ne reçoit automatiquement les ressources globales ;
- sélectionner un dossier inclut les ressources qu'il contient ;
- une même ressource venue de plusieurs sources n'est injectée qu'une fois ;
- retirer une ressource d'un dossier la retire de l'agent ;
- le runtime ne reçoit que les tools/MCP explicitement autorisés.
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.agents.executor import create_agent_executor
from core.agents.resources import resolve_agent_resources
from core.agents.types import Agent
from core.folders import FolderManager, FolderResourceProvider
from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeProvider:
    default_model = "fake-model"

    def __init__(self) -> None:
        self.calls: list[list[Any]] = []

    async def chat(self, messages, model=None, temperature=None):
        self.calls.append(list(messages))
        return _FakeResponse("ok")


class _FakeRegistry:
    def __init__(self, provider: _FakeProvider) -> None:
        self._provider = provider

    def get_provider(self, provider_id: str):
        return self._provider if provider_id == "fake" else None


class _FakeProviderManager:
    def __init__(self, provider: _FakeProvider) -> None:
        self._registry = _FakeRegistry(provider)
        self._providers_config: dict[str, Any] = {}


class _FakeSkillStore:
    def __init__(self, skills: dict[str, dict[str, Any]]) -> None:
        self._skills = skills

    async def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        return self._skills.get(skill_id)

    async def list_skills(self) -> list[dict[str, Any]]:
        return list(self._skills.values())


class _FakeToolManager:
    """ToolManager minimal : getters sync (protocole ToolManager réel)."""

    def __init__(self, tools: dict[str, dict[str, Any]]) -> None:
        self._tools = tools

    def get_tool(self, tool_id: str) -> dict[str, Any] | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools.values())


SKILLS = {
    "skill-folder": {
        "id": "skill-folder", "name": "Folder Skill",
        "content": "Méthodologie du dossier.", "is_active": True,
    },
    "skill-explicit": {
        "id": "skill-explicit", "name": "Explicit Skill",
        "content": "Skill choisi individuellement.", "is_active": True,
    },
    "skill-orphan": {
        "id": "skill-orphan", "name": "Global Skill",
        "content": "Jamais autorisé automatiquement.", "is_active": True,
    },
}

TOOLS = {
    "tool-web": {
        "id": "tool-web", "name": "web_search",
        "description": "Recherche web", "provider": "builtin",
    },
    "tool-mcp": {
        "id": "tool-mcp", "name": "mcp_grep",
        "description": "Grep MCP", "provider": "mcp-fs",
    },
}


def _setup():
    """Managers Core réels partageant le même store."""
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    knowledge = KnowledgeManager(store=store)
    skill_store = _FakeSkillStore(SKILLS)
    tools = _FakeToolManager(TOOLS)
    folders = FolderManager(
        store=store, knowledge=knowledge, collections=collections, skills=skill_store
    )
    return store, rag, collections, knowledge, skill_store, tools, folders


# ── (SUITE) ──────────────────────────────────────────────────────────────────

def _build_executor(provider, skill_store, collections, knowledge, folders, tools):
    return create_agent_executor(
        provider_manager=_FakeProviderManager(provider),
        skill_store=skill_store,
        knowledge_collections=collections,
        folders=folders,
        knowledge_manager=knowledge,
        tools=tools,
    )


def _system_of(provider) -> str:
    return provider.calls[0][0].content


def test_agent_without_selection_receives_nothing():
    """Aucune ressource globale n'est injectée sans décision explicite."""

    async def scenario():
        provider = _FakeProvider()
        _s, rag, collections, knowledge, skill_store, tools, folders = _setup()
        executor = _build_executor(
            provider, skill_store, collections, knowledge, folders, tools
        )
        # Catalogue global garni : rien ne doit fuiter vers l'agent.
        await knowledge.create("Protocole", content="Contenu global interdit.")
        await collections.create_collection("Global Col", user_id="alice")

        agent = Agent(id="a0", name="Blank Agent", provider="fake")
        await executor(agent, "Tâche")

        system = _system_of(provider)
        assert "[Connaissances]" not in system
        assert "[Knowledge:" not in system
        assert "[Skill:" not in system
        assert "Outils autorisés" not in system
        assert "Contenu global interdit." not in system

    asyncio.run(scenario())


def test_folder_selection_includes_contained_resources():
    """Sélectionner un dossier inclut knowledge + collection + skill contenus."""

    async def scenario():
        provider = _FakeProvider()
        _s, rag, collections, knowledge, skill_store, tools, folders = _setup()
        executor = _build_executor(
            provider, skill_store, collections, knowledge, folders, tools
        )

        folder = await folders.create_folder("OSINT Kit", user_id="alice")
        node = await knowledge.create("Protocole OSINT", content="Ne jamais toucher la cible.")
        doc = await rag.ingest("Recon passive : DNS et certificats.", title="Recon")
        col = await collections.create_collection("Recon Docs", user_id="alice")
        await collections.add_document(col["id"], doc.id)
        await folders.attach_resource(folder["id"], "knowledge", node.id)
        await folders.attach_resource(folder["id"], "collection", col["id"])
        await folders.attach_resource(folder["id"], "skill", "skill-folder")

        agent = Agent(id="a1", name="OSINT Agent", provider="fake", folder_ids=[folder["id"]])
        result = await resolve_agent_resources(
            agent, folders=folders, knowledge=knowledge,
            collections=collections, skills=skill_store, tools=tools,
        )
        assert [k["id"] for k in result["knowledge"]] == [node.id]
        assert [c["id"] for c in result["collections"]] == [col["id"]]
        assert [s["id"] for s in result["skills"]] == ["skill-folder"]
        assert all(s["source"] == f"folder:{folder['id']}" for s in result["skills"])

        await executor(agent, "Lance la recon")
        system = _system_of(provider)
        assert "[Knowledge: Protocole OSINT]" in system
        assert "Ne jamais toucher la cible." in system
        assert "Méthodologie du dossier." in system
        assert "[Connaissances]" in system
        # Ressources hors sélection : jamais injectées.
        assert "Skill choisi individuellement." not in system

    asyncio.run(scenario())


# ── (SUITE 2) ────────────────────────────────────────────────────────────────

def test_multiple_agents_receive_only_their_own_resources():
    """Deux agents aux ensembles différents : chacun reçoit exactement les
    siennes — knowledge spécifique, collections, skills et tools/MCP."""

    async def scenario():
        provider_a = _FakeProvider()
        provider_b = _FakeProvider()
        _s, rag, collections, knowledge, skill_store, tools, folders = _setup()
        executor_a = _build_executor(
            provider_a, skill_store, collections, knowledge, folders, tools
        )
        executor_b = _build_executor(
            provider_b, skill_store, collections, knowledge, folders, tools
        )

        node_b = await knowledge.create("Dossier médical", content="Informations médicales.")
        doc_b = await rag.ingest("Comptes rendus de laboratoire.", title="Labo")
        col_b = await collections.create_collection("Médical", user_id="alice")
        await collections.add_document(col_b["id"], doc_b.id)

        # Agent A : knowledge spécifique + tools builtin et MCP.
        node_a = await knowledge.create("Notes research", content="Notes de recherche.")
        agent_a = Agent(
            id="a1", name="Research Agent", provider="fake",
            knowledge_ids=[node_a.id],
            tool_ids=["tool-web", "tool-mcp"],
        )
        await executor_a(agent_a, "Analyse")

        # Agent B : collection + skill explicites, aucun tool.
        agent_b = Agent(
            id="b1", name="Medical Agent", provider="fake",
            knowledge_collection_ids=[col_b["id"]],
            skill_ids=["skill-explicit"],
        )
        # La requête contient un terme du document de la collection :
        # le RAG (voie lexicale en test) retrouve bien le chunk autorisé.
        await executor_b(agent_b, "Résume les comptes rendus de laboratoire")

        system_a = _system_of(provider_a)
        assert "[Knowledge: Notes research]" in system_a
        assert "Notes de recherche." in system_a
        assert "web_search (builtin)" in system_a
        assert "mcp_grep (mcp-fs)" in system_a
        assert "[Skill:" not in system_a  # aucun skill autorisé pour A
        assert "[Connaissances]" not in system_a  # aucune collection pour A
        assert "Informations médicales." not in system_a

        system_b = _system_of(provider_b)
        assert "Skill choisi individuellement." in system_b
        assert "[Connaissances]" in system_b
        assert "[Knowledge:" not in system_b
        assert "Outils autorisés" not in system_b  # aucun tool pour B
        assert "web_search" not in system_b

    asyncio.run(scenario())

# ── (SUITE 3) ────────────────────────────────────────────────────────────────

def test_dedup_and_individual_removal():
    """Une ressource présente à la fois dans un dossier ET sélectionnée
    explicitement n'est injectée qu'une fois ; retirer la ressource du
    dossier la retire effectivement des agents qui ne passent que par lui."""

    async def scenario():
        provider = _FakeProvider()
        _s, rag, collections, knowledge, skill_store, tools, folders = _setup()
        executor = _build_executor(
            provider, skill_store, collections, knowledge, folders, tools
        )

        folder = await folders.create_folder("Commun", user_id="alice")
        await folders.attach_resource(folder["id"], "skill", "skill-explicit")

        agent = Agent(
            id="d1", name="Dedup Agent", provider="fake",
            skill_ids=["skill-explicit"],  # même skill, en explicite
            folder_ids=[folder["id"]],
        )
        resolved = await resolve_agent_resources(
            agent, folders=folders, knowledge=knowledge,
            collections=collections, skills=skill_store, tools=tools,
        )
        assert len(resolved["skills"]) == 1  # déduplication par identité

        await executor(agent, "Tâche")
        assert _system_of(provider).count("Skill choisi individuellement.") == 1

        # Retrait individuel : la ressource quitte le dossier...
        await folders.detach_resource(folder["id"], "skill", "skill-explicit")
        # ...mais reste accessible si sélectionnée explicitement.
        provider2 = _FakeProvider()
        executor2 = _build_executor(
            provider2, skill_store, collections, knowledge, folders, tools
        )
        await executor2(agent, "Tâche")
        assert "Skill choisi individuellement." in _system_of(provider2)

        # Agent ne la référençant QUE via le dossier : n'y a plus accès.
        agent_folder_only = Agent(
            id="d2", name="Folder Only", provider="fake", folder_ids=[folder["id"]]
        )
        provider3 = _FakeProvider()
        executor3 = _build_executor(
            provider3, skill_store, collections, knowledge, folders, tools
        )
        await executor3(agent_folder_only, "Tâche")
        assert "Skill choisi individuellement." not in _system_of(provider3)

    asyncio.run(scenario())


def test_ghost_resources_are_ignored_and_reported():
    """Un dossier supprimé ou un skill disparu n'bloque pas l'exécution et
    apparaît dans ``ghosts`` (observabilité) — jamais de crash."""

    async def scenario():
        provider = _FakeProvider()
        _s, rag, collections, knowledge, skill_store, tools, folders = _setup()
        executor = _build_executor(
            provider, skill_store, collections, knowledge, folders, tools
        )
        folder = await folders.create_folder("Éphémère", user_id="alice")
        await folders.delete_folder(folder["id"])

        agent = Agent(
            id="g1", name="Ghost Agent", provider="fake",
            folder_ids=[folder["id"]], skill_ids=["skill-supprimé"],
        )
        resolved = await resolve_agent_resources(
            agent, folders=folders, knowledge=knowledge,
            collections=collections, skills=skill_store, tools=tools,
        )
        types = {(g["resource_type"], g["resource_id"]) for g in resolved["ghosts"]}
        assert ("folder", folder["id"]) in types
        assert ("skill", "skill-supprimé") in types
        assert resolved["skills"] == []

        result = await executor(agent, "Tâche")
        assert result == "ok"

    asyncio.run(scenario())


def test_tool_resolution_and_folder_tool_membership():
    """Les tools autorisés viennent de la sélection explicite ; le résolveur
    supporte aussi un classement des tools dans un dossier (provider async)."""

    async def scenario():
        _p, rag, collections, knowledge, skill_store, tools, folders = _setup()
        # Registre ouvert : les tools deviennent classables dans les dossiers
        # (FolderResourceProvider attend des getters async).
        async def _get_tool(tool_id: str):
            return tools.get_tool(tool_id)

        async def _list_tools():
            return tools.list_tools()

        folders.add_provider("tool", FolderResourceProvider(_get_tool, _list_tools))

        folder = await folders.create_folder("Toolbox", user_id="alice")
        await folders.attach_resource(folder["id"], "tool", "tool-mcp")

        agent = Agent(
            id="t1", name="Tooled Agent", provider="fake",
            tool_ids=["tool-web"], folder_ids=[folder["id"]],
        )
        resolved = await resolve_agent_resources(
            agent, folders=folders, knowledge=knowledge,
            collections=collections, skills=skill_store, tools=tools,
        )
        tool_ids = {t["id"] for t in resolved["tools"]}
        assert tool_ids == {"tool-web", "tool-mcp"}
        sources = {t["id"]: t["source"] for t in resolved["tools"]}
        assert sources["tool-web"] == "explicit"
        assert sources["tool-mcp"] == f"folder:{folder['id']}"

    asyncio.run(scenario())
