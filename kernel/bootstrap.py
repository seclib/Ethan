"""Bootstrap — Entry point for the Cognitive Kernel service."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.bus.nats_bus import NatsEventBus
from kernel.goals.manager import GoalManager
from kernel.kernel import CognitiveKernel
from kernel.learning.engine import LearningEngine
from kernel.learning.modeler import SelfModelUpdater
from kernel.learning.store import ExperienceStore
from kernel.learning.detector import PatternDetector
from kernel.learning.generator import RuleGenerator
from kernel.registry.module_registry import ModuleRegistry
from kernel.scheduler.scheduler import Scheduler
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from kernel.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    """Start the Cognitive Kernel with optional Learning Engine."""
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan",
    )
    log_level = os.getenv("LOG_LEVEL", "INFO")
    enable_learning = os.getenv("ENABLE_LEARNING", "false").lower() == "true"

    setup_logging(log_level)
    logger.info("Cognitive Kernel bootstrapping... learning=%s", enable_learning)

    bus = NatsEventBus()
    redis = RedisLiveState(redis_url)
    pg = PostgresPersistentState(database_url)

    await bus.connect(nats_url)
    await redis.connect()
    await pg.connect()

    scheduler = Scheduler(bus)
    registry = ModuleRegistry(bus, pg, redis)
    goals = GoalManager(bus, pg, redis)

    learning = None
    if enable_learning:
        store = ExperienceStore(redis, pg)
        detector = PatternDetector(threshold=3)
        generator = RuleGenerator()
        modeler = SelfModelUpdater(redis)
        learning = LearningEngine(bus, store, detector, generator, modeler)
        logger.info("Learning Engine initialized")

    kernel = CognitiveKernel(
        bus=bus,
        redis=redis,
        pg=pg,
        registry=registry,
        goals=goals,
        scheduler=scheduler,
        learning=learning,
    )

    await kernel.start()

    loop = asyncio.get_event_loop()
    stop = asyncio.Future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(
                sig,
                lambda: asyncio.ensure_future(_shutdown(kernel, stop)),
            )
        except NotImplementedError:
            signal.signal(sig, lambda s, f: asyncio.ensure_future(_shutdown(kernel, stop)))

    await stop
    logger.info("Kernel bootstrap complete, awaiting shutdown")


async def _shutdown(kernel: CognitiveKernel, stop: asyncio.Future):
    logger.info("Shutdown signal received")
    await kernel.stop()
    if not stop.done():
        stop.set_result(None)


if __name__ == "__main__":
    asyncio.run(main())