"""Knowledge Types — Types de données pour le module Knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KnowledgeType(str, Enum):
    """Types de nœuds de connaissance."""
    CONCEPT = "concept"
    FACT = "fact"
    RULE = "rule"
    ENTITY = "entity"
    SOURCE = "source"
    DOCUMENT = "document"


@dataclass
class KnowledgeConnection:
    """Connexion entre deux nœuds de connaissance."""
    id: str
    from_node_id: str
    to_node_id: str
    relation_type: str = "related_to"
    strength: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize a relation for durable storage."""
        return {
            "id": self.id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeConnection":
        """Rebuild a relation from storage."""
        return cls(
            id=data["id"],
            from_node_id=data["from_node_id"],
            to_node_id=data["to_node_id"],
            relation_type=data.get("relation_type", "related_to"),
            strength=float(data.get("strength", 1.0)),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow(),
        )


@dataclass
class KnowledgeNode:
    """Nœud de connaissance persistante."""
    id: str
    label: str
    node_type: KnowledgeType = KnowledgeType.CONCEPT
    content: str = ""
    source: str = ""
    connections: list[KnowledgeConnection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le nœud en dict."""
        return {
            "id": self.id,
            "label": self.label,
            "node_type": self.node_type.value,
            # `type` is retained for existing API/WebUI clients.  New Core
            # callers should use the explicit `node_type` field.
            "type": self.node_type.value,
            "content": self.content,
            "source": self.source,
            "connections": [connection.to_dict() for connection in self.connections],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeNode":
        """Désérialise un nœud depuis un dict."""
        return cls(
            id=data["id"],
            label=data.get("label", ""),
            node_type=KnowledgeType(data.get("node_type", "concept")),
            content=data.get("content", ""),
            source=data.get("source", ""),
            connections=[
                KnowledgeConnection.from_dict(c)
                for c in data.get("connections", [])
            ],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.utcnow(),
        )
