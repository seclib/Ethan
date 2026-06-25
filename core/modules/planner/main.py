"""Planner Module — Decomposes tasks into executable steps."""

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


PLANNER_RULES = {
    "analysis": [
        {"step": "understand_request", "description": "Parse and understand the request"},
        {"step": "gather_data", "description": "Collect relevant data"},
        {"step": "process_data", "description": "Process and analyze data"},
        {"step": "generate_report", "description": "Generate report from analysis"},
        {"step": "summarize_result", "description": "Summarize findings"},
    ],
    "research": [
        {"step": "parse_query", "description": "Parse search query"},
        {"step": "search_sources", "description": "Search across sources"},
        {"step": "filter_results", "description": "Filter relevant results"},
        {"step": "synthesize", "description": "Synthesize findings"},
    ],
    "communication": [
        {"step": "validate_recipients", "description": "Validate recipients"},
        {"step": "compose_message", "description": "Compose message"},
        {"step": "review_content", "description": "Review content"},
        {"step": "send_message", "description": "Send message"},
    ],
    "scheduling": [
        {"step": "check_availability", "description": "Check participant availability"},
        {"step": "propose_slots", "description": "Propose time slots"},
        {"step": "confirm_booking", "description": "Confirm booking"},
    ],
    "generation": [
        {"step": "define_requirements", "description": "Define requirements"},
        {"step": "draft_content", "description": "Draft content"},
        {"step": "review_draft", "description": "Review draft"},
        {"step": "finalize", "description": "Finalize output"},
    ],
    "summarization": [
        {"step": "read_source", "description": "Read source material"},
        {"step": "extract_key_points", "description": "Extract key points"},
        {"step": "write_summary", "description": "Write summary"},
    ],
    "translation": [
        {"step": "detect_language", "description": "Detect source language"},
        {"step": "translate", "description": "Translate content"},
        {"step": "review_translation", "description": "Review translation"},
    ],
    "general": [
        {"step": "analyze_request", "description": "Analyze the request"},
        {"step": "execute", "description": "Execute primary action"},
        {"step": "confirm_result", "description": "Confirm result"},
    ],
}


class PlannerModule(CognitiveModule):
    """Receives tasks and decomposes them into steps."""

    def __init__(self):
        self.nc: Optional[nats.NATS] = None
        self.module_id = "planner-v1"

    def get_manifest(self) -> ModuleManifest:
        return ModuleManifest(
            module_id=self.module_id,
            name="Planner Module",
            version="1.0.0",
            capabilities=["module.planner"],
            topics_subscribed=["ethan.task.created"],
            topics_published=["ethan.task.plan"],
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
                logger.error(f"Planner handler error: {e}")

        for topic in self.get_manifest().topics_subscribed:
            await self.nc.subscribe(topic, cb=on_msg)
            logger.info(f"Planner subscribed to {topic}")

    async def handle_event(self, event: Event) -> Optional[Event]:
        logger.info(f"Planner received: {event.type}")
        task = event.data.get("task", {})
        task_type = task.get("type", "general")

        steps = self._generate_steps(task_type)

        plan = {
            "plan_id": str(event.id),
            "task_id": task.get("task_id"),
            "task_type": task_type,
            "steps": steps,
            "estimated_steps": len(steps),
        }

        logger.info(f"Planner created plan: {len(steps)} steps for {task_type}")

        return Event(
            type=EventType.TASK_PLAN,
            source=self.module_id,
            data={"plan": plan},
            metadata={"trace_id": event.metadata.get("trace_id", "")},
        )

    def _generate_steps(self, task_type: str) -> list[dict]:
        return PLANNER_RULES.get(task_type, PLANNER_RULES["general"])

    async def shutdown(self) -> None:
        if self.nc:
            await self.nc.drain()
            logger.info("Planner shut down")


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    module = PlannerModule()
    ctx = ModuleContext(
        module_id=os.getenv("MODULE_ID", "planner-v1"),
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