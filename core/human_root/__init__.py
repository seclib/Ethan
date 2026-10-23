"""Core — Human Root of Trust.

Le Human Root of Trust (HROT) est le pilier de la confiance humaine dans ETHAN.

Principes :
1. L'humain est la source unique de confiance.
2. Aucune action sensible ne s'exécute sans approbation humaine explicite.
3. Le HROT est inaltérable : toute décision critique est auditée et signée.
4. Le HROT ne délègue jamais son autorité ; il la demande.

Les modules appellent `HumanRoot` pour toute action critique :
- modifs du système d'exploitation
- accès à des données persistantes sensibles
- exécution de code arbitraire
- suppression de ressources
- changements de configuration de sécurité

Tout appel vers HROT retourne une réponse qui est stockée en append-only
dans l'audit log et, si besoin, publiée sur l'Event Bus.
"""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.approval import ApprovalEngine, ApprovalRequest, ApprovalResponse, ApprovalStatus

logger = logging.getLogger(__name__)


class TrustRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class TrustAction:
    """Représente une action dont la confiance repose sur un humain."""

    action_id: str
    caller: str
    category: str
    risk: TrustRisk
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""

    def signature(self) -> str:
        payload = f"{self.action_id}|{self.caller}|{self.category}|{self.risk.value}|{self.summary}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ApprovalOutcome(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TrustDecision:
    """Décision finale d'un appel HROT."""

    action_id: str
    category: str
    risk: TrustRisk
    outcome: ApprovalOutcome
    resolved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: str = ""
    reason: str = ""
    signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "category": self.category,
            "risk": self.risk.value,
            "outcome": self.outcome.value,
            "resolved_at": self.resolved_at.isoformat(),
            "trace_id": self.trace_id,
            "reason": self.reason,
            "signature": self.signature,
        }


class HumanRoot:
    """Moteur du Human Root of Trust."""

    def __init__(
        self,
        approval_engine: ApprovalEngine | None = None,
        audit_log: "AuditLog" | None = None,
    ) -> None:
        self._approval_engine = approval_engine
        self._audit = audit_log if audit_log is not None else AuditLog()
        self._in_flight: dict[str, TrustAction] = {}

    def _default_publish(self, request: ApprovalRequest) -> None:
        logger.info("HROT approve: %s (%s)", request.category, request.title)

    def request_approval(
        self,
        caller: str,
        category: str,
        summary: str,
        risk: TrustRisk,
        details: dict[str, Any] | None = None,
        timeout_seconds: int = 300,
        trace_id: str = "",
    ) -> str:
        """Demande l'avalisation humaine d'une action critique.

        Retourne l'identifiant de la requête, qui peut être résolu via le
        moteur d'approbation.
        """
        request = ApprovalRequest(
            category=category,
            title=f"HROT [{risk.value.upper()}] {summary}",
            description=summary,
            details=details or {},
            source="human_root",
            source_id=caller,
            timeout_seconds=timeout_seconds,
            correlation_id=trace_id,
        )
        if self._approval_engine is not None:
            self._approval_engine.request(  # type: ignore[func-returns-value]
                request.category.value,
                title=request.title,
                description=request.description,
                details=request.details,
                source="human_root",
                source_id=caller,
                timeout_seconds=timeout_seconds,
                correlation_id=trace_id,
            )
        action_id = request.id
        self._in_flight[action_id] = TrustAction(
            action_id=action_id,
            caller=caller,
            category=category,
            risk=risk,
            summary=summary,
            details=details or {},
            trace_id=trace_id,
        )
        logger.info("HROT request #%s for %s (%s)", action_id, summary, risk.value)
        return action_id

    def resolve(
        self,
        action_id: str,
        approved: bool,
        reason: str = "",
        responder: str = "human",
    ) -> TrustDecision:
        """Résout une demande de confiance par un humain."""
        action = self._in_flight.get(action_id)
        if action is None:
            raise KeyError(f"HROT action {action_id} not found")
        outcome = ApprovalOutcome.APPROVED if approved else ApprovalOutcome.REJECTED
        decision = TrustDecision(
            action_id=action_id,
            category=action.category,
            risk=action.risk,
            outcome=outcome,
            reason=reason,
            trace_id=action.trace_id or "",
            signature=action.signature(),
        )
        if self._audit is not None:
            self._audit.record(decision.to_dict())
        return decision

    def is_human_root_trusted(self, action_id: str) -> bool:
        return action_id in self._in_flight and self._in_flight[action_id].risk != TrustRisk.CRITICAL

from .audit_log import AuditLog

__all__ = [
    "HumanRoot",
    "AuditLog",
    "TrustRisk",
    "TrustAction",
    "TrustDecision",
    "ApprovalOutcome",
]
