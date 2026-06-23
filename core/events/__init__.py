"""Event System — ADR-1007

Architecture événementielle pour découplage et observabilité.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types d'événements du système."""

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"

    # Capability events
    CAPABILITY_STARTED = "capability.started"
    CAPABILITY_COMPLETED = "capability.completed"
    CAPABILITY_FAILED = "capability.failed"

    # Memory events
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"

    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_DESTROYED = "agent.destroyed"

    # User events
    USER_INPUT_RECEIVED = "user.input.received"
    USER_RESPONSE_GENERATED = "user.response.generated"

    # Security events
    SECURITY_AUDIT = "security.audit"


@dataclass
class Event:
    """Événement métier."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: EventType = EventType.SYSTEM_STARTUP
    source: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventHandler(ABC):
    """Interface abstraite pour les handlers d'événements."""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Traiter un événement."""
        pass


class EventBus:
    """Bus d'événements central pour communication asynchrone."""

    def __init__(self, record_history: bool = True):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._history: List[Event] = []
        self._record_history = record_history

    async def publish(self, event: Event) -> None:
        """Publier un événement à tous les subscribers."""
        if self._record_history:
            self._history.append(event)

        handlers = self._handlers.get(event.type, [])
        if not handlers:
            return

        logger.debug(f"Publishing event {event.type} to {len(handlers)} handlers")

        # Exécuter tous les handlers en parallèle
        tasks = [handler.handle(event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Souscrire un handler à un type d'événement."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type}")

    async def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Désouscrire un handler d'un type d'événement."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler unsubscribed from {event_type}")
            except ValueError:
                pass

    def get_history(self, event_type: EventType | None = None) -> List[Event]:
        """Récupérer l'historique des événements."""
        if event_type is None:
            return self._history.copy()
        return [e for e in self._history if e.type == event_type]

    def clear_history(self) -> None:
        """Vider l'historique des événements."""
        self._history.clear()


# Global event bus instance
bus = EventBus()