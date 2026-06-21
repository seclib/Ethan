# Jarvis OS — Event System
# Système d'événements asynchrones pour la communication entre composants

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priorité des événements."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """Événement standardisé."""
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    id: str = ""


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Bus d'événements asynchrone.

    Permet la communication découplée entre composants via :
    - Publish/Subscribe
    - Filtrage par type d'événement
    - Priorités
    - Async handlers
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}
        self._wildcard_handlers: list[EventHandler] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler for event: {event_type}")

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events."""
        self._wildcard_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Unsubscribe from an event type."""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            return True
        return False

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        tasks = []

        # Notify type-specific handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                tasks.append(self._safe_call(handler, event))

        # Notify wildcard handlers
        for handler in self._wildcard_handlers:
            tasks.append(self._safe_call(handler, event))

        # Run all handlers concurrently
        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        """Call a handler safely, catching exceptions."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Event handler error for {event.type}: {e}")

    def clear(self) -> None:
        """Clear all handlers."""
        self._handlers.clear()
        self._wildcard_handlers.clear()


# Global event bus instance
bus = EventBus()