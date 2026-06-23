"""Autonomous Goal Generation — Entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from kernel.autonomy.curiosity import CuriosityEngine
from kernel.autonomy.environment import EnvironmentAnalyzer
from kernel.autonomy.engine import AutonomyEngine
from kernel.autonomy.weakness import WeaknessDetector
from kernel.bus.nats_bus import NatsEventBus
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from kernel.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    bus = NatsEventBus()
    redis = RedisLiveState(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    pg = PostgresPersistentState(os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan"))

    await bus.connect(os.getenv("NATS_URL", "nats://localhost:4222"))
    await redis.connect()
    await pg.connect()

    curiosity = CuriosityEngine()
    weakness = WeaknessDetector()
    environment = EnvironmentAnalyzer()

    engine = AutonomyEngine(
        bus=bus,
        redis=redis,
        curiosity=curiosity,
        weakness=weakness,
        environment=environment,
    )

    await engine.start()

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await engine.stop()
        await bus.close()
        await redis.close()
        await pg.close()


if __name__ == "__main__":
    asyncio.run(main())