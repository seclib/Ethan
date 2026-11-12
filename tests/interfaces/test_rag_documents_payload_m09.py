"""Tests ciblés M09 — payload des endpoints RAG documents (v1.py).

Défaut démontré : `GET /v1/rag/documents` sérialisait les chunks complets
(texte + vecteurs d'embedding) de chaque document → 190 MB de JSON, 128 MB
de table humaine, timeout client par défaut dépassé.

- la liste renvoie des résumés : `chunk_count`, sans `chunks` ni embeddings ;
- le détail renvoie les chunks sans les vecteurs d'embedding ;
- le stockage durable (`to_dict`) est inchangé (régression).
"""

from __future__ import annotations

import pytest
from core.rag.ingestion import DocumentChunk, IngestedDocument
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from interfaces.api.routers.v1 import CoreDomainServices, router, set_core_domain_services

DOCUMENT = IngestedDocument(
    id="doc-1",
    title="Terraform labs",
    source="file:///tmp/doc.md",
    content="contenu source",
    chunks=[
        DocumentChunk(
            id="chunk-1",
            document_id="doc-1",
            content="premier chunk",
            embedding=[0.1] * 1024,
            order=0,
        ),
        DocumentChunk(
            id="chunk-2",
            document_id="doc-1",
            content="second chunk",
            embedding=[0.2] * 1024,
            order=1,
        ),
    ],
    metadata={"origin": "test"},
)


class _FakeRAG:
    """Pipeline RAG minimal pour les routes de lecture."""

    def __init__(self, documents: list[IngestedDocument]):
        self._documents = documents

    async def list_documents(self) -> list[IngestedDocument]:
        return list(self._documents)

    async def get_document(self, document_id: str) -> IngestedDocument | None:
        return next((d for d in self._documents if d.id == document_id), None)


@pytest.fixture
def client():
    """FastAPI avec le router v1 et un RAG factice injecté (restauré ensuite)."""
    from interfaces.api.routers import v1

    original = v1._domains
    set_core_domain_services(CoreDomainServices(rag=_FakeRAG([DOCUMENT])))
    app = FastAPI()
    app.include_router(router)
    yield app
    set_core_domain_services(original)


@pytest.mark.asyncio
async def test_list_documents_returns_summaries(client) -> None:
    """La liste expose `chunk_count` et n'embarque ni chunks ni embeddings."""
    transport = ASGITransport(app=client)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/rag/documents")

    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    doc = items[0]
    assert doc["id"] == "doc-1"
    assert doc["chunk_count"] == 2
    assert "chunks" not in doc
    assert doc["content"] == "contenu source"


@pytest.mark.asyncio
async def test_document_detail_has_chunks_without_embeddings(client) -> None:
    """Le détail conserve les chunks (texte) mais jamais les vecteurs."""
    transport = ASGITransport(app=client)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/rag/documents/doc-1")

    assert res.status_code == 200
    doc = res.json()
    assert [c["id"] for c in doc["chunks"]] == ["chunk-1", "chunk-2"]
    assert doc["chunks"][0]["content"] == "premier chunk"
    assert all("embedding" not in c for c in doc["chunks"])


@pytest.mark.asyncio
async def test_document_detail_unknown_id_is_404(client) -> None:
    transport = ASGITransport(app=client)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/rag/documents/unknown")

    assert res.status_code == 404


def test_durable_storage_shape_is_unchanged() -> None:
    """Régression : le format de stockage durable garde content + embedding."""
    stored = DOCUMENT.chunks[0].to_dict()
    assert stored["content"] == "premier chunk"
    assert stored["embedding"] == [0.1] * 1024

    full = DOCUMENT.to_dict()
    assert full["chunks"][0]["embedding"] == [0.1] * 1024
