"""Enrichment Middleware — Enrichit les événements."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Coroutine
from uuid import uuid4

from core.types.event import Event

logger = logging.getLogger(__name__)


class EnrichmentMiddleware:
    """Middleware d'enrichissement d'événements."""

    def __init__(self):
        self._enrichers: list[Callable[[Event], None]] = []

    def add_enricher(self, enricher: Callable[[Event], None]) -> None:
        """Ajoute un enrichisseur.

        Args:
            enricher: Fonction d'enrichissement
        """
        self._enrichers.append(enricher)

    async def process(self, event: Event, next_handler: Callable[[Event], Coroutine[Any, Any, None]]) -> None:
        """Traite un événement.

        Args:
            event: Événement
            next_handler: Handler suivant
        """
        # Enrichir
        for enricher in self._enrichers:
            try:
                enricher(event)
            except Exception as e:
                logger.error(f"Enricher error: {e}", exc_info=True)

        # Continuer
        await next_handler(event)


# Enrichisseurs standards

def add_correlation_id(event: Event) -> None:
    """Ajoute un correlation_id si absent."""
    if not event.correlation_id:
        event.correlation_id = str(uuid4())


def add_timestamps(event: Event) -> None:
    """Ajoute des timestamps."""
    if not event.metadata:
        event.metadata = {}
    
    if "published_at" not in event.metadata:
        event.metadata["published_at"] = datetime.utcnow().isoformat()


def add_trace_ids(event: Event) -> None:
    """Ajoute des IDs de tracing."""
    if not event.metadata:
        event.metadata = {}
    
    if "span_id" not in event.metadata:
        event.metadata["span_id"] = str(uuid4())
    
    if "parent_span_id" not in event.metadata:
        event.metadata["parent_span_id"] = event.metadata.get("span_id")