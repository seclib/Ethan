"""Memory Module — Stores task events in Redis and PostgreSQL."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Optional
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import nats
import redis.asyncio as aioredis
from nats.aio.msg import Msg

from core.bus.nats_auth import nats_connect_options
from core.ethan_types.event import Event, EventType
from core.ethan_types.sdk.module import CognitiveModule, ModuleContext, ModuleManifest
from core.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


class MemoryModule(CognitiveModule):
    """Stores task events for later retrieval."""

    def __init__(self):
        self.nc: Optional[nats.NATS] = None
        self.redis: Optional[aioredis.Redis] = None
        self.module_id = "memory-v1"

    def get_manifest(self) -> ModuleManifest:
        return ModuleManifest(
            module_id=self.module_id,
            name="Memory Module",
            version="1.0.0",
            capabilities=["module.memory"],
            topics_subscribed=["ethan.task.created", "ethan.task.plan", "ethan.task.completed"],
            topics_published=["ethan.memory.stored"],
        )

    async def initialize(self, context: ModuleContext) -> None:
        self.module_id = context.module_id
        timeout = float(os.getenv("MODULE_CONNECT_TIMEOUT", "10"))
        self.nc = await asyncio.wait_for(
            nats.connect(context.nats_url, name=self.module_id, **nats_connect_options()),
            timeout=timeout,
        )

        redis_url = context.config.get("redis_url", "redis://localhost:6379/0")
        self.redis = aioredis.from_url(redis_url, protocol=2)

        async def on_msg(msg: Msg):
            try:
                data = json.loads(msg.data.decode())
                event = Event.from_dict(data)
                response = await self.handle_event(event)
                if response:
                    subject = (
                        msg.reply or response.type.value
                        if isinstance(response.type, EventType)
                        else msg.reply or str(response.type)
                    )
                    await self.nc.publish(subject, response.to_json())
            except Exception as e:
                logger.error(f"Memory handler error: {e}")

        for topic in self.get_manifest().topics_subscribed:
            await asyncio.wait_for(self.nc.subscribe(topic, cb=on_msg), timeout=timeout)
            logger.info(f"Memory subscribed to {topic}")

    async def handle_event(self, event: Event) -> Optional[Event]:
        logger.info(f"Memory storing: {event.type}")
        key = f"memory:{event.id}"
        payload = {
            "event_type": event.type,
            "source": event.source,
            "timestamp": event.timestamp,
            "data": event.data,
            "metadata": event.metadata,
        }

        # Store in Redis (7 days)
        await self.redis.set(key, json.dumps(payload), ex=604800)

        logger.info(f"Memory stored event {event.id} under {key}")

        return Event(
            type=EventType.MEMORY_STORED,
            source=self.module_id,
            data={"memory_key": key, "event_id": event.id},
            metadata={"trace_id": event.metadata.get("trace_id", "")},
        )

    async def shutdown(self) -> None:
        if self.nc:
            await self.nc.drain()
        if self.redis:
            await self.redis.close()
        logger.info("Memory shut down")


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    module = MemoryModule()
    ctx = ModuleContext(
        module_id=os.getenv("MODULE_ID", "memory-v1"),
        nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
        config={"redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0")},
    )
    await module.initialize(ctx)
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await module.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
