"""Reflective Module — Logs and summarizes completed tasks."""

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


class ReflectiveModule(CognitiveModule):
    """Receives completed tasks, logs and emits a reflection (stub)."""

    def __init__(self):
        self.nc: Optional[nats.NATS] = None
        self.module_id = "reflective-v1"

    def get_manifest(self) -> ModuleManifest:
        return ModuleManifest(
            module_id=self.module_id,
            name="Reflective Module",
            version="1.0.0",
            capabilities=["module.reflective"],
            topics_subscribed=["ethan.task.completed"],
            topics_published=["ethan.reflection.done"],
        )

    async def initialize(self, context: ModuleContext) -> None:
        self.module_id = context.module_id
        self.nc = await nats.connect(context.nats_url, name=self.module_id)

        async def on_msg(msg: Msg):
            try:
                data = json.loads(msg.data.decode())
                event = Event.from_dict(data)
                response = await self.handle_event(event)
                if response and msg.reply:
                    await self.nc.publish(msg.reply, json.dumps(response.dict()).encode())
            except Exception as e:
                logger.error(f"Reflective handler error: {e}")

        for topic in self.get_manifest().topics_subscribed:
            await self.nc.subscribe(topic, cb=on_msg)
            logger.info(f"Reflective subscribed to {topic}")

    async def handle_event(self, event: Event) -> Optional[Event]:
        logger.info(f"Reflective received: {event.type}")
        task = event.data.get("task", {})
        task_type = task.get("type", "general")
        source = event.data.get("result", {}).get("source", "unknown")

        summary = {
            "summary": f"Processed task of type '{task_type}' with success.",
            "task_id": task.get("task_id"),
            "outcome": "success",
            "source_module": source,
        }

        reflection_event = Event(
            type=EventType.REFLECTION_DONE,
            source=self.module_id,
            data={"summary": summary},
            metadata={"trace_id": event.metadata.get("trace_id", "")},
        )

        logger.info(f"Reflection emitted for task {task.get('task_id')}")

        return reflection_event

    async def shutdown(self) -> None:
        if self.nc:
            await self.nc.drain()
        logger.info("Reflective shut down")


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    module = ReflectiveModule()
    ctx = ModuleContext(
        module_id=os.getenv("MODULE_ID", "reflective-v1"),
        nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
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