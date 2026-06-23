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
from kernel.registry.module_registry import ModuleRegistry
from kernel.scheduler.scheduler import Scheduler
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from kernel.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    """Start the Cognitive Kernel."""
    # Configuration from environment
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan",
    )
    log_level = os.getenv("LOG_LEVEL", "INFO")

    # Setup logging
    setup_logging(log_level)
    logger.info("Cognitive Kernel bootstrapping...")

    # Initialize infrastructure
    bus = NatsEventBus()
    redis = RedisLiveState(redis_url)
    pg = PostgresPersistentState(database_url)

    # Connect to infrastructure
    await bus.connect(nats_url)
    await redis.connect()
    await pg.connect()

    # Initialize subsystems
    scheduler = Scheduler(bus)
    registry = ModuleRegistry(bus, pg, redis)
    goals = GoalManager(bus, pg, redis)

    # Create and start kernel
    kernel = CognitiveKernel(
        bus=bus,
        redis=redis,
        pg=pg,
        registry=registry,
        goals=goals,
        scheduler=scheduler,
    )

    await kernel.start()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    stop = asyncio.Future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(
                sig,
                lambda: asyncio.ensure_future(_shutdown(kernel, stop)),
            )
        except NotImplementedError:
            # Windows compatibility
            signal.signal(sig, lambda s, f: asyncio.ensure_future(_shutdown(kernel, stop)))

    # Keep running until shutdown
    await stop
    logger.info("Kernel bootstrap complete, awaiting shutdown")


async def _shutdown(kernel: CognitiveKernel, stop: asyncio.Future):
    """Graceful shutdown."""
    logger.info("Shutdown signal received")
    await kernel.stop()
    if not stop.done():
        stop.set_result(None)


if __name__ == "__main__":
    asyncio.run(main())