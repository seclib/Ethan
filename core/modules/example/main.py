"""Example cognitive module — subscribes to NATS, logs, and echoes."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import nats
from nats.aio.msg import Msg

from sdk.event import Event, EventType
from sdk.module import CognitiveModule, ModuleContext, ModuleManifest
from kernel.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


class ExampleModule(CognitiveModule):
    """Example module that logs incoming events and echoes a response."""

    def __init__(self):
        self.nc: Optional[nats.NATS] = None
        self.module_id = "example-v1"

    def get_manifest(self) -> ModuleManifest:
        return ModuleManifest(
            module_id=self.module_id,
            name="Example Module",
            version="1.0.0",
            capabilities=["module.reasoning", "module.example"],
            topics_subscribed=["ethan.module.reasoning", "ethan.module.example"],
            topics_published=["ethan.module.reasoning.done", "ethan.module.example.done"],
        )

    async def initialize(self, context: ModuleContext) -> None:
        """Connect to NATS."""
        self.module_id = context.module_id
        logger.info(f"ExampleModule initializing: {self.module_id}")

        self.nc = await nats.connect(
            context.nats_url,
            name=self.module_id,
        )

        # Subscribe to module topics
        async def on_message(msg: Msg):
            try:
                data = json.loads(msg.data.decode())
                event = Event.from_dict(data)
                response = await self.handle_event(event)
                if response and msg.reply:
                    await self.nc.publish(msg.reply, json.dumps(response.dict()).encode())
            except Exception as e:
                logger.error(f"ExampleModule handler error: {e}")

        for topic in self.get_manifest().topics_subscribed:
            await self.nc.subscribe(topic, cb=on_message)
            logger.info(f"ExampleModule subscribed to {topic}")

        # Register in PostgreSQL (via outbox for simplicity)
        logger.info(f"ExampleModule initialized: {self.module_id}")

    async def handle_event(self, event: Event) -> Optional[Event]:
        """Log the event and return a mock response."""
        logger.info(f"ExampleModule received: {event.type} from {event.source}")
        logger.info(f"  data: {event.data}")

        # Mock processing — simulate a cognitive step
        await asyncio.sleep(0.1)

        return Event(
            type=event.type.replace("module.", "module.").replace("reasoning", "reasoning") + ".done",
            source=self.module_id,
            data={
                "processed": True,
                "input": event.data,
                "result": {"status": "completed", "output": "Mock processing complete"},
            },
            metadata={"trace_id": event.metadata.get("trace_id", "")},
        )

    async def shutdown(self) -> None:
        """Close NATS connection."""
        if self.nc:
            await self.nc.drain()
            logger.info("ExampleModule shut down")


async def main():
    """Entry point for the example module service."""
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    module_id = os.getenv("MODULE_ID", "example-v1")

    module = ExampleModule()
    context = ModuleContext(module_id=module_id, nats_url=nats_url)
    await module.initialize(context)

    # Keep running
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await module.shutdown()


if __name__ == "__main__":
    asyncio.run(main())