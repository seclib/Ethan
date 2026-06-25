"""Self-Healing System — Detects failures and isolates broken modules."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from kernel.bus.interface import EventBus
from kernel.state.redis_state import RedisLiveState
from sdk.autonomy import HealthStatus
from sdk.event import Event

logger = logging.getLogger(__name__)


class SelfHealingSystem:
    """Monitors modules, retries failed operations, isolates broken modules."""

    MAX_RETRIES = 3
    ISOLATION_THRESHOLD = 3

    def __init__(self, bus: EventBus, redis: RedisLiveState):
        self.bus = bus
        self.redis = redis
        self._failures: Dict[str, int] = {}
        self._running = False

    async def start(self) -> None:
        self._running = True
        await self.bus.subscribe("system.error", self._on_error, queue="self-healing")
        logger.info("Self-Healing System started")

    async def stop(self) -> None:
        self._running = False
        logger.info("Self-Healing System stopped")

    async def _on_error(self, event: Event) -> None:
        if not self._running:
            return
        try:
            module_id = event.data.get("module_id", event.source)
            self._failures[module_id] = self._failures.get(module_id, 0) + 1
            consecutive = self._failures[module_id]

            status = HealthStatus(
                module_id=module_id,
                healthy=consecutive < self.ISOLATION_THRESHOLD,
                consecutive_failures=consecutive,
                last_failure=event.timestamp,
                isolation_reason="" if consecutive < self.ISOLATION_THRESHOLD else f"Failed {consecutive} times",
            )
            await self.redis.set(f"health:{module_id}", status.dict(), ttl=3600)

            if consecutive >= self.ISOLATION_THRESHOLD:
                await self._isolate_module(module_id)
            else:
                logger.warning(f"Module {module_id} failure {consecutive}/{self.MAX_RETRIES}")

            await self.bus.publish("autonomy.self_heal.triggered", Event(
                type="autonomy.self_heal.triggered",
                source="self-healing",
                data={"status": status.dict()},
            ))
        except Exception as e:
            logger.error(f"Self-healing handler failed: {e}")

    async def _isolate_module(self, module_id: str) -> None:
        """Remove broken module from registry."""
        logger.warning(f"Isolating module: {module_id}")
        await self.bus.publish("system.module.unhealthy", Event(
            type="system.module.unhealthy",
            source="self-healing",
            data={"module_id": module_id, "action": "isolate"},
        ))

    async def reset_failures(self, module_id: str) -> None:
        """Clear failure counter after successful operation."""
        self._failures.pop(module_id, None)
        status = HealthStatus(module_id=module_id, healthy=True, consecutive_failures=0,
                              last_success=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat())
        await self.redis.set(f"health:{module_id}", status.dict(), ttl=3600)