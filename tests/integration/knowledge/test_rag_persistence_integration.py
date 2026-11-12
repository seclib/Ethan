"""Integration tests demonstrating Knowledge/RAG persistence and ACL reuse."""

from __future__ import annotations

import asyncio

import pytest

from core.knowledge import KnowledgeCollectionManager
from core.rag.embeddings import RAGEmbeddings
from core.rag.pipeline import RAGPipeline
from core.state import CoreRecordStore


class CountingEmbeddings(RAGEmbeddings):
    """Deterministic embedding provider with an invocation counter."""

    def __init__(self):
        super().__init__(llm_client=None, model=None)
        self.calls = 0

    async def embed_texts(self, texts):
        self.calls += 1
        return [[float(len(t)), 1.0] for t in texts]

    async def embed_text(self, text):
        await self.embed_texts([text])
        return [float(len(text)), 1.0]


@pytest.mark.asyncio
async def test_rag_persistence_reconstruction_and_acl():
    store = CoreRecordStore()
    counting = CountingEmbeddings()
    rag = RAGPipeline(embeddings=counting, chunk_size=1000, top_k=3, store=store)
    rag.attach_llm_client(None)
    rag._ingestion._embeddings = counting
    rag._retrieval._embeddings = counting

    collection_manager = KnowledgeCollectionManager(store=store, rag=rag, groups=None)

    collection = await collection_manager.create_collection(
        "integration collection", user_id="owner"
    )
    rag.attach_llm_client(None)
    # keep custom embedder explicit in case attach reset it
    rag._ingestion._embeddings = counting
    rag._retrieval._embeddings = counting

    source = "Known token alpha here"
    first = await rag.ingest(content=source, title="alpha-doc", document_id="doc-alpha")
    await collection_manager.add_document(collection["id"], first.id)

    await counting.embed_texts([source])
    initial_calls = counting.calls
    assert initial_calls >= 1

    first_docs = await rag.list_documents()
    assert [d.id for d in first_docs] == ["doc-alpha"]

    second = await rag.ingest(content=source, title="alpha-doc", document_id="doc-alpha")
    assert second.id == "doc-alpha"

    # Recreate pipeline on the same store
    second_counting = CountingEmbeddings()
    rag2 = RAGPipeline(embeddings=second_counting, chunk_size=1000, top_k=3, store=store)
    await rag2._ensure_loaded()
    reconstruction_calls = second_counting.calls
    assert reconstruction_calls == 0
    listed = await rag2.list_documents()
    assert listed and listed[0].id == "doc-alpha"

    results = await rag2.retrieve("Known", document_ids=[first.id])
    assert results
    assert results[0].document_title == "alpha-doc"

    # ACL denial
    second_user = "intruder"
    allowed = await collection_manager.check_access(collection, second_user, permission="read")
    assert allowed is False

    collection = await collection_manager.share_collection(collection["id"], [{"user_id": second_user, "permission": "write"}])
    allowed = await collection_manager.check_access(collection, second_user, is_admin=False, permission="read")
    assert allowed is True

