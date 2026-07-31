"""Autonomous Goal Generation — Entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.autonomy.controller import AutonomyLoopController
from core.autonomy.curiosity import CuriosityEngine
from core.autonomy.environment import EnvironmentAnalyzer
from core.autonomy.healing import SelfHealingSystem
from core.autonomy.idle import IdleStateIntelligence
from core.autonomy.scheduler import PriorityScheduler
from core.autonomy.weakness import WeaknessDetector
from core.bus.nats_bus import NatsEventBus
from core.state.redis_state import RedisLiveState
from core.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    bus = NatsEventBus()
    redis = RedisLiveState(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    connect_timeout = float(os.getenv("CONNECT_TIMEOUT", "10"))
    startup_timeout = float(os.getenv("STARTUP_TIMEOUT", "30"))

    await asyncio.wait_for(
        bus.connect(os.getenv("NATS_URL", "nats://localhost:4222")),
        timeout=connect_timeout,
    )
    await asyncio.wait_for(redis.connect(), timeout=connect_timeout)

    scheduler = PriorityScheduler()
    idle = IdleStateIntelligence(bus, redis)
    healing = SelfHealingSystem(bus, redis)
    curiosity = CuriosityEngine()
    weakness = WeaknessDetector()
    environment = EnvironmentAnalyzer()
    controller = AutonomyLoopController(bus, redis)

    await asyncio.wait_for(idle.start(), timeout=startup_timeout)
    await asyncio.wait_for(healing.start(), timeout=startup_timeout)
    await asyncio.wait_for(controller.start(), timeout=startup_timeout)
    logger.info("Autonomy Service started")

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await controller.stop()
        await healing.stop()
        await idle.stop()
        await bus.close()
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
