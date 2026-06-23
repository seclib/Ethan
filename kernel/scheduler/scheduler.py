"""Scheduler — Background tasks and cron-like event triggers."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, Optional

from kernel.bus.interface import EventBus
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)


class Scheduler:
    """Manages background tasks and scheduled event triggers."""

    def __init__(self, bus: EventBus):
        self.bus = bus
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        """Start scheduler loop."""
        self._running = True
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop all scheduled tasks."""
        self._running = False
        for name, task in self._tasks.items():
            task.cancel()
            logger.info(f"Cancelled scheduled task: {name}")
        self._tasks.clear()

    async def schedule_cron(
        self, name: str, interval_seconds: int, topic: str, payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Schedule a recurring event at a fixed interval."""
        async def _loop():
            while self._running:
                await asyncio.sleep(interval_seconds)
                event = Event(
                    type=EventType.SCHEDULE_TRIGGER,
                    source=f"scheduler:{name}",
                    data={"topic": topic, "payload": payload or {}},
                )
                await self.bus.publish(topic, event)
                logger.debug(f"Scheduled trigger: {name} → {topic}")

        task = asyncio.create_task(_loop(), name=name)
        self._tasks[name] = task
        logger.info(f"Scheduled cron: {name} every {interval_seconds}s → {topic}")