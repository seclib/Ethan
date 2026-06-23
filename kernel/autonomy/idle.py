"""Idle State Intelligence — Detects inactivity and triggers internal work."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from kernel.bus.interface import EventBus
from sdk.event import Event
from sdk.autonomy import CycleState

logger = logging.getLogger(__name__)


class IdleStateIntelligence:
    """Monitors idle time and triggers autonomous goals."""

    IDLE_THRESHOLD_SECONDS = 30

    def __init__(self, bus: EventBus, redis_client):
        self.bus = bus
        self.redis = redis_client
        self._idle_since = 0.0
        self._running = False

    async def start(self) -> None:
        self._running = True
        asyncio.create_task(self._watch_idle())
        logger.info("Idle State Intelligence started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Idle State Intelligence stopped")

    async def _watch_idle(self) -> None:
        while self._running:
            await asyncio.sleep(5)
            last_event = self._get_last_event_time()
            if last_event and (asyncio.get_event_loop().time() - last_event) > self.IDLE_THRESHOLD_SECONDS:
                await self.bus.publish("idle.detected", Event(
                    type="idle.detected",
                    source="idle-intelligence",
                    data={"idle_seconds": int(asyncio.get_event_loop().time() - last_event)},
                ))
                logger.info("Idle state detected")

    def _get_last_event_time(self) -> float:
        return asyncio.get_event_loop().time()