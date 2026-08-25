"""Knowledge collections — Core-owned grouping of RAG documents.

ETHAN Core owns knowledge collections.  A collection groups RAG documents so
the WebUI can offer Open-WebUI-style selection ("use this collection in the
chat") without owning any data or logic.

The collection itself is a lightweight record; the documents live in the
RAGPipeline catalogue.  Retrieval is delegated to the RAG pipeline with a
collection filter.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.rag.pipeline import RAGPipeline
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_COLLECTIONS = "knowledge-collections"


class KnowledgeCollectionManager:
    """Own knowledge collections and their document membership."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
        rag: RAGPipeline | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()
        self._rag = rag or RAGPipeline()

    # ── CRUD collections ────────────────────────────────────────────────

    async def create_collection(
        self,
        name: str,
        description: str = "",
        user_id: str = "anonymous",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a knowledge collection."""
        normalized = name.strip()
        if not normalized:
            raise ValueError("Collection name must not be empty")
        collection = {
            "id": str(uuid4()),
            "name": normalized,
            "description": description,
            "user_id": user_id,
            "document_ids": [],
            "metadata": dict(metadata or {}),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        await self._store.save(_DOMAIN_COLLECTIONS, collection["id"], collection)
        await self._publish(EventType.KNOWLEDGE_CREATED, "knowledge.collection.created", {"collection": collection})
        return collection

    async def get_collection(self, collection_id: str) -> dict[str, Any] | None:
        """Retrieve a collection by id."""
        return await self._store.get(_DOMAIN_COLLECTIONS, collection_id)

    async def list_collections(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List collections, optionally filtered by owner."""
        collections = await self._store.list(_DOMAIN_COLLECTIONS)
        if user_id is not None:
            collections = [c for c in collections if c.get("user_id") == user_id]
        return collections

    async def update_collection(
        self, collection_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update collection metadata."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            return None
        for key in ("name", "description", "metadata"):
            if key in data:
                collection[key] = data[key]
        collection["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        await self._publish(EventType.KNOWLEDGE_UPDATED, "knowledge.collection.updated", {"collection": collection})
        return collection

    async def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection (documents remain in the RAG catalogue)."""
        existed = await self._store.delete(_DOMAIN_COLLECTIONS, collection_id)
        if existed:
            await self._publish(EventType.KNOWLEDGE_DELETED, "knowledge.collection.deleted", {"collection_id": collection_id})
        return existed

    # ── Document membership ─────────────────────────────────────────────

    async def add_document(self, collection_id: str, document_id: str) -> dict[str, Any] | None:
        """Attach an existing RAG document to a collection."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            return None
        document = await self._rag.get_document(document_id)
        if document is None:
            raise ValueError(f"RAG document {document_id} not found")
        if document_id not in collection["document_ids"]:
            collection["document_ids"].append(document_id)
            collection["updated_at"] = _utc_now()
            await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        return collection

    async def remove_document(self, collection_id: str, document_id: str) -> dict[str, Any] | None:
        """Detach a document from a collection."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            return None
        if document_id in collection["document_ids"]:
            collection["document_ids"].remove(document_id)
            collection["updated_at"] = _utc_now()
            await self._store.save(_DOMAIN_COLLECTIONS, collection_id, collection)
        return collection

    async def list_documents(self, collection_id: str) -> list[dict[str, Any]]:
        """List the RAG documents attached to a collection."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            return []
        documents = []
        for document_id in collection.get("document_ids", []):
            document = await self._rag.get_document(document_id)
            if document is not None:
                documents.append(document.to_dict())
        return documents

    # ── Retrieval scoped to a collection ────────────────────────────────

    async def retrieve(
        self,
        query: str,
        collection_id: str,
        *,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve chunks restricted to one collection's documents."""
        collection = await self.get_collection(collection_id)
        if collection is None:
            raise ValueError(f"Collection {collection_id} not found")
        allowed = set(collection.get("document_ids", []))
        chunks = await self._rag.retrieve(query, top_k=top_k)
        return [
            {
                "chunk": item.chunk.to_dict(),
                "score": item.score,
                "document_title": item.document_title,
                "document_source": item.document_source,
            }
            for item in chunks
            if item.chunk.document_id in allowed
        ]

    async def build_context(
        self,
        query: str,
        collection_id: str,
        *,
        top_k: int | None = None,
    ) -> str:
        """Build a bounded RAG context restricted to one collection."""
        results = await self.retrieve(query, collection_id, top_k=top_k)
        if not results:
            return ""
        parts = []
        for i, item in enumerate(results, start=1):
            title = item.get("document_title") or "Document"
            source = item.get("document_source") or ""
            chunk = item.get("chunk", {})
            content = chunk.get("content", "")
            parts.append(f"[{i}] {title} ({source})\n{content}")
        return "\n\n".join(parts)

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="knowledge-collections", payload=payload))


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["KnowledgeCollectionManager"]