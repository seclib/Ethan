"""Executive Module — Parses user intents and creates structured tasks."""

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
from nats.aio.msg import Msg

from sdk.event import Event, EventType
from sdk.module import CognitiveModule, ModuleContext, ModuleManifest
from kernel.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)

TASK_TYPES = {
    "analyze": "analysis",
    "analyse": "analysis",
    "search": "research",
    "find": "research",
    "send": "communication",
    "notify": "communication",
    "schedule": "scheduling",
    "plan": "scheduling",
    "create": "generation",
    "write": "generation",
    "summarize": "summarization",
    "summarise": "summarization",
    "translate": "translation",
}


class ExecutiveModule(CognitiveModule):
    """Receives raw user intents and emits structured task events."""

    def __init__(self):
        self.nc: Optional[nats.NATS] = None
        self.module_id = "executive-v1"

    def get_manifest(self) -> ModuleManifest:
        return ModuleManifest(
            module_id=self.module_id,
            name="Executive Module",
            version="1.0.0",
            capabilities=["module.executive"],
            topics_subscribed=["ethan.intent.user"],
            topics_published=["ethan.task.created"],
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
                logger.error(f"Executive handler error: {e}")

        for topic in self.get_manifest().topics_subscribed:
            await self.nc.subscribe(topic, cb=on_msg)
            logger.info(f"Executive subscribed to {topic}")

    async def handle_event(self, event: Event) -> Optional[Event]:
        logger.info(f"Executive received: {event.type}")
        intent = event.data.get("intent", {})
        user_input = intent.get("user_input", "")
        source = intent.get("source", "text")

        task_type = self._classify(user_input)

        task = {
            "task_id": str(uuid4()),
            "type": task_type,
            "source": source,
            "input": user_input,
            "priority": "normal",
            "context": intent.get("context", {}),
            "session_id": event.metadata.get("session_id", ""),
            "user_id": event.metadata.get("auth", {}).get("user_id", "anonymous"),
        }

        logger.info(f"Executive created task: type={task_type} id={task['task_id']}")

        return Event(
            id=task["task_id"],
            type=EventType.TASK_CREATED,
            source=self.module_id,
            data={"task": task},
            metadata={"trace_id": event.metadata.get("trace_id", "")},
        )

    def _classify(self, text: str) -> str:
        text_lower = text.lower()
        for keyword, task_type in TASK_TYPES.items():
            if keyword in text_lower:
                return task_type
        return "general"

    async def shutdown(self) -> None:
        if self.nc:
            await self.nc.drain()
            logger.info("Executive shut down")


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    module = ExecutiveModule()
    ctx = ModuleContext(
        module_id=os.getenv("MODULE_ID", "executive-v1"),
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