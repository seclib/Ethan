"""Autonomous Goal Generation — Entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from kernel.autonomy.controller import AutonomyLoopController
from kernel.autonomy.curiosity import CuriosityEngine
from kernel.autonomy.environment import EnvironmentAnalyzer
from kernel.autonomy.healing import SelfHealingSystem
from kernel.autonomy.idle import IdleStateIntelligence
from kernel.autonomy.scheduler import PriorityScheduler
from kernel.autonomy.weakness import WeaknessDetector
from kernel.bus.nats_bus import NatsEventBus
from kernel.state.redis_state import RedisLiveState
from kernel.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    bus = NatsEventBus()
    redis = RedisLiveState(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    await bus.connect(os.getenv("NATS_URL", "nats://localhost:4222"))
    await redis.connect()

    scheduler = PriorityScheduler()
    idle = IdleStateIntelligence(bus, redis)
    healing = SelfHealingSystem(bus, redis)
    curiosity = CuriosityEngine()
    weakness = WeaknessDetector()
    environment = EnvironmentAnalyzer()
    controller = AutonomyLoopController(bus, redis)

    await idle.start()
    await healing.start()
    await controller.start()
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