"""ApprovalEngine — Système d'approbation asynchrone.

Les modules peuvent :
1. Créer une requête d'approbation → publiée sur l'EventBus
2. Attendre la réponse humaine (asyncio.Future avec timeout)
3. Recevoir la résolution (approuvée/rejetée/timeout)

Utilise un pattern asyncio.Future pour l'attente non-bloquante.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from core.approval.types import (
    ApprovalCategory,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
)

logger = logging.getLogger(__name__)


def _default_publish(request: ApprovalRequest) -> None:
    """Publication par défaut : log uniquement."""
    logger.info(
        "Approval requested: [%s] %s — %s (timeout: %ss)",
        request.category.value,
        request.title,
        request.description[:100],
        request.timeout_seconds,
    )


class ApprovalEngine:
    """Moteur d'approbation asynchrone.

    Gère le cycle de vie complet des requêtes d'approbation :
    création → publication → attente → résolution → nettoyage.
    """

    def __init__(
        self,
        publish_fn: Callable[[ApprovalRequest], None] | None = None,
        audit_log_fn: Callable[..., None] | None = None,
    ) -> None:
        self._publish_fn = publish_fn or _default_publish
        self._audit_log_fn = audit_log_fn

        # Futures en attente : request_id → Future[ApprovalResponse]
        self._pending: dict[str, asyncio.Future[ApprovalResponse]] = {}
        # Détails affichables à l'humain qui doit décider. Les futures seules
        # ne permettent pas à une interface de présenter le périmètre réel.
        self._requests: dict[str, ApprovalRequest] = {}
        self._lock = asyncio.Lock()
        self._human_root: Any | None = None

    def set_human_root(self, human_root: Any) -> None:
        """Attache le Human Root of Trust comme autorité supérieure."""
        self._human_root = human_root

    # ── Création de requête ─────────────────────────────────────────

    async def create_request(
        self,
        category: ApprovalCategory | str,
        title: str = "",
        description: str = "",
        details: dict[str, Any] | None = None,
        source: str = "system",
        source_id: str = "",
        timeout_seconds: int = 300,
        correlation_id: str = "",
    ) -> ApprovalRequest:
        """Crée et publie une requête d'approbation sans attendre la décision.

        Permet à un flux SSE d'émettre la demande au client AVANT d'attendre
        la résolution (in-stream approval). La décision est ensuite obtenue
        via ``await_decision(request_id)``.
        """
        if isinstance(category, str):
            category = ApprovalCategory(category)

        request = ApprovalRequest(
            category=category,
            title=title,
            description=description,
            details=details or {},
            source=source,
            source_id=source_id,
            timeout_seconds=timeout_seconds,
            correlation_id=correlation_id,
        )

        loop = asyncio.get_running_loop()
        future: asyncio.Future[ApprovalResponse] = loop.create_future()

        async with self._lock:
            self._pending[request.id] = future
            self._requests[request.id] = request

        if self._human_root is not None:
            try:
                from core.human_root import TrustAction, TrustRisk
                risk = (
                    TrustRisk.CRITICAL
                    if str(category).lower() in ("command_exec", "system_modify")
                    else TrustRisk.HIGH
                )
                self._human_root._in_flight[request.id] = TrustAction(
                    action_id=request.id,
                    caller=source,
                    category=category.value if hasattr(category, "value") else str(category),
                    risk=risk,
                    summary=title or description,
                    details=details or {},
                    trace_id=correlation_id,
                )
            except Exception:
                pass

        try:
            self._publish_fn(request)
        except Exception as e:
            logger.error("ApprovalEngine: publish failed: %s", e)
            async with self._lock:
                self._pending.pop(request.id, None)
                self._requests.pop(request.id, None)
            raise

        if self._audit_log_fn is not None:
            try:
                self._audit_log_fn(
                    category="approval",
                    decision="pending",
                    action=f"approval.request:{category.value}",
                    actor=source,
                    details={
                        "request_id": request.id,
                        "title": title,
                        "description": description[:200],
                        "timeout": timeout_seconds,
                    },
                    correlation_id=correlation_id,
                )
            except Exception:
                pass

        return request

    def get_request(self, request_id: str) -> ApprovalRequest | None:
        """Retourne la requête enregistrée (ou None)."""
        return self._requests.get(request_id)

    async def await_decision(
        self,
        request_id: str,
        timeout_seconds: int = 300,
    ) -> ApprovalResponse:
        """Attend la décision pour une requête déjà créée."""
        future = self._pending.get(request_id)
        request = self._requests.get(request_id)
        if future is None or request is None:
            return ApprovalResponse(
                request_id=request_id,
                status=ApprovalStatus.CANCELLED,
                reason="Unknown request",
            )

        title = request.title
        category = request.category
        try:
            response = await asyncio.wait_for(
                asyncio.shield(future),
                timeout=timeout_seconds,
            )
            return response
        except TimeoutError:
            async with self._lock:
                self._pending.pop(request_id, None)
                self._requests.pop(request_id, None)

            logger.warning("Approval TIMEOUT: %s (%ss) — %s", request_id, timeout_seconds, title)

            if self._audit_log_fn is not None:
                try:
                    self._audit_log_fn(
                        category="approval",
                        decision="timeout",
                        action=f"approval.timeout:{category.value}",
                        actor="system",
                        details={"request_id": request_id, "title": title, "timeout": timeout_seconds},
                        correlation_id=request.correlation_id,
                    )
                except Exception:
                    pass

            return ApprovalResponse(
                request_id=request_id,
                status=ApprovalStatus.TIMEOUT,
                reason=f"Timeout after {timeout_seconds}s",
            )

    async def request(
        self,
        category: ApprovalCategory | str,
        title: str = "",
        description: str = "",
        details: dict[str, Any] | None = None,
        source: str = "system",
        source_id: str = "",
        timeout_seconds: int = 300,
        correlation_id: str = "",
    ) -> ApprovalResponse:
        """Crée une requête d'approbation et attend la réponse (compat)."""
        try:
            req = await self.create_request(
                category=category,
                title=title,
                description=description,
                details=details,
                source=source,
                source_id=source_id,
                timeout_seconds=timeout_seconds,
                correlation_id=correlation_id,
            )
        except Exception as e:
            return ApprovalResponse(
                request_id="",
                status=ApprovalStatus.CANCELLED,
                reason=f"Create failed: {e}",
            )
        return await self.await_decision(req.id, timeout_seconds=timeout_seconds)

    # ── Résolution de requête ───────────────────────────────────────

    def resolve(
        self,
        request_id: str,
        approved: bool,
        reason: str = "",
        responder: str = "human",
        authority=None,
    ) -> bool:
        """Resolve a pending approval request.

        If a trusted authority is supplied, it becomes authoritative. Otherwise,
        the legacy responder string is accepted for compatibility, while still
        rejecting obvious self-approval.
        """
        future = self._pending.get(request_id)
        request = self._requests.get(request_id)
        if future is None or future.done() or request is None:
            return False

        if authority is None:
            return False
        if not getattr(authority, "is_human_authority", False):
            return False
        permissions = set(getattr(authority, "permissions", ()) or ())
        if "ADMIN" not in permissions:
            return False
        if getattr(authority, "human", False) is False and getattr(authority, "principal_type", "").upper() != "HUMAN":
            return False
        responder = getattr(authority, "principal_id", responder)
        if request.source_id and responder == request.source_id:
            return False

        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        response = ApprovalResponse(
            request_id=request_id,
            status=status,
            reason=reason,
            responder=responder,
        )

        future.set_result(response)

        if self._human_root is not None:
            try:
                if request_id in self._human_root._in_flight:
                    self._human_root.resolve(
                        action_id=request_id,
                        approved=approved,
                        reason=reason,
                        responder=responder,
                    )
            except Exception:
                pass

        # Nettoyage
        self._pending.pop(request_id, None)
        self._requests.pop(request_id, None)

        logger.info(
            "Approval RESOLVED: %s → %s (by %s)",
            request_id,
            status.value,
            responder,
        )

        # Logger l'audit
        if self._audit_log_fn is not None:
            try:
                self._audit_log_fn(
                    category="approval",
                    decision=status.value,
                    action=f"approval.resolve:{status.value}",
                    actor=responder,
                    details={
                        "request_id": request_id,
                        "reason": reason[:200],
                    },
                )
            except Exception:
                pass

        return True

    def resolve_by_request(
        self,
        request: ApprovalRequest,
        approved: bool,
        reason: str = "",
        responder: str = "human",
    ) -> bool:
        """Résout une requête d'approbation à partir de l'objet Request."""
        return self.resolve(request.id, approved, reason, responder)

    # ── Annulation ──────────────────────────────────────────────────

    def cancel(self, request_id: str, reason: str = "") -> bool:
        """Annule une requête d'approbation en attente."""
        future = self._pending.get(request_id)
        if future is None or future.done():
            return False

        response = ApprovalResponse(
            request_id=request_id,
            status=ApprovalStatus.CANCELLED,
            reason=reason or "Cancelled by system",
        )
        future.set_result(response)
        self._pending.pop(request_id, None)
        self._requests.pop(request_id, None)
        logger.info("Approval CANCELLED: %s — %s", request_id, reason)
        return True

    def cancel_all(self, reason: str = "System shutdown") -> int:
        """Annule toutes les requêtes en attente."""
        count = 0
        for request_id in list(self._pending.keys()):
            if self.cancel(request_id, reason):
                count += 1
        logger.info("ApprovalEngine: %d pending requests cancelled", count)
        return count

    def cancel_by_correlation(self, correlation_id: str, reason: str = "") -> bool:
        """Cancel one pending request belonging to an operation correlation id."""
        for request_id, request in list(self._requests.items()):
            if request.correlation_id == correlation_id:
                return self.cancel(request_id, reason)
        return False

    # ── Requêtes ────────────────────────────────────────────────────

    def list_pending(self) -> list[dict[str, Any]]:
        """Liste les requêtes en attente (sans la Future)."""
        return [
            {**request.to_dict(), "status": "pending"}
            for request_id, request in self._requests.items()
            if request_id in self._pending
        ]

    @property
    def pending_count(self) -> int:
        """Nombre de requêtes en attente."""
        return len(self._pending)
