"""ETHAN Event Bus — NATS Implementation

Uses the canonical Event from core.ethan_types.event for consistency.
"""

from __future__ import annotations

import json
import inspect
import logging
import asyncio
import os
from typing import Any, Dict, Optional
from uuid import uuid4

from core.bus.interface import EventBus as EventBusContract
from core.bus.interface import EventHandler, Subscription
from core.ethan_types.event import Event

try:
    import nats
    from nats.aio.client import Client as NATSClient
    from nats.aio.msg import Msg
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

logger = logging.getLogger(__name__)


class EventBus(EventBusContract):
    """Event Bus — NATS-based communication

    Implements core.bus.interface.EventBus contract.
    """

    def __init__(self, servers: str = "nats://nats:4222"):
        self.servers = servers
        self._client: Optional[NATSClient] = None
        self._subscriptions: Dict[str, list[Any]] = {}

    async def connect(self, servers: Optional[str] = None) -> None:
        """Connect to NATS server.

        Args:
            servers: Optional URL override. If not provided, uses the URL
                     passed to __init__. This signature is compatible with
                     both the abstract EventBus.connect(servers) and the
                     common pattern of calling bus.connect() without args.
        """
        if not NATS_AVAILABLE:
            raise RuntimeError("NATS library not available. Install with: pip install nats-py")

        if self._client is not None:
            return

        url = servers or self.servers
        timeout = float(os.getenv("NATS_CONNECT_TIMEOUT", "10"))
        self._client = await asyncio.wait_for(nats.connect(url), timeout=timeout)
        logger.info("NATS EventBus connected to %s", url)

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self._client:
            await self._client.close()
            self._client = None
            self._subscriptions = {}
            logger.info("NATS EventBus disconnected")

    async def close(self) -> None:
        """Alias for disconnect — matches EventBus interface."""
        await self.disconnect()

    async def publish(self, subject: str, event: Event) -> None:
        """Publish an event to a subject."""
        if self._client is None:
            raise RuntimeError("Not connected to NATS")

        await self._client.publish(subject, event.to_json())

    async def subscribe(
        self,
        subject: str,
        callback: EventHandler,
        queue: Optional[str] = None,
    ) -> Subscription:
        """Subscribe to a subject and return a contract-compliant handle."""
        if self._client is None:
            raise RuntimeError("Not connected to NATS")

        async def handler(msg: Msg) -> None:
            event = Event.from_json(msg.data)
            result = callback(event)
            if inspect.isawaitable(result):
                await result

        sub = await self._client.subscribe(subject, cb=handler, queue=queue)
        self._subscriptions.setdefault(subject, []).append(sub)
        subscription_id = str(uuid4())

        async def unsubscribe_from_nats() -> None:
            # Keep the public handle and the raw NATS subscription in sync.
            subscriptions = self._subscriptions.get(subject, [])
            if sub in subscriptions:
                await sub.unsubscribe()
                subscriptions.remove(sub)
                if not subscriptions:
                    self._subscriptions.pop(subject, None)

        return Subscription(
            id=subscription_id,
            pattern=subject,
            handler=callback,
            bus=self,
            unsubscribe_callback=unsubscribe_from_nats,
        )

    async def request(self, subject: str, event: Event, timeout: float = 30.0) -> Optional[Event]:
        """Request-reply pattern."""
        if self._client is None:
            raise RuntimeError("Not connected to NATS")

        msg = await self._client.request(subject, event.to_json(), timeout=timeout)
        if msg:
            return Event.from_json(msg.data)
        return None

    async def unsubscribe(self, subject: str) -> None:
        """Unsubscribe from a subject."""
        for subscription in list(self._subscriptions.get(subject, [])):
            await subscription.unsubscribe()
        self._subscriptions.pop(subject, None)

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()
