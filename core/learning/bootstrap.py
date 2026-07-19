"""Learning Engine — Entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.bus.nats_bus import NatsEventBus
from core.learning.detector import PatternDetector
from core.learning.engine import LearningEngine
from core.learning.generator import RuleGenerator
from core.learning.modeler import SelfModelUpdater
from core.learning.store import ExperienceStore
from core.state.postgres_state import PostgresPersistentState
from core.state.redis_state import RedisLiveState
from core.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    bus = NatsEventBus()
    redis = RedisLiveState(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    pg = PostgresPersistentState(os.getenv("DATABASE_URL", "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan"))

    await bus.connect(os.getenv("NATS_URL", "nats://localhost:4222"))
    await redis.connect()
    await pg.connect()

    store = ExperienceStore(redis, pg)
    detector = PatternDetector(threshold=3)
    generator = RuleGenerator()
    modeler = SelfModelUpdater(redis)

    engine = LearningEngine(bus, store, detector, generator, modeler)
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