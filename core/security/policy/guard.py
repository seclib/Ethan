"""Policy Guard — Point d'entrée obligatoire pour les actions sensibles.

Garantit qu'aucune action à effet de bord ne peut être exécutée sans passer
par l'évaluation du Policy Engine. Le garde **ne déléguera jamais** l'appel
de la fonction d'exécution si la décision n'est pas ALLOW ou confirmée :
appeler directement un outil court-circuite le moteur et est donc interdit
par construction — toute fonction sensible doit être appelée *via* ce garde.

Modes de confirmation :
- si ``approver`` est fourni, REQUIRE_CONFIRMATION est résolu par l'approver
  (True → ALLOW, False/None → DENY) ;
- sans approver, REQUIRE_CONFIRMATION est un refus (fail-closed, CR-7).
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from core.security.policy.engine import PolicyEngine
from core.security.policy.types import (
    PolicyConfirmationRequiredError,
    PolicyDecision,
    PolicyDeniedError,
    PolicyRequest,
    PolicyResult,
)

logger = logging.getLogger(__name__)


class PolicyGuard:
    """Garde d'exécution des actions sensibles (non contournable)."""

    def __init__(
        self,
        engine: PolicyEngine | None = None,
        approver: (
            Callable[[PolicyRequest, PolicyDecision], Awaitable[bool]] | None
        ) = None,
    ) -> None:
        self._engine = engine or PolicyEngine()
        self._approver = approver

    @property
    def engine(self) -> PolicyEngine:
        """Le moteur sous-jacent (pour inspection / audit)."""
        return self._engine

    # ── Évaluation seule (aucune exécution) ────────────────────────────

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """Évalue sans exécuter. Utilisable pour pré-auditer ou afficher."""
        return self._engine.evaluate(request)

    def check(
        self,
        category: str,
        action: str,
        resource: str,
        params: dict | None = None,
        source: str = "unknown",
    ) -> PolicyDecision:
        """Évalue une action (sans exécution)."""
        return self._engine.check(
            category, action, resource, params=params, source=source
        )

    # ── Exécution protégée ─────────────────────────────────────────────

    async def execute(
        self,
        category: str,
        action: str,
        resource: str,
        fn: Callable[..., Any] | Callable[..., Awaitable[Any]],
        params: dict | None = None,
        *,
        source: str = "unknown",
    ) -> Any:
        """Évalue puis exécute ``fn`` uniquement si autorisé.

        Args:
            category: Catégorie d'action (filesystem, shell, …).
            action: Action précise (read, write, delete, …).
            resource: Ressource ciblée.
            fn: Fonction d'exécution réelle (ne sera JAMAIS appelée si la
                décision n'est pas ALLOW ou confirmée).
            params: Paramètres à passer à ``fn`` (kwargs).
            source: Origine déclarative (informationnelle — A6).

        Returns:
            Le résultat de ``fn(**params)``.

        Raises:
            PolicyDeniedError: si la décision est DENY (ou non confirmée sans
                approver). Le callback n'est jamais invoqué.
        """
        request = PolicyRequest(
            category=category,
            action=action,
            resource=resource,
            params=params or {},
            source=source,
        )
        decision = self._engine.evaluate(request)

        if decision.result is PolicyResult.DENY:
            raise PolicyDeniedError(decision)

        if decision.result is PolicyResult.REQUIRE_CONFIRMATION:
            approved = await self._confirm(request, decision)
            if not approved:
                raise PolicyConfirmationRequiredError(decision)

        # Décision ALLOW (ou confirmation obtenue) : exécution.
        call_kwargs = dict(params or {})
        return await self._call(fn, call_kwargs)

    # ── Helpers ────────────────────────────────────────────────────────

    async def _confirm(
        self,
        request: PolicyRequest,
        decision: PolicyDecision,
    ) -> bool:
        """Résout une confirmation humaine.

        Sans approver → refus (fail-closed, CR-7). Avec approver, la
        décision de l'humain fait foi (PR-1) — mais l'approver ne peut
        jamais autoriser une action DENY (déjà rejetée en amont).
        """
        if self._approver is None:
            logger.warning(
                "PolicyGuard: confirmation requise sans approver -> refus (%s)",
                decision.policy_id,
            )
            return False
        try:
            return await self._approver(request, decision)
        except Exception as exc:  # fail-closed : toute erreur = refus
            logger.error("PolicyGuard: approver failed (%s) -> refus", exc)
            return False

    @staticmethod
    async def _call(
        fn: Callable[..., Any] | Callable[..., Awaitable[Any]],
        kwargs: dict[str, Any],
    ) -> Any:
        """Appelle la fonction, qu'elle soit sync ou async."""
        if inspect.iscoroutinefunction(fn):
            return await fn(**kwargs)
        result = fn(**kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
