"""Tests Core — l'executor d'agent résout ses domains vers les ressources Core.

Chaîne réelle bout en bout (aucun mock du domaine) : DomainManager + stores
Core réels ; seul le provider LLM est un fake capturant les messages, car
l'objet testé est la résolution domain_ids → (skills, collections), pas le LLM.

Invariant de sécurité : un agent ne peut s'auto-attribuer des ressources —
seules les memberships Core rattachées à ses domain_ids (validés à la
création) sont injectées dans son contexte.
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.agents.executor import create_agent_executor
from core.agents.types import Agent
from core.domains import DomainManager
from core.knowledge import KnowledgeCollectionManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeProvider:
    """Provider LLM factice qui capture les messages reçus."""

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
    """Store de skills minimal respectant le protocole get_skill."""

    def __init__(self, skills: dict[str, dict[str, Any]]) -> None:
        self._skills = skills

    async def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        return self._skills.get(skill_id)

    async def list_skills(self) -> list[dict[str, Any]]:
        return list(self._skills.values())


def _build_executor(provider, *, skills=None):
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    domains = DomainManager(store=store, collections=collections, skills=skills)
    executor = create_agent_executor(
        provider_manager=_FakeProviderManager(provider),
        skill_store=skills,
        knowledge_collections=collections,
        domain_manager=domains,
    )
    return executor, domains, collections, rag
def test_executor_injects_domain_skills_and_collections():
    """Les skills et collections rattachés aux domains de l'agent sont injectés."""

    async def scenario():
        provider = _FakeProvider()
        skill_store = _FakeSkillStore({
            "skill-osint": {
                "id": "skill-osint",
                "name": "OSINT Basics",
                "content": "Toujours sourcer les infos avant analyse.",
                "is_active": True,
            },
        })
        executor, domains, collections, rag = _build_executor(
            provider, skills=skill_store
        )

        # Domain réel + ressources réellement rattachées (membership Core).
        domain = await domains.create_domain("OSINT", user_id="alice")
        col = await collections.create_collection("OSINT Docs", user_id="alice")
        doc = await rag.ingest(
            "Recon passive : ne jamais toucher la cible.",
            title="Recon",
            source="recon.md",
        )
        await collections.add_document(col["id"], doc.id)
        await domains.attach_resource(domain["id"], "collection", col["id"])
        await domains.attach_resource(domain["id"], "skill", "skill-osint")

        agent = Agent(
            id="agent-1",
            name="OSINT Agent",
            provider="fake",
            domain_ids=[domain["id"]],
        )
        await executor(agent, "Analyse la surface d'exposition")

        system = provider.calls[0][0].content
        assert "Toujours sourcer les infos avant analyse." in system
        assert "[Connaissances]" in system
        assert "Recon passive" in system

    asyncio.run(scenario())

def test_executor_merges_agent_and_domain_collections_without_duplicates():
    """Les collections agent + domain fusionnent, dédupliquées, sans conflit."""

    async def scenario():
        provider = _FakeProvider()
        executor, domains, collections, rag = _build_executor(provider)

        domain = await domains.create_domain("Recon", user_id="alice")
        shared_col = await collections.create_collection("Shared", user_id="alice")
        own_col = await collections.create_collection("Own", user_id="alice")
        shared_doc = await rag.ingest(
            "Méthodologie de recon passive partagée.",
            title="Shared Recon",
            source="shared.md",
        )
        await collections.add_document(shared_col["id"], shared_doc.id)
        await domains.attach_resource(domain["id"], "collection", shared_col["id"])

        agent = Agent(
            id="agent-2",
            name="Mixed Agent",
            provider="fake",
            knowledge_collection_ids=[shared_col["id"], own_col["id"]],
            domain_ids=[domain["id"]],
        )
        await executor(agent, "Explique la méthodologie de recon partagée")

        # Aucun doublon : la collection partagée n'est injectée qu'une fois.
        system = provider.calls[0][0].content
        assert system.count("[Connaissances]") == 1

    asyncio.run(scenario())


def test_executor_skill_id_override_beats_domain_skills():
    """Un skill_id explicite prime : seul ce skill est injecté."""

    async def scenario():
        provider = _FakeProvider()
        skill_store = _FakeSkillStore({
            "skill-a": {
                "id": "skill-a",
                "name": "A",
                "content": "Contenu A",
                "is_active": True,
            },
            "skill-b": {
                "id": "skill-b",
                "name": "B",
                "content": "Contenu B",
                "is_active": True,
            },
        })
        executor, domains, _c, _s = _build_executor(provider, skills=skill_store)

        domain = await domains.create_domain("Forensic", user_id="alice")
        await domains.attach_resource(domain["id"], "skill", "skill-b")

        agent = Agent(
            id="agent-3",
            name="Forensic Agent",
            provider="fake",
            skill_ids=["skill-a"],
            domain_ids=[domain["id"]],
        )
        await executor(agent, "Tâche", skill_id="skill-a")

        system = provider.calls[0][0].content
        assert "Contenu A" in system
        assert "Contenu B" not in system

    asyncio.run(scenario())


def test_executor_ignores_ghost_domain_gracefully():
    """Un domain supprimé après création de l'agent dégrade sans bloquer."""

    async def scenario():
        provider = _FakeProvider()
        executor, domains, _c, _s = _build_executor(provider)

        domain = await domains.create_domain("Ephemeral", user_id="alice")
        agent = Agent(
            id="a4", name="Ghost Agent", provider="fake", domain_ids=[domain["id"]]
        )
        await domains.delete_domain(domain["id"])

        result = await executor(agent, "Tâche")

        assert result == "ok"

    asyncio.run(scenario())


def test_executor_without_domain_manager_warns_and_proceeds():
    """Sans DomainManager branché, les domains déclarés sont ignorés (warning)."""

    async def scenario():
        provider = _FakeProvider()
        store = CoreRecordStore()
        rag = RAGPipeline(store=store)
        collections = KnowledgeCollectionManager(store=store, rag=rag)
        executor = create_agent_executor(
            provider_manager=_FakeProviderManager(provider),
            knowledge_collections=collections,
            domain_manager=None,  # non branché
        )

        agent = Agent(id="a5", name="No Domains", provider="fake", domain_ids=["d1"])
        result = await executor(agent, "Tâche")

        assert result == "ok"
        assert "[Connaissances]" not in provider.calls[0][0].content

    asyncio.run(scenario())
