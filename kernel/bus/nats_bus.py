"""NATS Event Bus implementation."""

from __future__ import annotations

import json
import logging
from typing import Optional

import nats
from nats.aio.client import Msg
from nats.aio.msg import Msg as NatsMsg
from nats.js import JetStreamContext

from sdk.event import Event
from kernel.bus.interface import EventBus, EventHandler, Subscription

logger = logging.getLogger(__name__)


class NatsEventBus(EventBus):
    """Event bus implementation using NATS with JetStream."""

    def __init__(self):
        self._conn: Optional[nats.NATS] = None
        self._js: Optional[JetStreamContext] = None
        self._subs: list[Subscription] = []

    async def connect(self, servers: str = "nats://localhost:4222") -> None:
        """Connect to NATS and enable JetStream."""
        logger.info(f"Connecting to NATS: {servers}")
        self._conn = await nats.connect(servers, name="ethan-kernel")
        self._js = self._conn.jetstream()
        logger.info("NATS connected, JetStream enabled")

    async def publish(self, topic: str, event: Event) -> None:
        """Publish event to NATS topic as JSON."""
        payload = json.dumps(event.dict()).encode()
        if self._js:
            await self._js.publish(topic, payload)
        else:
            await self._conn.publish(topic, payload)
        logger.debug(f"Published to {topic}: {event.type}")

    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
        queue: Optional[str] = None,
    ) -> Subscription:
        """Subscribe with optional queue group for load balancing."""
        if not self._conn:
            raise RuntimeError("NATS not connected")

        async def _on_message(msg: NatsMsg):
            try:
                data = json.loads(msg.data.decode())
                event = Event.from_dict(data)
                await handler(event)
            except Exception as exc:
                logger.error(f"Handler error on {topic}: {exc}")

        sub = await self._conn.subscribe(topic, cb=_on_message, queue=queue)
        self._subs.append(Subscription(topic, sub.sid))
        logger.info(f"Subscribed to {topic}" + (f" (queue={queue})" if queue else ""))
        return Subscription(topic, sub.sid)

    async def request(
        self,
        topic: str,
        event: Event,
        timeout: float = 30.0,
    ) -> Optional[Event]:
        """Publish and wait for a reply (request-reply pattern)."""
        payload = json.dumps(event.dict()).encode()
        try:
            msg = await self._conn.request(topic, payload, timeout=timeout)
            data = json.loads(msg.data.decode())
            return Event.from_dict(data)
        except nats.errors.TimeoutError:
            logger.warning(f"Request timeout on {topic} after {timeout}s")
            return None

    async def close(self) -> None:
        """Close NATS connection."""
        if self._conn:
            await self._conn.drain()
            logger.info("NATS connection closed")