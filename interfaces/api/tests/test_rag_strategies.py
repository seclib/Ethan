"""Tests API — exposition réelle des stratégies RAG (interfaces/api/routers/v1.py).

Exécute le vrai KnowledgeCollectionManager et le vrai RAGPipeline via le
router v1 (CoreRecordStore mémoire). La WebUI ne doit découvrir les
stratégies QUE via GET /v1/rag/strategies — aucune stratégie non implémentée
dans le Core n'est exposée ni acceptée.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from routers import v1
from core.knowledge import KnowledgeCollectionManager
from core.rag import RAGPipeline
from core.rag.embeddings import RAGEmbeddings
from core.state import CoreRecordStore


class _FakeEmbedClient:
    """Embeddings déterministes (voie sémantique testable sans provider)."""

    _VECTORS = {
        "postgresql": [0.98, 0.02, 0.05],
        "administration base de donnees": [1.0, 0.0, 0.0],
    }

    async def embed(self, texts, model=None):  # noqa: ANN001, ANN201
        return [list(self._VECTORS.get(t.strip().lower(), [0.33, 0.33, 0.34])) for t in texts]


@pytest.fixture(autouse=True)
def real_services():
    """Vrais managers Core + CoreDomainServices injectés (même store)."""
    store = CoreRecordStore()
    rag = RAGPipeline(store=store, embeddings=RAGEmbeddings(llm_client=_FakeEmbedClient()))
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    v1.set_knowledge_collections(collections)
    v1.set_core_domain_services(v1.CoreDomainServices(rag=rag))
    yield collections
    v1.set_knowledge_collections(None)


def test_list_strategies_route_exposes_real_catalog():
    """GET /rag/strategies : catalogue réel + défaut + recommandation Core."""
    result = asyncio.run(v1.list_rag_strategies())
    assert result["default"] == "auto"
    ids = {s["id"] for s in result["strategies"]}
    assert ids == {"auto", "keyword", "semantic", "hybrid"}
    for s in result["strategies"]:
        assert s["label"] and s["description"]

    # Recommandation calculée par le Core : le fixture injecte un client
    # d'embedding → hybrid, cohérent avec les capacités réellement disponibles.
    rec = result["recommendation"]
    assert rec["strategy_id"] == "hybrid"
    assert rec["has_real_embeddings"] is True
    assert rec["reason"]
    assert rec["strategy_id"] in ids


def test_create_collection_with_retrieval_strategy_route():
    """POST /knowledge/collections : stratégie par collection persistée."""
    col = asyncio.run(v1.create_collection({
        "name": "Docs", "user_id": "alice", "retrieval_strategy": "hybrid",
    }))
    assert col["retrieval_strategy"] == "hybrid"

    # Stratégie inconnue → 422 (jamais silencieusement acceptée)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_collection({
            "name": "Ghost", "retrieval_strategy": "rerank",
        }))
    assert exc.value.status_code == 422

    # Mise à jour : stratégie valide appliquée, inconnue refusée
    updated = asyncio.run(v1.update_collection(col["id"], {"retrieval_strategy": "semantic"}))
    assert updated["retrieval_strategy"] == "semantic"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.update_collection(col["id"], {"retrieval_strategy": "advanced"}))
    assert exc.value.status_code == 422


def test_update_rag_config_strategy_route():
    """PUT /rag/config : la stratégie globale est appliquée et persistée."""
    result = asyncio.run(v1.update_rag_config({"strategy": "hybrid"}))
    assert result["config"]["strategy"] == "hybrid"
    assert result["stats"]["strategy"] == "hybrid"

    # Le GET reflète la configuration persistée
    fetched = asyncio.run(v1.get_rag_config())
    assert fetched["config"]["strategy"] == "hybrid"

    # Stratégie inconnue → 422 (validation stricte côté API)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.update_rag_config({"strategy": "rerank"}))
    assert exc.value.status_code == 422

    # La configuration valide n'a pas été corrompue par l'échec
    fetched = asyncio.run(v1.get_rag_config())
    assert fetched["config"]["strategy"] == "hybrid"


def test_collection_retrieve_uses_effective_strategy():
    """POST /knowledge/collections/{id}/retrieve applique la stratégie de la
    collection (semantic) plutôt que la globale (keyword)."""
    collections = v1.get_knowledge_collections()
    doc = asyncio.run(collections._rag.ingest("postgresql", title="BDD"))
    col = asyncio.run(collections.create_collection(
        "Docs", user_id="alice", retrieval_strategy="semantic"
    ))
    asyncio.run(collections.add_document(col["id"], doc.id))
    asyncio.run(v1.update_rag_config({"strategy": "keyword"}))

    # Requête sans recouvrement lexical : seule la voie sémantique trouve.
    results = asyncio.run(v1.retrieve_collection(
        {"query": "administration base de donnees"}, col["id"]
    ))
    assert results and results[0]["chunk"]["document_id"] == doc.id
