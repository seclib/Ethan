"""Event Publisher — Publication d'événements avec validation et enrichissement."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.bus.priorities import Priority
from core.types.event import Event

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publie des événements sur le bus.
    
    Responsabilités :
    - Validation des événements
    - Enrichissement (metadata, correlation_id)
    - Sérialisation
    - Publication avec retry
    """

    def __init__(self, bus: Any, validator: Any | None = None):
        self._bus = bus
        self._validator = validator
        self._max_retries = 3
        self._retry_delay = 0.1  # secondes

    async def publish(
        self,
        subject: str,
        event: Event,
        priority: Priority = Priority.NORMAL,
    ) -> None:
        """Publie un événement.

        Args:
            subject: Sujet (e.g., "ethan.module.executor.task.completed")
            event: Événement à publier
            priority: Niveau de priorité
        """
        # 1. Valider
        if self._validator and not self._validator.validate(event):
            raise ValueError(f"Invalid event: {event.id}")

        # 2. Enrichir
        self._enrich(event, priority)

        # 3. Publier avec retry
        for attempt in range(self._max_retries):
            try:
                await self._bus.publish(subject, event)
                logger.debug(f"Published {event.type} on {subject} (priority: {priority.name})")
                return
            except Exception as e:
                if attempt == self._max_retries - 1:
                    logger.error(f"Failed to publish event after {self._max_retries} attempts: {e}")
                    raise
                logger.warning(f"Publish attempt {attempt + 1} failed, retrying...")
                import asyncio
                await asyncio.sleep(self._retry_delay * (attempt + 1))

    def _enrich(self, event: Event, priority: Priority) -> None:
        """Enrichit l'événement avec des métadonnées.

        Args:
            event: Événement
            priority: Priorité
        """
        # Correlation ID (hériter ou générer)
        if not event.correlation_id:
            event.correlation_id = str(uuid4())

        # Span ID pour tracing
        if not event.metadata:
            event.metadata = {}
        
        if "span_id" not in event.metadata:
            event.metadata["span_id"] = str(uuid4())
        
        if "parent_span_id" not in event.metadata:
            event.metadata["parent_span_id"] = event.metadata.get("span_id")

        # Timestamps
        event.metadata["published_at"] = datetime.utcnow().isoformat()
        event.metadata["priority"] = priority.name

    async def publish_and_wait(
        self,
        subject: str,
        event: Event,
        response_subject: str,
        timeout: float = 30.0,
    ) -> Event | None:
        """Publie et attend une réponse (request/reply).

        Args:
            subject: Sujet de publication
            event: Événement
            response_subject: Sujet de réponse
            timeout: Timeout en secondes

        Returns:
            Événement de réponse ou None
        """
        self._enrich(event, Priority.HIGH)
        return await self._bus.request(response_subject, event, timeout=timeout)