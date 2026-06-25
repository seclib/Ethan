"""Logging Middleware — Log des événements."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Coroutine

from core.types.event import Event

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Middleware de logging d'événements."""

    def __init__(self, log_level: int = logging.DEBUG):
        self._log_level = log_level

    async def process(self, event: Event, next_handler: Callable[[Event], Coroutine[Any, Any, None]]) -> None:
        """Traite un événement.

        Args:
            event: Événement
            next_handler: Handler suivant
        """
        start = time.time()

        logger.log(
            self._log_level,
            f"Event received: {event.type.value} (id: {event.id}, source: {event.source})",
        )

        try:
            await next_handler(event)
            duration = (time.time() - start) * 1000
            logger.debug(f"Event processed: {event.type.value} in {duration:.2f}ms")
        except Exception as e:
            logger.error(f"Event processing failed: {event.type.value} - {e}", exc_info=True)
            raise