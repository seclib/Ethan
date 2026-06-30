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
        self._lock = asyncio.Lock()

    # ── Création de requête ─────────────────────────────────────────

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
        """Crée une requête d'approbation et attend la réponse.

        Retourne la réponse (APPROVED, REJECTED ou TIMEOUT).
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

        # Créer la Future avant publication pour éviter race condition
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ApprovalResponse] = loop.create_future()

        async with self._lock:
            self._pending[request.id] = future

        # Publier la requête
        try:
            self._publish_fn(request)
        except Exception as e:
            logger.error("ApprovalEngine: publish failed: %s", e)
            async with self._lock:
                self._pending.pop(request.id, None)
            return ApprovalResponse(
                request_id=request.id,
                status=ApprovalStatus.CANCELLED,
                reason=f"Publish failed: {e}",
            )

        # Logger l'audit
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

        # Attendre la réponse avec timeout
        try:
            response = await asyncio.wait_for(
                asyncio.shield(future),
                timeout=timeout_seconds,
            )
            return response
        except TimeoutError:
            async with self._lock:
                self._pending.pop(request.id, None)

            logger.warning(
                "Approval TIMEOUT: %s (%ss) — %s",
                request.id, timeout_seconds, title,
            )

            if self._audit_log_fn is not None:
                try:
                    self._audit_log_fn(
                        category="approval",
                        decision="timeout",
                        action=f"approval.timeout:{category.value}",
                        actor="system",
                        details={
                            "request_id": request.id,
                            "title": title,
                            "timeout": timeout_seconds,
                        },
                        correlation_id=correlation_id,
                    )
                except Exception:
                    pass

            return ApprovalResponse(
                request_id=request.id,
                status=ApprovalStatus.TIMEOUT,
                reason=f"Timeout after {timeout_seconds}s",
            )

    # ── Résolution de requête ───────────────────────────────────────

    def resolve(
        self,
        request_id: str,
        approved: bool,
        reason: str = "",
        responder: str = "human",
    ) -> bool:
        """Résout une requête d'approbation en attente.

        Retourne True si la requête a été résolue, False si elle n'existe pas.
        """
        future = self._pending.get(request_id)
        if future is None or future.done():
            return False

        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        response = ApprovalResponse(
            request_id=request_id,
            status=status,
            reason=reason,
            responder=responder,
        )

        future.set_result(response)

        # Nettoyage
        self._pending.pop(request_id, None)

        logger.info(
            "Approval RESOLVED: %s → %s (by %s)",
            request_id, status.value, responder,
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

    # ── Requêtes ────────────────────────────────────────────────────

    def list_pending(self) -> list[dict[str, Any]]:
        """Liste les requêtes en attente (sans la Future)."""
        # On ne peut pas récupérer le détail depuis la Future,
        # donc on retourne juste les IDs
        return [
            {"request_id": rid, "status": "pending"}
            for rid in self._pending.keys()
        ]

    @property
    def pending_count(self) -> int:
        """Nombre de requêtes en attente."""
        return len(self._pending)