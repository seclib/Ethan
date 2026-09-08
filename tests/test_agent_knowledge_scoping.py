"""Tests Core — l'executor d'agent scope le RAG sur les collections assignées.

Chaîne réelle bout en bout (aucun mock du domaine) : KnowledgeCollectionManager
+ RAGPipeline réels ; seul le provider LLM est un fake capturant les messages,
car l'objet testé est la construction du prompt, pas le LLM.
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.agents.executor import create_agent_executor
from core.agents.types import Agent
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


def _agent(knowledge_collection_ids: list[str]) -> Agent:
    return Agent(
        id="agent-1",
        name="RAG Agent",
        provider="fake",
        knowledge_collection_ids=knowledge_collection_ids,
    )


def test_executor_injects_rag_context_from_assigned_collections():
    """Le system prompt contient le contexte RAG scopé aux collections."""

    async def scenario():
        store = CoreRecordStore()
        rag = RAGPipeline(store=store)
        collections = KnowledgeCollectionManager(store=store, rag=rag)

        col = await collections.create_collection("Docs", user_id="alice")
        doc = await rag.ingest(
            "ETHAN Core owns the knowledge collections and RAG retrieval.",
            title="Architecture",
            source="architecture.md",
        )
        await collections.add_document(col["id"], doc.id)

        provider = _FakeProvider()
        executor = create_agent_executor(
            provider_manager=_FakeProviderManager(provider),
            knowledge_collections=collections,
        )

        await executor(
            _agent([col["id"]]),
            "Explique la architecture knowledge",
        )

        assert provider.calls, "Le provider doit avoir été appelé"
        system = provider.calls[0][0].content
        assert "[Connaissances]" in system
        assert "Architecture" in system
        assert "ETHAN Core owns the knowledge collections" in system

    asyncio.run(scenario())


def test_executor_without_collections_has_no_knowledge_section():
    """Sans collections assignées, aucune section [Connaissances]."""

    async def scenario():
        provider = _FakeProvider()
        executor = create_agent_executor(
            provider_manager=_FakeProviderManager(provider),
            knowledge_collections=None,
        )

        await executor(_agent([]), "Tâche simple")

        system = provider.calls[0][0].content
        assert "[Connaissances]" not in system

    asyncio.run(scenario())


def test_executor_ignores_unavailable_collections_gracefully():
    """Une collection manquante dégrade (warning) sans bloquer l'exécution."""

    async def scenario():
        provider = _FakeProvider()
        executor = create_agent_executor(
            provider_manager=_FakeProviderManager(provider),
            knowledge_collections=None,  # aucun manager réel
        )

        result = await executor(_agent(["ghost-collection"]), "Tâche")

        assert result == "ok"
        assert "[Connaissances]" not in provider.calls[0][0].content

    asyncio.run(scenario())


def test_agent_type_roundtrip_metadata_fallback():
    """Compat : metadata.knowledge_ids (convention WebUI) → champ typé."""

    legacy = Agent.from_dict({
        "id": "a",
        "name": "Legacy",
        "metadata": {"knowledge_ids": ["col-1", "col-2"]},
    })
    assert legacy.knowledge_collection_ids == ["col-1", "col-2"]

    typed = Agent.from_dict({
        "id": "a",
        "name": "Typed",
        "knowledge_collection_ids": ["col-3"],
        "metadata": {"knowledge_ids": ["stale"]},
    })
    assert typed.knowledge_collection_ids == ["col-3"]  # le champ typé prime

    # Round-trip complet via to_dict
    assert Agent.from_dict(typed.to_dict()).knowledge_collection_ids == ["col-3"]
