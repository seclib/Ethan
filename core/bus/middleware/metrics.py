"""Metrics Middleware — Collecte de métriques."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Coroutine

from core.types.event import Event

logger = logging.getLogger(__name__)


class MetricsMiddleware:
    """Middleware de collecte de métriques."""

    def __init__(self, metrics_collector: Any | None = None):
        self._metrics = metrics_collector

    async def process(self, event: Event, next_handler: Callable[[Event], Coroutine[Any, Any, None]]) -> None:
        """Traite un événement.

        Args:
            event: Événement
            next_handler: Handler suivant
        """
        if not self._metrics:
            await next_handler(event)
            return

        start = time.time()

        try:
            await next_handler(event)
            duration = (time.time() - start) * 1000

            # Métriques de succès
            self._metrics.increment("eventbus.consumed", tags={
                "type": event.type.value,
                "success": "true",
            })
            self._metrics.histogram("eventbus.consume.latency", duration)

        except Exception as e:
            duration = (time.time() - start) * 1000

            # Métriques d'erreur
            self._metrics.increment("eventbus.consumed", tags={
                "type": event.type.value,
                "success": "false",
            })
            self._metrics.increment("eventbus.errors", tags={
                "type": event.type.value,
            })
            self._metrics.histogram("eventbus.consume.latency", duration)

            raise