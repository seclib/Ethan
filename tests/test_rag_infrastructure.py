"""tests/test_rag_infrastructure.py — RAG pipeline: chunking, embeddings,
dimension validation, backend failure, re-indexing, deleted documents.

Couverture demandée :
- chunking (stratégies character / sentence / paragraph + taille/overlap)
- embedded failure (fallback mock dimensionnellement cohérent)
- dimension mismatch (rejet à l'ingestion + validation upsert Qdrant)
- Qdrant failure (backend indisponible / panne runtime → la recherche et
  l'ingestion ne cassent pas ; fallback mémoire)
- re-indexing (les documents déjà ingérés sont ré-indexés à l'ouverture)
- deleted documents (purge catalogue + index vectoriel)

Ces tests ne touchent AUCUN service externe : qdrant/chromadb ne sont pas
installés, on teste donc le chemin d'échec réel (RuntimeError via import
paresseux) et des fakes mémoire pour les backends.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from core.rag.embeddings import RAGEmbeddings
from core.rag.ingestion import RAGIngestion
from core.rag.pipeline import RAGPipeline
from core.rag.vector_store import RAGVectorStore, QdrantVectorStore
from core.state.record_store import CoreRecordStore


class FailingEmbeddings(RAGEmbeddings):
    """Client d'embedding qui échoue systématiquement (réseau/provider down)."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embedding service unavailable")

    async def embed_text(self, text: str) -> list[float]:
        raise RuntimeError("embedding service unavailable")


class MixedDimEmbeddings(RAGEmbeddings):
    """Client qui change de dimension entre deux appels (bug provider)."""

    def __init__(self) -> None:
        self._calls = 0

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._calls += 1
        dim = 3 if self._calls == 1 else 7
        return [[float(i + 1) / 10 for i in range(dim)] for _ in texts]

    async def embed_text(self, text: str) -> list[float]:
        return (await self.embed_texts([text]))[0]


class EmptyEmbeddings(RAGEmbeddings):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[] for _ in texts]


class FakeVectorStore(RAGVectorStore):
    """Backend fake qui comptabilise les upserts / suppressions."""

    name = "fake"

    def __init__(self) -> None:
        self.records: list[dict] = []
        self.upsert_calls = 0
        self.deleted: list[str] = []

    async def upsert(self, records: list[dict]) -> None:
        self.upsert_calls += 1
        self.records.extend(records)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        return []

    async def delete_document(self, document_id: str) -> None:
        self.deleted.append(document_id)


class ExplodingStore(RAGVectorStore):
    """Backend qui lève systématiquement à l'upsert (panne runtime)."""

    name = "exploding"

    async def upsert(self, records: list[dict]) -> None:
        raise RuntimeError("qdrant connection refused")

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        return []

    async def delete_document(self, document_id: str) -> None:
        pass


def _pipeline() -> RAGPipeline:
    return RAGPipeline(store=CoreRecordStore())

# ── Chunking (stratégies + taille/overlap) ───────────────────────────────────


class TestChunking:
    def test_character_respects_size(self):
        text = "un deux trois quatre cinq six sept huit neuf dix " * 20
        ingestion = RAGIngestion(chunk_size=50, chunk_overlap=10, splitting_strategy="character")
        chunks = ingestion._chunk_text(text)
        assert len(chunks) > 1
        assert all(len(c) <= 50 for c in chunks)

    def test_sentence_strategy_groups_sentences(self):
        text = "Un. Deux. CinQ. Six. " * 5
        ingestion = RAGIngestion(chunk_size=40, chunk_overlap=5, splitting_strategy="sentence")
        chunks = ingestion._chunk_text(text)
        assert len(chunks) > 1
        assert all(len(c) <= 40 for c in chunks)

    def test_paragraph_strategy_keeps_paragraphs(self):
        text = "Para un contenu complet sur le RAG.\n\nPara deux avec du texte.\n\nPara trois."
        ingestion = RAGIngestion(chunk_size=1000, chunk_overlap=0, splitting_strategy="paragraph")
        chunks = ingestion._chunk_text(text)
        assert len(chunks) >= 1
        assert any("Para un" in c for c in chunks)

    def test_reconfigure_strategy_hot(self):
        ingestion = RAGIngestion()
        ingestion.set_chunking(splitting_strategy="sentence")
        assert ingestion._splitting_strategy == "sentence"
        with pytest.raises(ValueError):
            ingestion.set_chunking(splitting_strategy="does-not-exist")


# ── Embedding failure (fallback) ────────────────────────────────────────────


class TestEmbeddingFailure:
    @pytest.mark.asyncio
    async def test_failing_llm_falls_back_to_mock(self):
        """RAGEmbeddings non configuré → mock dimensionnellement stable."""
        emb = RAGEmbeddings()
        vectors = await emb.embed_texts(["a", "b", "c"])
        assert len(vectors) == 3
        assert all(len(v) == 8 for v in vectors)

    @pytest.mark.asyncio
    async def test_embedding_error_does_not_raise_on_fallback(self):
        """Un client qui lève → mock (dégradé, jamais de crash pipeline)."""

        class ExplodingClient:
            async def embed(self, texts, model=None):
                raise RuntimeError("network down")

        emb = RAGEmbeddings(llm_client=ExplodingClient())
        vectors = await emb.embed_texts(["hello"])
        assert len(vectors) == 1
        assert len(vectors[0]) == 8

    @pytest.mark.asyncio
    async def test_failed_ingestion_not_catalogued(self):
        ingestion = RAGIngestion(embeddings=FailingEmbeddings())
        with pytest.raises(RuntimeError):
            await ingestion.ingest("Un contenu de test.", title="T")
        assert ingestion.list_documents() == []


# ── Dimension mismatch ──────────────────────────────────────────────────────


class TestDimensionMismatch:
    @pytest.mark.asyncio
    async def test_in_document_mixed_dims_raises(self):
        ingestion = RAGIngestion(embeddings=MixedDimEmbeddings())
        await ingestion.ingest("aaaa bbbb cccc dddd.", title="A")
        with pytest.raises(ValueError, match="dimension mismatch"):
            await ingestion.ingest("zzz www yyy xxx.", title="B")

    @pytest.mark.asyncio
    async def test_empty_embedding_raises(self):
        ingestion = RAGIngestion(embeddings=EmptyEmbeddings())
        with pytest.raises(ValueError, match="empty embedding"):
            await ingestion.ingest("contenu", title="T")

    def test_qdrant_upsert_validates_dimension(self):
        """QdrantVectorStore refuse un upsert dont la dimension diffère
        du vector_size configuré — avant tout appel réseau."""
        store = QdrantVectorStore(host="localhost", port=6333, vector_size=8)
        store._client = object()  # simule un client déjà initialisé
        try:
            import asyncio
            asyncio.run(store.upsert([
                {"chunk_id": "c1", "embedding": [1, 2, 3], "document_id": "d1"}
            ]))
            pytest.fail("Expected dimension mismatch")
        except ValueError as exc:
            assert "dimension mismatch" in str(exc)


# ── Qdrant failure (fallback / résilience) ─────────────────────────────────


class TestQdrantFailure:
    @pytest.mark.asyncio
    async def test_unavailable_backend_falls_back_to_memory(self):
        """qdrant-client absent → connexion impossible ; le pipeline retombe
        en mémoire (cosine) et la recherche fonctionne toujours."""
        p = RAGPipeline(store=CoreRecordStore())
        await p.configure(
            vector_backend="qdrant",
            vector_backend_config={"host": "localhost", "port": 6333},
        )
        doc = await p.ingest(
            "Qdrant indisponible mais la recherche Core reste fonctionnelle.",
            title="T",
        )
        results = await p.retrieve("recherche Core")
        assert isinstance(results, list)
        assert p.stats()["vector_backend"] == "qdrant"  # config gardée
        await p.delete_document(doc.id)

    @pytest.mark.asyncio
    async def test_runtime_upsert_failure_keeps_document(self):
        """Une panne runtime à l'upsert ne retire pas le document du catalogue
        (index_document attrape l'exception)."""
        p = RAGPipeline(store=CoreRecordStore())
        p._retrieval.attach_vector_store(ExplodingStore())
        doc = await p.ingest("Document avec des embeddings réels de test.", title="T")
        assert doc.id in {d.id for d in await p.list_documents()}
        await p.delete_document(doc.id)


# ── Re-indexing à l'ouverture ──────────────────────────────────────────────


class TestReindexing:
    @pytest.mark.asyncio
    async def test_reindex_on_load_populates_new_backend(self, monkeypatch):
        store = CoreRecordStore()
        p = RAGPipeline(store=store)
        d1 = await p.ingest("Premier document de reindexation.", title="Doc1")
        d2 = await p.ingest("Second document.", title="Doc2")

        # Le ré-indexage réel passe par un backend configuré : on mappe
        # create_vector_store vers un fake pour simuler un backend externe
        # sans dépendance réseau.
        from core.rag import pipeline as rag_pipeline_module

        fake = FakeVectorStore()
        monkeypatch.setattr(
            rag_pipeline_module,
            "create_vector_store",
            lambda backend, config=None: fake,
        )

        # Nouvelle instance sur le même store, backend externe configuré :
        # à l'ouverture, les documents restaurés sont ré-indexés.
        p2 = RAGPipeline(store=store, vector_backend="qdrant")
        await p2._ensure_loaded()

        assert fake.upsert_calls > 0
        assert all(r["document_id"] in {d1.id, d2.id} for r in fake.records)
        assert {r["document_id"] for r in fake.records} == {d1.id, d2.id}

    @pytest.mark.asyncio
    async def test_idempotent_reindex_same_chunk_ids(self, monkeypatch):
        store = CoreRecordStore()
        p = RAGPipeline(store=store)
        await p.ingest("Document stable pour le test d'idempotence.", title="M")

        from core.rag import pipeline as rag_pipeline_module

        fake1 = FakeVectorStore()
        fake2 = FakeVectorStore()
        stores = iter([fake1, fake2])
        monkeypatch.setattr(
            rag_pipeline_module,
            "create_vector_store",
            lambda backend, config=None: next(stores),
        )

        p2 = RAGPipeline(store=store, vector_backend="qdrant")
        await p2._ensure_loaded()
        ids1 = {r["chunk_id"] for r in fake1.records}

        p3 = RAGPipeline(store=store, vector_backend="qdrant")
        await p3._ensure_loaded()
        ids2 = {r["chunk_id"] for r in fake2.records}

        assert ids1 == ids2


# ── Deleted documents ──────────────────────────────────────────────────────


class TestDeletedDocuments:
    @pytest.mark.asyncio
    async def test_delete_removes_from_catalogue_and_store(self):
        store = CoreRecordStore()
        p = RAGPipeline(store=store)
        d1 = await p.ingest("Premier document à supprimer.", title="D1")
        d2 = await p.ingest("Second document conservé.", title="D2")

        fake = FakeVectorStore()
        p._retrieval.attach_vector_store(fake)
        await p._load_vector_store()

        removed = await p.delete_document(d1.id)
        assert removed is True

        remaining = await p.list_documents()
        assert {d.id for d in remaining} == {d2.id}
        assert d1.id not in p._retrieval._documents
        assert d2.id in p._retrieval._documents

    @pytest.mark.asyncio
    async def test_delete_missing_document_returns_false(self):
        p = RAGPipeline(store=CoreRecordStore())
        removed = await p.delete_document("does-not-exist")
        assert removed is False

    @pytest.mark.asyncio
    async def test_search_excludes_deleted_document(self):
        p = RAGPipeline(store=CoreRecordStore())
        d1 = await p.ingest("Le renard roux court dans la forêt.", title="A")
        await p.ingest("La baleine bleue nage dans l'océan.", title="B")
        await p.delete_document(d1.id)

        results = await p.retrieve("forêt renard roux")
        assert all(c.chunk.document_id != d1.id for c in results)
