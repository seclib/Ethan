"""Validation Middleware — Valide les événements."""

from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine

from core.types.event import Event

logger = logging.getLogger(__name__)


class ValidationMiddleware:
    """Middleware de validation d'événements."""

    def __init__(self):
        self._validators: list[Callable[[Event], bool]] = []

    def add_validator(self, validator: Callable[[Event], bool]) -> None:
        """Ajoute un validateur.

        Args:
            validator: Fonction de validation
        """
        self._validators.append(validator)

    async def process(self, event: Event, next_handler: Callable[[Event], Coroutine[Any, Any, None]]) -> None:
        """Traite un événement.

        Args:
            event: Événement
            next_handler: Handler suivant
        """
        # Valider
        for validator in self._validators:
            if not validator(event):
                logger.warning(f"Event validation failed: {event.id}")
                return

        # Continuer
        await next_handler(event)