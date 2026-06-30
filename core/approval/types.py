"""Types du module d'approbation — requêtes, réponses, statuts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class ApprovalCategory(StrEnum):
    """Catégories d'actions nécessitant approbation."""

    FILE_WRITE = "file_write"
    COMMAND_EXEC = "command_exec"
    NETWORK_ACCESS = "network_access"
    PLUGIN_INSTALL = "plugin_install"
    SKILL_INSTALL = "skill_install"
    MISSION_STEP = "mission_step"
    PROACTIVE_ACTION = "proactive_action"
    EMAIL_SEND = "email_send"
    DATA_EXPORT = "data_export"
    SYSTEM_MODIFY = "system_modify"
    COST_THRESHOLD = "cost_threshold"


class ApprovalStatus(StrEnum):
    """Statut d'une requête d'approbation."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ApprovalRequest:
    """Requête d'approbation envoyée à l'humain."""

    id: str = field(default_factory=lambda: f"app_{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    category: ApprovalCategory = ApprovalCategory.MISSION_STEP
    title: str = ""
    description: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    source_id: str = ""
    timeout_seconds: int = 300
    correlation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "details": self.details,
            "source": self.source,
            "source_id": self.source_id,
            "timeout_seconds": self.timeout_seconds,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True)
class ApprovalResponse:
    """Réponse à une requête d'approbation."""

    request_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    responder: str = "human"

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "responder": self.responder,
        }