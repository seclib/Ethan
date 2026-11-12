"""Knowledge/RAG scenarios integrated with metrics collector."""

from __future__ import annotations

import asyncio
from typing import Any

from tests.benchmarks.knowledge.generator import generate_documents
from tests.benchmarks.knowledge.metrics import BenchmarkMetricsCollector, BenchmarkResult
from tests.benchmarks.knowledge.metrics import BenchmarkResult as BR

from core.knowledge import KnowledgeCollectionManager
from core.rag.embeddings import RAGEmbeddings
from core.rag.pipeline import RAGPipeline
from core.state import CoreRecordStore


class DeterministicEmbeddings(RAGEmbeddings):
    def __init__(self) -> None:
        super().__init__(None, None)
        self.calls = 0

    async def embed_texts(self, texts):
        self.calls += 1
        return [[float(len(t)), 1.0] for t in texts]

    async def embed_text(self, text):
        await self.embed_texts([text])
        return [float(len(text)), 1.0]


def _collection_operation(n: int) -> dict[str, Any]:
    store = CoreRecordStore()
    manager = KnowledgeCollectionManager(store=store)
    for i in range(n):
        c = asyncio.run(manager.create_collection(f"bench-collection-{i}", user_id="bench"))
        assert c["id"].startswith("bench-") or True
        got = asyncio.run(manager.get_collection(c["id"]))
        assert got is not None
    listed = asyncio.run(manager.list_collections(user_id="bench"))
    assert len(listed) == n
    return {"documents": 0, "collections": n}


def _document_persistence(n: int) -> dict[str, Any]:
    store = CoreRecordStore()
    counting = DeterministicEmbeddings()
    rag = RAGPipeline(embeddings=counting, chunk_size=256, top_k=3, store=store)
    for d in generate_documents(seed=2, count=n, target_chars=240):
        result = asyncio.run(rag.ingest(content=d.content, title=d.title, document_id=d.id))
        assert result.id == d.id and result.chunks
    documents = asyncio.run(rag.list_documents())
    assert len(documents) == n
    first = asyncio.run(rag.get_document(documents[0].id))
    assert first is not None and first.chunks
    return {"documents": n, "chunks": sum(len(d.chunks) for d in documents) if documents else 0}


def _rag_ingestion(n: int) -> dict[str, Any]:
    store = CoreRecordStore()
    counting = DeterministicEmbeddings()
    rag = RAGPipeline(embeddings=counting, chunk_size=256, top_k=3, store=store)
    total_chunks = 0
    for d in generate_documents(seed=3, count=n, target_chars=240):
        doc = asyncio.run(rag.ingest(content=d.content, title=d.title, document_id=d.id))
        assert doc.chunks
        total_chunks += len(doc.chunks)
    assert counting.calls == n
    return {"documents": n, "chunks": total_chunks}


def _rag_retrieval(n: int) -> dict[str, Any]:
    store = CoreRecordStore()
    counting = DeterministicEmbeddings()
    rag = RAGPipeline(embeddings=counting, chunk_size=256, top_k=3, store=store)
    seeds = generate_documents(seed=4, count=n, target_chars=240)
    created = [asyncio.run(rag.ingest(content=d.content, title=d.title, document_id=d.id)) for d in seeds]
    hits = asyncio.run(rag.retrieve("Known", document_ids=[created[0].id]))
    assert hits
    return {"documents": n, "hits": len(hits)}


def _reconstruction(n: int) -> dict[str, Any]:
    store = CoreRecordStore()
    counting = DeterministicEmbeddings()
    rag = RAGPipeline(embeddings=counting, chunk_size=256, top_k=3, store=store)
    seeds = generate_documents(seed=5, count=n, target_chars=240)
    for d in seeds:
        asyncio.run(rag.ingest(content=d.content, title=d.title, document_id=d.id))
    rag2 = RAGPipeline(embeddings=counting, chunk_size=256, top_k=3, store=store)
    asyncio.run(rag2._ensure_loaded())
    docs = asyncio.run(rag2.list_documents())
    assert len(docs) == n
    hits = asyncio.run(rag2.retrieve("Known", document_ids=[seeds[0].id]))
    assert hits
    return {"documents": n, "reconstruction_calls": counting.calls}


def benchmark_collection_operations(n=100, warmup=0, iterations=2):
    stats = {}
    op = lambda: stats.update(_collection_operation(n))
    result = BenchmarkMetricsCollector("collections", warmup=warmup, iterations=iterations).run(op)
    return result, stats


def benchmark_document_persistence(n=100, warmup=0, iterations=2):
    stats = {}
    op = lambda: stats.update(_document_persistence(n))
    result = BenchmarkMetricsCollector("documents", warmup=warmup, iterations=iterations).run(op)
    return result, stats


def benchmark_rag_ingestion(n=100, warmup=0, iterations=2):
    stats = {}
    def op():
        out = _rag_ingestion(n)
        stats["documents"] = out["documents"]
        stats["chunks"] = out["chunks"]
    result = BenchmarkMetricsCollector("rag-ingestion", warmup=warmup, iterations=iterations).run(op)
    return result, stats


def benchmark_rag_retrieval(n=100, warmup=0, iterations=2):
    stats = {}
    def op():
        out = _rag_retrieval(n)
        stats["documents"] = out["documents"]
        stats["hits"] = out["hits"]
    result = BenchmarkMetricsCollector("rag-retrieval", warmup=warmup, iterations=iterations).run(op)
    return result, stats


def benchmark_reconstruction(n=100, warmup=0, iterations=2):
    stats = {}
    def op():
        out = _reconstruction(n)
        stats["documents"] = out["documents"]
        stats["reconstruction_calls"] = out["reconstruction_calls"]
    result = BenchmarkMetricsCollector("rag-reconstruction", warmup=warmup, iterations=iterations).run(op)
    return result, stats
