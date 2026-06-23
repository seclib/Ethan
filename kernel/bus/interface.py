"""Event Bus interface — Abstract base for NATS implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional

from sdk.event import Event


class Subscription:
    """Represents a NATS subscription."""

    def __init__(self, topic: str, sid: int):
        self.topic = topic
        self.sid = sid


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus(ABC):
    """Abstract event bus. Implementations wrap NATS JetStream."""

    @abstractmethod
    async def connect(self, servers: str = "nats://localhost:4222") -> None:
        """Connect to NATS cluster."""
        ...

    @abstractmethod
    async def publish(self, topic: str, event: Event) -> None:
        """Publish an event to a topic."""
        ...

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
        queue: Optional[str] = None,
    ) -> Subscription:
        """Subscribe to a topic with optional queue group."""
        ...

    @abstractmethod
    async def request(
        self,
        topic: str,
        event: Event,
        timeout: float = 30.0,
    ) -> Optional[Event]:
        """Publish and wait for a reply (request-reply pattern)."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close connection."""
        ...