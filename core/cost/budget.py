"""BudgetGuard — Contrôle budgétaire multi-scope.

Inspiré du BudgetGuard de Jarvis-OS, adapté pour l'architecture Ethan :
- Scopes : global (mensuel), project (par projet), run (par exécution)
- Alertes warn à ratio configurable
- Hard-stop quand le budget est épuisé
- Seed depuis l'historique PostgreSQL/JSONL
- Publication d'alertes sur l'EventBus
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from typing import Any

from core.cost.tracker import CostTracker
from core.cost.types import BudgetAlert, BudgetConfig, BudgetScope, BudgetStatus

logger = logging.getLogger(__name__)


def _default_publish(alert: BudgetAlert) -> None:
    """Publish par défaut : log uniquement."""
    logger.info("BudgetAlert: [%s] %s (%.2f/%.2f $)",
                alert.status.value, alert.message, alert.spent_usd, alert.limit_usd)


class BudgetGuard:
    """Garde-fou budgétaire multi-scope.

    Vérifie les dépenses avant exécution et émet des alertes.
    Utilise un asyncio.Lock pour la thread-safety.
    """

    def __init__(
        self,
        tracker: CostTracker,
        config: BudgetConfig | None = None,
        publish_fn: Any = None,
    ) -> None:
        self._tracker = tracker
        self._config = config or BudgetConfig()
        self._publish_fn = publish_fn or _default_publish
        self._lock = asyncio.Lock()

        # Accumulateurs in-memory pour projets et runs
        self._project_spent: dict[str, float] = {}
        self._run_spent: dict[str, float] = {}

        # Scopes ayant déjà déclenché une alerte warn
        self._warned: set[str] = set()

        logger.info(
            "BudgetGuard: enabled=%s, monthly=%.2f$, project=%.2f$, run=%.2f$",
            self._config.enabled,
            self._config.monthly_limit_usd,
            self._config.project_limit_usd,
            self._config.run_limit_usd,
        )

    # ── API publique ────────────────────────────────────────────────

    async def reserve(
        self,
        estimated_usd: float,
        scope: BudgetScope = BudgetScope.GLOBAL,
        scope_id: str = "",
    ) -> bool:
        """Vérifie si on peut dépenser estimated_usd.

        Retourne False (hard-stop) si le budget est épuisé.
        """
        if not self._config.enabled:
            return True

        async with self._lock:
            return self._check_and_warn(estimated_usd, scope, scope_id)

    def reserve_sync(
        self,
        estimated_usd: float,
        scope: BudgetScope = BudgetScope.GLOBAL,
        scope_id: str = "",
    ) -> bool:
        """Version synchrone de reserve() pour les appels non-async."""
        if not self._config.enabled:
            return True
        return self._check_and_warn(estimated_usd, scope, scope_id)

    def _check_and_warn(
        self,
        estimated_usd: float,
        scope: BudgetScope,
        scope_id: str,
    ) -> bool:
        """Vérifie le budget et émet des alertes si nécessaire."""
        spent = self._get_spent(scope, scope_id)
        limit = self._get_limit(scope)
        projected = spent + estimated_usd

        if limit == float("inf") or limit <= 0:
            return True

        # Hard-stop
        if projected > limit:
            self._emit_alert(
                scope=scope,
                scope_id=scope_id,
                status=BudgetStatus.HARD_STOP,
                spent=spent,
                limit=limit,
                message=f"Budget {scope.value} dépassé: {projected:.4f} > {limit:.4f}$",
            )
            logger.warning(
                "BudgetGuard HARD_STOP: %s/%s %.4f > %.4f$",
                scope.value, scope_id, projected, limit,
            )
            return False

        # Warn (une seule fois par scope)
        scope_key = f"{scope.value}:{scope_id}" if scope_id else scope.value
        ratio = projected / limit
        if ratio >= self._config.warn_ratio and scope_key not in self._warned:
            self._warned.add(scope_key)
            if self._config.alert_on_warning:
                self._emit_alert(
                    scope=scope,
                    scope_id=scope_id,
                    status=BudgetStatus.WARNING,
                    spent=spent,
                    limit=limit,
                    message=(
                        f"Budget {scope.value} à "
                        f"{ratio:.0%}: {projected:.4f} / {limit:.4f}$"
                    ),
                )
                logger.info(
                    "BudgetGuard WARNING: %s/%s %.0f%%",
                    scope.value, scope_id, ratio * 100,
                )

        return True

    def record(
        self,
        actual_usd: float,
        scope: BudgetScope = BudgetScope.GLOBAL,
        scope_id: str = "",
    ) -> None:
        """Enregistre une dépense réelle."""
        if not self._config.enabled or actual_usd <= 0:
            return

        if scope == BudgetScope.PROJECT:
            pid = scope_id or "_default"
            self._project_spent[pid] = self._project_spent.get(pid, 0.0) + actual_usd
        elif scope == BudgetScope.RUN:
            rid = scope_id or "_default"
            self._run_spent[rid] = self._run_spent.get(rid, 0.0) + actual_usd

    def remaining(
        self,
        scope: BudgetScope = BudgetScope.GLOBAL,
        scope_id: str = "",
    ) -> float:
        """Budget restant pour ce scope."""
        limit = self._get_limit(scope)
        if limit == float("inf"):
            return float("inf")
        return max(0.0, limit - self._get_spent(scope, scope_id))

    def status(self) -> dict[str, Any]:
        """Résumé complet de l'état budgétaire."""
        monthly = self._tracker.get_monthly_totals()
        global_spent = monthly.get("cost_usd", 0.0)
        global_limit = self._config.monthly_limit_usd

        projects = {
            pid: {
                "spent_usd": round(spent, 6),
                "limit_usd": self._config.project_limit_usd,
                "remaining_usd": round(
                    max(0.0, self._config.project_limit_usd - spent), 6
                ),
            }
            for pid, spent in self._project_spent.items()
        }

        return {
            "enabled": self._config.enabled,
            "global": {
                "spent_usd": round(global_spent, 6),
                "limit_usd": global_limit,
                "remaining_usd": round(max(0.0, global_limit - global_spent), 6),
                "utilization_pct": round(
                    global_spent / global_limit * 100, 2
                ) if global_limit > 0 else 0.0,
                "status": self._get_status(global_spent, global_limit).value,
            },
            "projects": projects,
            "warned_scopes": list(self._warned),
        }

    # ── Interne ─────────────────────────────────────────────────────

    def _get_spent(self, scope: BudgetScope, scope_id: str) -> float:
        if scope == BudgetScope.GLOBAL:
            monthly = self._tracker.get_monthly_totals()
            return monthly.get("cost_usd", 0.0)
        if scope == BudgetScope.PROJECT:
            return self._project_spent.get(scope_id or "_default", 0.0)
        if scope == BudgetScope.RUN:
            return self._run_spent.get(scope_id or "_default", 0.0)
        return 0.0

    def _get_limit(self, scope: BudgetScope) -> float:
        if scope == BudgetScope.GLOBAL:
            return self._config.monthly_limit_usd
        if scope == BudgetScope.PROJECT:
            return self._config.project_limit_usd
        if scope == BudgetScope.RUN:
            return self._config.run_limit_usd
        return float("inf")

    def _get_status(self, spent: float, limit: float) -> BudgetStatus:
        if limit == float("inf") or limit <= 0:
            return BudgetStatus.UNLIMITED
        if spent >= limit:
            return BudgetStatus.HARD_STOP
        if spent >= limit * self._config.warn_ratio:
            return BudgetStatus.WARNING
        return BudgetStatus.OK

    def _emit_alert(
        self,
        scope: BudgetScope,
        scope_id: str,
        status: BudgetStatus,
        spent: float,
        limit: float,
        message: str,
    ) -> None:
        alert = BudgetAlert(
            scope=scope,
            scope_id=scope_id,
            status=status,
            ratio=spent / limit if limit > 0 else 0.0,
            spent_usd=spent,
            limit_usd=limit,
            message=message,
        )
        try:
            self._publish_fn(alert)
        except Exception as e:
            logger.warning("BudgetGuard: publish failed: %s", e)

    def reset_monthly(self) -> None:
        """Réinitialise les alertes warn pour le nouveau mois."""
        self._warned.clear()
        logger.info("BudgetGuard: monthly alerts reset")