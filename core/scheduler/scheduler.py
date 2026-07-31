"""Scheduler — Background tasks and cron-like event triggers."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, Optional

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType

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
        tasks = list(self._tasks.items())
        for name, task in tasks:
            task.cancel()
            logger.info(f"Cancelled scheduled task: {name}")
        self._tasks.clear()
        if tasks:
            results = await asyncio.gather(
                *(task for _, task in tasks), return_exceptions=True
            )
            for (name, _), result in zip(tasks, results):
                if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
                    logger.error(
                        "Scheduled task failed during shutdown: %s",
                        name,
                        exc_info=(type(result), result, result.__traceback__),
                    )

    async def schedule_cron(
        self, name: str, interval_seconds: int, topic: str, payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Schedule a recurring event at a fixed interval."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        previous = self._tasks.get(name)
        if previous is not None and not previous.done():
            previous.cancel()
            await asyncio.gather(previous, return_exceptions=True)

        async def _loop():
            while self._running:
                await asyncio.sleep(interval_seconds)
                event = Event(
                    type=EventType.SCHEDULE_TRIGGER,
                    source=f"scheduler:{name}",
                    payload={"topic": topic, "payload": payload or {}},
                )
                await self.bus.publish(topic, event)
                logger.debug(f"Scheduled trigger: {name} → {topic}")

        task = asyncio.create_task(_loop(), name=name)
        self._tasks[name] = task
        task.add_done_callback(self._task_done)
        logger.info(f"Scheduled cron: {name} every {interval_seconds}s → {topic}")

    def _task_done(self, task: asyncio.Task) -> None:
        """Consume task exceptions so failed schedules are observable."""
        if task.cancelled():
            return
        try:
            error = task.exception()
        except asyncio.CancelledError:
            return
        if error is not None:
            logger.error(
                "Scheduled task failed",
                exc_info=(type(error), error, error.__traceback__),
            )
