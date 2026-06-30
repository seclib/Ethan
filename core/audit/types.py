"""Types du module d'audit — entrées immuables du journal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class AuditCategory(StrEnum):
    """Catégories d'événements d'audit."""

    SYSTEM = "system"
    COMMAND = "command"
    APPROVAL = "approval"
    BUDGET = "budget"
    GATE = "gate"
    PLUGIN = "plugin"
    SKILL = "skill"
    MEMORY = "memory"
    SECURITY = "security"
    ERROR = "error"
    MISSION = "mission"
    PROACTIVE = "proactive"


class AuditDecision(StrEnum):
    """Décision d'audit possible."""

    ALLOWED = "allowed"
    DENIED = "denied"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    AUTO = "auto"
    DRY_RUN = "dry_run"
    PENDING = "pending"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class AuditEntry:
    """Entrée d'audit immuable.

    Une fois créée, une entrée ne peut jamais être modifiée.
    L'horodatage est figé à la création.
    """

    id: str = field(default_factory=lambda: f"aud_{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    category: AuditCategory = AuditCategory.SYSTEM
    decision: AuditDecision = AuditDecision.AUTO
    action: str = ""
    actor: str = "system"
    source: str = "system"
    details: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'entrée en dictionnaire pour stockage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "decision": self.decision.value,
            "action": self.action,
            "actor": self.actor,
            "source": self.source,
            "details": self.details,
            "correlation_id": self.correlation_id,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEntry:
        """Désérialise depuis un dictionnaire."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            category=AuditCategory(data["category"]),
            decision=AuditDecision(data["decision"]),
            action=data["action"],
            actor=data["actor"],
            source=data["source"],
            details=data.get("details", {}),
            correlation_id=data.get("correlation_id", ""),
            tags=data.get("tags", []),
        )