"""Tests Core — stratégies RAG (abstraction fondée sur les capacités réelles).

Chaque stratégie exposée est testée sur un chemin de code réel de
``core/rag/retrieval.py``. Le reranking, qui n'existe pas dans ETHAN (aucun
cross-encoder, aucune méthode rank sur les providers), ne doit JAMAIS être
exposé ni accepté.
"""

from __future__ import annotations

import asyncio

import pytest

from core.knowledge import KnowledgeCollectionManager
from core.rag.embeddings import RAGEmbeddings
from core.rag.pipeline import RAGPipeline
from core.rag.strategies import (
    DEFAULT_STRATEGY,
    available_strategies,
    get_strategy,
    normalize_strategy,
    recommend_strategy,
    validate_strategy,
)
from core.state import CoreRecordStore


class _SynonymEmbedClient:
    """Client LLM factice : embeddings déterministes via table de synonymes.

    Permet de tester la voie sémantique sans provider réel : « chat » et
    « animal domestique » partagent un espace vectoriel SANS recouvrement
    lexical — exactement ce que la recherche par mots-clés ne trouve pas.
    """

    _VECTORS = {
        "chat": [0.05, 0.98, 0.05],
        "animal domestique": [0.0, 1.0, 0.0],
        "postgresql": [0.98, 0.02, 0.05],
        "administration base de donnees": [1.0, 0.0, 0.0],
    }
    _DEFAULT = [0.33, 0.33, 0.34]

    async def embed(self, texts, model=None):  # noqa: ANN001, ANN201
        return [list(self._VECTORS.get(t.strip().lower(), self._DEFAULT)) for t in texts]


def _pipeline(strategy: str = DEFAULT_STRATEGY) -> RAGPipeline:
    return RAGPipeline(
        store=CoreRecordStore(),
        embeddings=RAGEmbeddings(llm_client=_SynonymEmbedClient()),
        strategy=strategy,
    )


def _mock_pipeline() -> RAGPipeline:
    """Pipeline SANS client LLM : embeddings mock (tous zéros)."""
    return RAGPipeline(store=CoreRecordStore())


# ── Catalogue de stratégies ──────────────────────────────────────────────────

def test_catalog_exposes_only_real_strategies():
    """Le catalogue ne contient que les stratégies réellement implémentées."""
    strategies = available_strategies()
    ids = {s["id"] for s in strategies}
    assert ids == {"auto", "keyword", "semantic", "hybrid"}
    # Le reranking n'existe pas dans ETHAN : jamais exposé.
    assert "rerank" not in ids and "advanced" not in ids
    for s in strategies:
        assert s["label"] and s["description"]
        assert isinstance(s["requires_embeddings"], bool)
    assert get_strategy("hybrid").id == "hybrid"
    with pytest.raises(ValueError):
        get_strategy("rerank")


def test_validate_strict_and_normalize_fail_safe():
    """Validation stricte pour l'API, normalisation fail-safe pour le moteur."""
    assert validate_strategy(" HYBRID ") == "hybrid"
    with pytest.raises(ValueError):
        validate_strategy("rerank")
    with pytest.raises(ValueError):
        validate_strategy("")
    assert normalize_strategy(None) == DEFAULT_STRATEGY
    assert normalize_strategy("n'importe quoi") == DEFAULT_STRATEGY
    assert normalize_strategy("Semantic") == "semantic"


# ── Stratégie keyword ────────────────────────────────────────────────────────

def test_keyword_strategy_works_without_real_embeddings():
    """``keyword`` : recherche textuelle pure, indépendante des embeddings."""

    async def scenario():
        p = _mock_pipeline()
        await p.ingest("Recette de tarte aux pommes maison.", title="Cuisine")
        await p.ingest("Manuel d'administration PostgreSQL.", title="BDD")

        hits = await p.retrieve("pommes", strategy="keyword")
        assert hits and all("pommes" in h.chunk.content.lower() for h in hits)

        # Aucun recouvrement lexical → aucun résultat (pas de magie sémantique)
        assert await p.retrieve("ordinateur", strategy="keyword") == []

    asyncio.run(scenario())


# ── Stratégie semantic ───────────────────────────────────────────────────────

def test_semantic_strategy_finds_synonyms_without_lexical_overlap():
    """``semantic`` : retrouve « chat » pour la requête « animal domestique »."""

    async def scenario():
        p = _pipeline()
        chat_doc = await p.ingest("chat", title="Animaux")
        await p.ingest("postgresql", title="BDD")

        # La requête n'a AUCUN mot commun avec le document « chat ».
        hits = await p.retrieve("animal domestique", strategy="semantic")
        assert hits, "la voie sémantique doit retrouver le synonyme"
        assert hits[0].chunk.document_id == chat_doc.id

        # L'équivalent lexical ne trouve rien sur la même requête.
        assert await p.retrieve("animal domestique", strategy="keyword") == []

    asyncio.run(scenario())


def test_semantic_strategy_falls_back_to_textual_on_mock_embeddings():
    """``semantic`` sans embeddings réels : repli documenté sur le textuel."""

    async def scenario():
        p = _mock_pipeline()
        doc = await p.ingest("Recette de tarte aux pommes maison.", title="Cuisine")
        hits = await p.retrieve("pommes", strategy="semantic")
        assert hits and all(h.chunk.document_id == doc.id for h in hits)

    asyncio.run(scenario())


# ── Stratégie hybrid ─────────────────────────────────────────────────────────

def test_hybrid_strategy_fuses_lexical_and_semantic():
    """``hybrid`` : la fusion RRF combine les classements des deux voies.

    Requête « animal domestique » sur deux documents :
    - « chat » : trouvé uniquement par la voie sémantique ;
    - « animal domestique expliqué » : trouvé uniquement par la voie lexicale.
    En hybrid top-1, le document boosté par les DEUX classements gagne
    (« animal domestique expliqué »), là où la sémantique seule renvoie « chat ».
    """

    async def scenario():
        p = _pipeline()
        await p.ingest("chat", title="Animaux")
        lexical_doc = await p.ingest("animal domestique expliqué", title="Élevage")

        semantic_top1 = await p.retrieve("animal domestique", strategy="semantic", top_k=1)
        assert semantic_top1[0].chunk.document_id != lexical_doc.id

        hybrid_top1 = await p.retrieve("animal domestique", strategy="hybrid", top_k=1)
        assert hybrid_top1[0].chunk.document_id == lexical_doc.id

        # Hybrid sans embeddings réels → composante keyword seule (dégradation).
        mock_p = _mock_pipeline()
        await mock_p.ingest("Recette de tarte aux pommes.", title="Cuisine")
        hits = await mock_p.retrieve("pommes", strategy="hybrid")
        assert hits and "pommes" in hits[0].chunk.content.lower()

    asyncio.run(scenario())


# ── Stratégie auto + config globale ──────────────────────────────────────────

def test_auto_strategy_is_default_and_degrades_gracefully():
    """``auto`` (défaut) : sémantique si embeddings réels, sinon textuel."""

    async def scenario():
        mock_p = _mock_pipeline()
        assert mock_p.get_config()["strategy"] == DEFAULT_STRATEGY
        await mock_p.ingest("Recette de tarte aux pommes.", title="Cuisine")
        # Auto + embeddings mock → chemin textuel, la recherche fonctionne.
        hits = await mock_p.retrieve("pommes")  # strategy=None → auto
        assert hits and "pommes" in hits[0].chunk.content.lower()

        real_p = _pipeline()
        chat_doc = await real_p.ingest("chat", title="Animaux")
        hits = await real_p.retrieve("animal domestique")  # auto → sémantique
        assert hits and hits[0].chunk.document_id == chat_doc.id

    asyncio.run(scenario())


def test_global_strategy_config_roundtrip_and_fail_safe():
    """La stratégie globale persiste (rag-config) ; une valeur inconnue est
    normalisée (fail-safe) au niveau moteur — la validation stricte est
    responsabilité de l'API."""

    async def scenario():
        store = CoreRecordStore()
        p = RAGPipeline(store=store)
        config = await p.configure(strategy="hybrid")
        assert config["strategy"] == "hybrid"
        assert p.stats()["strategy"] == "hybrid"
        await p.persist_config()

        # Une nouvelle instance retrouve la stratégie persistée.
        p2 = RAGPipeline(store=store)
        applied = await p2.load_persisted_config()
        assert applied is not None and applied["strategy"] == "hybrid"

        # Valeur inconnue → défaut fail-safe (jamais de crash).
        config = await p.configure(strategy="rerank-n-existe-pas")
        assert config["strategy"] == DEFAULT_STRATEGY

    asyncio.run(scenario())


# ── Stratégie par collection ─────────────────────────────────────────────────

def test_collection_strategy_overrides_global_and_resolves_effective():
    """Résolution effective : collection > globale > auto ; le retrieve d'une
    collection applique réellement sa stratégie."""

    async def scenario():
        store = CoreRecordStore()
        rag = _pipeline()  # stratégie globale : auto (embeddings réels simulés)
        collections = KnowledgeCollectionManager(store=store, rag=rag)

        chat_doc = await rag.ingest("chat", title="Animaux")
        pg_doc = await rag.ingest("postgresql", title="BDD")

        # Sans stratégie → hérite de la globale (auto).
        col = await collections.create_collection("Docs", user_id="alice")
        await collections.add_document(col["id"], chat_doc.id)
        await collections.add_document(col["id"], pg_doc.id)
        assert await collections.get_effective_strategy(col["id"]) == DEFAULT_STRATEGY

        # Stratégie globale → keyword ; la collection surcharge en semantic.
        await rag.configure(strategy="keyword")
        col_sem = await collections.create_collection(
            "Recherche sémantique", user_id="alice", retrieval_strategy="semantic"
        )
        await collections.add_document(col_sem["id"], chat_doc.id)
        await collections.add_document(col_sem["id"], pg_doc.id)

        # Effective : la collection gagne sur la globale.
        assert await collections.get_effective_strategy(col_sem["id"]) == "semantic"
        assert await collections.get_effective_strategy(col["id"]) == "keyword"

        # Retrieve réel : la requête « administration base de donnees » n'a
        # aucun recouvrement lexical avec « postgresql » — la collection
        # semantic le retrouve, la collection keyword (globale) non.
        results_sem = await collections.retrieve(
            "administration base de donnees", col_sem["id"]
        )
        assert results_sem
        assert results_sem[0]["chunk"]["document_id"] == pg_doc.id

        results_kw = await collections.retrieve(
            "administration base de donnees", col["id"]
        )
        assert results_kw == []

        # Retour à la globale : réinitialisation de la stratégie collection.
        await collections.update_collection(col_sem["id"], {"retrieval_strategy": None})
        assert await collections.get_effective_strategy(col_sem["id"]) == "keyword"

    asyncio.run(scenario())


def test_collection_rejects_unknown_strategy():
    """Une stratégie inconnue est refusée à la création ET à la mise à jour."""

    async def scenario():
        collections = KnowledgeCollectionManager(
            store=CoreRecordStore(), rag=_pipeline()
        )
        with pytest.raises(ValueError, match="inconnue"):
            await collections.create_collection("Docs", retrieval_strategy="rerank")
        col = await collections.create_collection("Docs", retrieval_strategy="hybrid")
        assert col["retrieval_strategy"] == "hybrid"
        with pytest.raises(ValueError, match="inconnue"):
            await collections.update_collection(col["id"], {"retrieval_strategy": "advanced"})
        # La valeur valide reste intacte après l'échec.
        still = await collections.get_collection(col["id"])
        assert still["retrieval_strategy"] == "hybrid"

    asyncio.run(scenario())


# ── Recommandation (fondée sur les capacités réelles) ────────────────────────

def test_recommendation_follows_real_engine_capabilities():
    """La recommandation appartient au Core et suit l'état réel du moteur :
    embeddings réels → hybrid ; embeddings mock → auto (jamais une stratégie
    qui se dégraderait immédiatement)."""

    # Sans client d'embedding → auto.
    rec_mock = _mock_pipeline().recommend_strategy()
    assert rec_mock["strategy_id"] == "auto"
    assert rec_mock["has_real_embeddings"] is False
    assert rec_mock["reason"]

    # Avec un client d'embedding réel → hybrid.
    rec_real = _pipeline().recommend_strategy()
    assert rec_real["strategy_id"] == "hybrid"
    assert rec_real["has_real_embeddings"] is True
    assert rec_real["reason"]

    # La fonction pure est cohérente et ne recommande JAMAIS une stratégie
    # non implémentée (garde-fou anti-stratégie fantôme).
    real_ids = {s["id"] for s in available_strategies()}
    for rec in (recommend_strategy(True), recommend_strategy(False)):
        assert rec["strategy_id"] in real_ids
