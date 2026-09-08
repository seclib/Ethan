"""Tests Core — réindexation d'une RAG Collection (rechunk + ré-embed).

Chaîne réelle : documents persistés d'une collection → suppression et
ré-ingestion via le pipeline Core (nouveaux ids de documents, chunks
régénérés), la collection pointant vers les nouveaux documents.
"""

from __future__ import annotations

import asyncio

import pytest

from core.knowledge import KnowledgeCollectionManager
from core.rag import RAGPipeline
from core.state import CoreRecordStore


def _collections() -> tuple[KnowledgeCollectionManager, RAGPipeline]:
    store = CoreRecordStore()
    rag = RAGPipeline(store=store)
    return KnowledgeCollectionManager(store=store, rag=rag), rag


def test_reindex_recreates_documents_and_keeps_source():
    """Réindexer remplace les documents par de nouveaux ids (rechunk+embed)."""

    async def scenario():
        collections, rag = _collections()
        doc = await rag.ingest(
            "Premier paragraphe de contenu significatif pour la collection.",
            title="Source", source="https://example.com/1",
            metadata={"web_url": "https://example.com/1"},
        )
        col = await collections.create_collection("Docs", user_id="alice")
        await collections.add_document(col["id"], doc.id)

        result = await collections.reindex_collection(col["id"])
        assert result["reindexed"] == 1
        assert result["documents"] == 1

        # La collection pointe vers un NOUVEAU document (ré-ingéré).
        updated_col = await collections.get_collection(col["id"])
        new_doc_id = updated_col["document_ids"][0]
        assert new_doc_id != doc.id
        # Le document d'origine a été purgé du piipeline.
        assert await rag.get_document(doc.id) is None
        # Le nouveau document conserve provenance + contenu.
        new_doc = await rag.get_document(new_doc_id)
        assert new_doc is not None
        assert new_doc.source == "https://example.com/1"
        assert new_doc.metadata.get("web_url") == "https://example.com/1"
        assert "contenu significatif" in new_doc.content

        # La liste des documents de la collection reflète le nouveau.
        listed = await collections.list_documents(col["id"])
        assert [d["id"] for d in listed] == [new_doc_id]

    asyncio.run(scenario())


def test_reindex_unknown_collection_raises():
    """Une collection inconnue lève ValueError (jamais de création implicite)."""

    async def scenario():
        collections, _ = _collections()
        with pytest.raises(ValueError):
            await collections.reindex_collection("ghost")

    asyncio.run(scenario())


def test_reindex_empty_collection_is_graceful():
    """Une collection sans documents → 0 réindexé, sans erreur."""

    async def scenario():
        collections, _ = _collections()
        col = await collections.create_collection("Vide", user_id="alice")
        result = await collections.reindex_collection(col["id"])
        assert result["reindexed"] == 0
        assert result["documents"] == 0

    asyncio.run(scenario())