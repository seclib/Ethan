"""Idle State Intelligence — Detects inactivity and triggers internal work."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from core.bus.interface import EventBus
from core.ethan_types.event import Event
from core.ethan_types.sdk.autonomy import CycleState

logger = logging.getLogger(__name__)


class IdleStateIntelligence:
    """Monitors idle time and triggers autonomous goals."""

    IDLE_THRESHOLD_SECONDS = 30

    def __init__(self, bus: EventBus, redis_client):
        self.bus = bus
        self.redis = redis_client
        self._idle_since = 0.0
        self._running = False
        self._watch_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._watch_task = asyncio.create_task(self._watch_idle(), name="idle-watch")
        self._watch_task.add_done_callback(self._watch_done)
        logger.info("Idle State Intelligence started")

    async def stop(self) -> None:
        self._running = False
        if self._watch_task is not None:
            self._watch_task.cancel()
            try:
                await asyncio.wait_for(self._watch_task, timeout=5)
            except asyncio.CancelledError:
                pass
            finally:
                self._watch_task = None
        logger.info("Idle State Intelligence stopped")

    def _watch_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        try:
            error = task.exception()
        except asyncio.CancelledError:
            return
        if error is not None:
            logger.error(
                "Idle watcher failed",
                exc_info=(type(error), error, error.__traceback__),
            )

    async def _watch_idle(self) -> None:
        while self._running:
            await asyncio.sleep(5)
            last_event = self._get_last_event_time()
            if last_event and (asyncio.get_event_loop().time() - last_event) > self.IDLE_THRESHOLD_SECONDS:
                await self.bus.publish("idle.detected", Event(
                    type="idle.detected",
                    source="idle-intelligence",
                    payload={"idle_seconds": int(asyncio.get_event_loop().time() - last_event)},
                ))
                logger.info("Idle state detected")

    def _get_last_event_time(self) -> float:
        return asyncio.get_event_loop().time()
