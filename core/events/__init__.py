"""Event System — ADR-1007 (Backward Compatible)

Ce module reste importable pour la rétrocompatibilité.
Il réexporte les nouveaux types depuis core/types et core/bus.

Les anciennes importations continuent de fonctionner :
    from core.events import Event, EventType, EventBus, EventHandler
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.bus.memory import InMemoryBus
from core.types.event import Event, EventType

logger = logging.getLogger(__name__)

# ─── Rétrocompatibilité : EventHandler (ABC) ──────────────────────

class EventHandler(ABC):
    """Interface abstraite pour les handlers d'événements.
    
    Rétrocompatible avec l'ancienne API.
    Utilisation recommandée : utiliser directement les callbacks du bus.
    """

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Traiter un événement."""
        pass


# ─── Rétrocompatibilité : EventBus (existant) ─────────────────────

class EventBus:
    """Bus d'événements central (ancienne API, rétrocompatible).

    Fonctionne comme un wrapper autour de InMemoryBus.
    Les nouvelles implémentations devraient utiliser directement
    core.bus.interface.EventBus.
    """

    def __init__(self, record_history: bool = True):
        self._inner = InMemoryBus(record_history=record_history)
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._record_history = record_history

    async def publish(self, event: Event) -> None:
        """Publie un événement à tous les subscribers."""
        # Anciens handlers enregistrés via subscribe()
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Handler error: {e}", exc_info=True)

        # Nouveaux handlers dans l'InMemoryBus
        await self._inner.publish(event.type.value, event)

    async def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Souscrit un handler à un type d'événement (ancienne API)."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type}")

    async def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Désouscrit un handler (ancienne API)."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler unsubscribed from {event_type}")
            except ValueError:
                pass

    def get_history(self, event_type: EventType | None = None) -> List[Event]:
        """Récupère l'historique des événements."""
        if event_type is None:
            return self._inner.get_history()
        return self._inner.get_history(event_type.value)

    def clear_history(self) -> None:
        """Vide l'historique des événements."""
        self._inner.clear_history()

    @property
    def inner_bus(self) -> InMemoryBus:
        """Accède au bus interne InMemoryBus."""
        return self._inner


# Instance globale (rétrocompatible)
bus = EventBus()

__all__ = [
    "Event",
    "EventType",
    "EventBus",
    "EventHandler",
    "bus",
]