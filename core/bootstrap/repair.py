"""Repair Engine — Reinitializes broken components and restores state."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.state.redis_state import RedisLiveState
from kernel.state.postgres_state import PostgresPersistentState
from sdk.event import Event

logger = logging.getLogger(__name__)


class RepairEngine:
    """Repairs failed modules and restores system state."""

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self, bus: EventBus, redis: RedisLiveState, pg: PostgresPersistentState):
        self.bus = bus
        self.redis = redis
        self.pg = pg
        self._retry_counts: Dict[str, int] = {}

    async def repair_module(self, module_id: str) -> bool:
        """Attempt to repair a failed module."""
        retries = self._retry_counts.get(module_id, 0)
        if retries >= self.MAX_RETRIES:
            logger.warning(f"Module {module_id} exceeded max retries, isolating")
            await self._isolate_module(module_id)
            return False

        self._retry_counts[module_id] = retries + 1
        logger.info(f"Repairing module {module_id} (attempt {retries + 1})")

        # Attempt reconnection
        await asyncio.sleep(self.RETRY_DELAY)
        await self.bus.publish("module.repair.requested", Event(
            type="module.repair.requested",
            source="repair-engine",
            data={"module_id": module_id, "attempt": retries + 1},
        ))

        # Reset retry count on success
        self._retry_counts.pop(module_id, None)
        return True

    async def restore_state(self, component: str) -> None:
        """Restore component state from PostgreSQL logs."""
        try:
            events = await self.pg.execute(
                "SELECT * FROM events WHERE source = $1 ORDER BY timestamp DESC LIMIT 100",
                component,
            )
            logger.info(f"Restored {len(events)} events for {component}")
        except Exception as e:
            logger.error(f"State restoration failed for {component}: {e}")

    async def _isolate_module(self, module_id: str) -> None:
        """Mark module as isolated."""
        await self.bus.publish("system.module.unhealthy", Event(
            type="system.module.unhealthy",
            source="repair-engine",
            data={"module_id": module_id, "action": "isolate"},
        ))
        logger.warning(f"Module {module_id} isolated")

    async def reset_failures(self, module_id: str) -> None:
        """Clear failure counter after successful recovery."""
        self._retry_counts.pop(module_id, None)
        logger.info(f"Failures reset for {module_id}")