"""Rate Limiter — Limite le taux d'actions."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from core.security.types import Action, SecurityContext, ValidationResult

logger = logging.getLogger(__name__)


class RateLimiter:
    """Limite le taux d'actions par acteur."""

    def __init__(self, max_actions: int = 100, window_seconds: int = 60):
        self._max_actions = max_actions
        self._window = window_seconds
        self._counts: dict[str, list[float]] = defaultdict(list)

    async def validate(self, action: Action, context: SecurityContext) -> ValidationResult:
        """Vérifie les limites de taux.

        Args:
            action: Action à valider
            context: Contexte de sécurité

        Returns:
            Résultat de validation
        """
        actor_id = context.identity.id
        now = time.time()

        # Nettoyer les entrées expirées
        self._counts[actor_id] = [
            t for t in self._counts[actor_id] if now - t < self._window
        ]

        # Vérifier la limite
        if len(self._counts[actor_id]) >= self._max_actions:
            return ValidationResult(
                valid=False,
                reason=f"Rate limit exceeded: {self._max_actions} per {self._window}s",
                violations=["rate_limit_exceeded"],
            )

        # Enregistrer l'action
        self._counts[actor_id].append(now)

        return ValidationResult(valid=True, validators_passed=["rate_limiter"])