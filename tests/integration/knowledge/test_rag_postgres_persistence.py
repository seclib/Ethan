"""PostgreSQL persistence integration test — safe and explicitly provisioned."""

from __future__ import annotations

import os
import uuid
from urllib.parse import urlparse

import asyncpg
import pytest

from core.knowledge import KnowledgeCollectionManager
from core.rag.embeddings import RAGEmbeddings
from core.rag.pipeline import RAGPipeline
from core.state import CoreRecordStore

pytestmark = pytest.mark.knowledge_postgres


class CountingEmbeddings(RAGEmbeddings):
    def __init__(self) -> None:
        super().__init__(None, None)
        self.calls = 0

    async def embed_texts(self, texts):
        self.calls += 1
        return [[float(len(text)), 1.0] for text in texts]

    async def embed_text(self, text):
        await self.embed_texts([text])
        return [float(len(text)), 1.0]


def _require_safe_env() -> str:
    url = os.environ.get("ETHAN_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("missing ETHAN_TEST_POSTGRES_URL")
    if os.environ.get("ETHAN_TEST_POSTGRES_SAFE") != "1":
        pytest.skip("missing ETHAN_TEST_POSTGRES_SAFE=1")
    parsed = urlparse(url)
    if parsed.username != "ethan_test":
        raise RuntimeError("test PostgreSQL user must be ethan_test")
    if (parsed.path or "").strip("/") != "ethan_knowledge_test":
        raise RuntimeError("test PostgreSQL database must be ethan_knowledge_test")
    return url


async def _connect_pool():
    url = _require_safe_env()
    pool = await asyncpg.create_pool(url)
    try:
        async with pool.acquire() as conn:
            if await conn.fetchval("SELECT current_database()") != "ethan_knowledge_test":
                raise RuntimeError("not the isolated test database")
            if await conn.fetchval("SELECT current_user") != "ethan_test":
                raise RuntimeError("not the isolated test user")
    except Exception:
        await pool.close()
        raise
    return pool


@pytest.mark.asyncio
async def test_postgres_persistence_integration():
    try:
        pool = await _connect_pool()
    except RuntimeError as exc:
        pytest.skip(str(exc))

    store = CoreRecordStore(pg_pool=pool)
    unique_doc_id = f"test-doc-{uuid.uuid4().hex}"
    unique_collection_id = None
    embedder = CountingEmbeddings()

    try:
        rag = RAGPipeline(embeddings=embedder, chunk_size=1000, top_k=3, store=store)
        collection_manager = KnowledgeCollectionManager(store=store, rag=rag)

        collection = await collection_manager.create_collection(
            name=f"test-collection-{uuid.uuid4().hex}",
            user_id="owner",
        )
        unique_collection_id = collection["id"]

        first = await rag.ingest(
            content="Known token alpha postgres persistence",
            title="pg-persistence",
            document_id=unique_doc_id,
        )
        await collection_manager.add_document(unique_collection_id, first.id)

        before_calls = embedder.calls
        assert before_calls >= 1
        assert len(first.chunks) >= 1

        results = await rag.retrieve("Known", document_ids=[unique_doc_id])
        assert results

        # Recreate Core instances using the same isolated DB.
        embedder2 = CountingEmbeddings()
        rag2 = RAGPipeline(embeddings=embedder2, chunk_size=1000, top_k=3, store=store)
        await rag2._ensure_loaded()
        rebuilt = await rag2.list_documents()
        assert any(d.id == unique_doc_id for d in rebuilt)

        rebuilt_results = await rag2.retrieve("Known", document_ids=[unique_doc_id])
        assert rebuilt_results
        assert embedder2.calls <= before_calls + 1

        # ACL denial/revoke should be explicit; behavior is reported as evidence.
        intruder = "intruder"
        collection_state = await collection_manager.get_collection(unique_collection_id)
        assert collection_state is not None
        assert await collection_manager.check_access(collection_state, intruder, permission="read") is False

        shared = await collection_manager.share_collection(unique_collection_id, [{"user_id": intruder, "permission": "write"}])
        assert await collection_manager.check_access(shared, intruder, permission="read") is True

        cleared = await collection_manager.share_collection(unique_collection_id, [])
        assert await collection_manager.check_access(cleared, intruder, permission="read") is False
    finally:
        if unique_collection_id:
            try:
                await store.delete("knowledge-collections", unique_collection_id)
            except Exception:
                pass
        try:
            await store.delete("rag-documents", unique_doc_id)
        except Exception:
            pass
        await pool.close()
