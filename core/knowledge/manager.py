"""Persistent knowledge graph owned by the ETHAN Core."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.knowledge.types import KnowledgeConnection, KnowledgeNode, KnowledgeType
from core.state.record_store import CoreRecordStore

if TYPE_CHECKING:
    from core.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """Own durable knowledge nodes, their sources and their relations."""

    _DOMAIN = "knowledge"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create(
        self,
        label: str,
        node_type: KnowledgeType | str = KnowledgeType.CONCEPT,
        content: str = "",
        source: str = "",
        connections: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeNode:
        """Create a knowledge node with optional outgoing relations."""
        normalized_label = label.strip()
        if not normalized_label:
            raise ValueError("Knowledge label must not be empty")
        kind = KnowledgeType(node_type)
        node = KnowledgeNode(
            id=str(uuid4()),
            label=normalized_label,
            node_type=kind,
            content=content,
            source=source,
            metadata=dict(metadata or {}),
        )
        for connection in connections or []:
            target_id = str(connection.get("to_node_id", "")).strip()
            if not target_id:
                raise ValueError("Knowledge connection requires to_node_id")
            node.connections.append(
                KnowledgeConnection(
                    id=str(uuid4()),
                    from_node_id=node.id,
                    to_node_id=target_id,
                    relation_type=str(connection.get("relation_type", "related_to")),
                    strength=float(connection.get("strength", 1.0)),
                    metadata=dict(connection.get("metadata", {})),
                )
            )
        await self._persist(node)
        await self._publish(EventType.KNOWLEDGE_CREATED, "knowledge.created", {"node": node.to_dict()})
        return node

    async def get(self, node_id: str) -> KnowledgeNode | None:
        """Retrieve one knowledge node."""
        data = await self._store.get(self._DOMAIN, node_id)
        return KnowledgeNode.from_dict(data) if data else None

    async def list(self, node_type: KnowledgeType | str | None = None) -> list[KnowledgeNode]:
        """List nodes, optionally restricted to one type."""
        kind = KnowledgeType(node_type) if node_type is not None else None
        nodes = [KnowledgeNode.from_dict(data) for data in await self._store.list(self._DOMAIN)]
        return [node for node in nodes if kind is None or node.node_type == kind]

    async def update(self, node_id: str, data: dict[str, Any]) -> KnowledgeNode | None:
        """Update node content or metadata without changing its identity."""
        node = await self.get(node_id)
        if node is None:
            return None
        if "label" in data:
            label = str(data["label"]).strip()
            if not label:
                raise ValueError("Knowledge label must not be empty")
            node.label = label
        if "node_type" in data:
            node.node_type = KnowledgeType(data["node_type"])
        if "content" in data:
            node.content = str(data["content"])
        if "source" in data:
            node.source = str(data["source"])
        if "metadata" in data:
            node.metadata.update(dict(data["metadata"]))
        node.updated_at = datetime.utcnow()
        await self._persist(node)
        await self._publish(EventType.KNOWLEDGE_UPDATED, "knowledge.updated", {"node": node.to_dict()})
        return node

    async def delete(self, node_id: str) -> bool:
        """Delete a node and remove relations pointing to it from all nodes."""
        existed = await self._store.delete(self._DOMAIN, node_id)
        if not existed:
            return False
        for node in await self.list():
            kept = [connection for connection in node.connections if connection.to_node_id != node_id]
            if len(kept) != len(node.connections):
                node.connections = kept
                node.updated_at = datetime.utcnow()
                await self._persist(node)
        await self._publish(EventType.KNOWLEDGE_DELETED, "knowledge.deleted", {"node_id": node_id})
        return True

    async def search(self, query: str, *, limit: int = 20) -> list[KnowledgeNode]:
        """Search labels, source and content deterministically in Core data."""
        terms = [term for term in query.casefold().split() if term]
        if not terms:
            return (await self.list())[:limit]

        scored: list[tuple[int, KnowledgeNode]] = []
        for node in await self.list():
            haystack = f"{node.label}\n{node.source}\n{node.content}".casefold()
            score = sum(term in haystack for term in terms)
            if score:
                scored.append((score, node))
        scored.sort(key=lambda item: (-item[0], item[1].label.casefold()))
        return [node for _, node in scored[:limit]]

    async def connect(
        self,
        from_node_id: str,
        to_node_id: str,
        relation_type: str = "related_to",
        strength: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeNode | None:
        """Create or replace a directed relation between two known nodes."""
        node = await self.get(from_node_id)
        if node is None:
            return None
        if await self.get(to_node_id) is None:
            raise ValueError(f"Knowledge node {to_node_id} not found")
        if not 0.0 <= strength <= 1.0:
            raise ValueError("Knowledge relation strength must be between 0 and 1")

        node.connections = [
            connection
            for connection in node.connections
            if not (
                connection.to_node_id == to_node_id
                and connection.relation_type == relation_type
            )
        ]
        node.connections.append(
            KnowledgeConnection(
                id=str(uuid4()),
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                relation_type=relation_type,
                strength=strength,
                metadata=dict(metadata or {}),
            )
        )
        node.updated_at = datetime.utcnow()
        await self._persist(node)
        await self._publish(EventType.KNOWLEDGE_UPDATED, "knowledge.updated", {"node": node.to_dict()})
        return node

    async def ingest_into_rag(self, node_id: str, rag: "RAGPipeline") -> str:
        """Expose a knowledge node to the RAG pipeline as a sourced document."""
        node = await self.get(node_id)
        if node is None:
            raise ValueError(f"Knowledge node {node_id} not found")
        document = await rag.ingest(
            content=node.content or node.label,
            title=node.label,
            source=node.source or f"knowledge:{node.id}",
            metadata={"knowledge_id": node.id, "knowledge_type": node.node_type.value},
        )
        return document.id

    async def _persist(self, node: KnowledgeNode) -> None:
        await self._store.save(self._DOMAIN, node.id, node.to_dict())

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="knowledge-manager", payload=payload))
