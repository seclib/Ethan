"""Bootstrap — Entry point for the Cognitive Kernel service."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

from core.autonomy.controller import AutonomyLoopController
from core.autonomy.curiosity import CuriosityEngine
from core.autonomy.environment import EnvironmentAnalyzer
from core.autonomy.weakness import WeaknessDetector
from core.bootstrap.bootstrapper import SystemBootstrapper
from core.bus.nats_bus import EventBus as NatsEventBus
from core.goals.manager import GoalManager
from core.kernel import CognitiveKernel
from core.learning.engine import LearningEngine
from core.learning.detector import PatternDetector
from core.learning.generator import RuleGenerator
from core.learning.modeler import SelfModelUpdater
from core.learning.store import ExperienceStore
from core.metacognition.engine import MetaCognitionEngine
from core.metacognition.load import CognitiveLoadManager
from core.metacognition.prioritizer import ModulePrioritizer
from core.metacognition.strategy import DecisionStrategySelector
from core.metacognition.trace import ThoughtTraceAnalyzer
from core.registry.module import ModuleRegistry
from core.scheduler.scheduler import Scheduler
from core.state.composite_backend import CompositeStateBackend
from core.state.postgres_state import PostgresPersistentState
from core.state.redis_state import RedisLiveState
from core.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    """Start the Cognitive Kernel with optional Learning + Meta-Cognition + Autonomy + Bootstrap."""
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan",
    )
    log_level = os.getenv("LOG_LEVEL", "INFO")
    enable_learning = os.getenv("ENABLE_LEARNING", "false").lower() == "true"
    enable_metacognition = os.getenv("ENABLE_METACOGNITION", "false").lower() == "true"
    enable_autonomy = os.getenv("ENABLE_AUTONOMY", "false").lower() == "true"
    connect_timeout = int(os.getenv("CONNECT_TIMEOUT", "10"))

    setup_logging(log_level)
    logger.info("Cognitive Kernel bootstrapping... learning=%s metacognition=%s autonomy=%s",
                enable_learning, enable_metacognition, enable_autonomy)

    bus = NatsEventBus(servers=nats_url)
    redis = RedisLiveState(redis_url)
    pg = PostgresPersistentState(database_url)

    # ── Résilience : retry avec timeout sur connexions externes ────────

    # Retry NATS connection with timeout
    for attempt in range(1, 11):
        try:
            await asyncio.wait_for(bus.connect(), timeout=connect_timeout)
            logger.info("NATS connection established")
            break
        except asyncio.TimeoutError:
            if attempt == 10:
                raise
            wait = min(attempt * 2, 10)
            logger.warning("NATS connection timeout, retry %s/%s in %ss", attempt, 10, wait)
            await asyncio.sleep(wait)
        except Exception as exc:
            if attempt == 10:
                raise
            wait = min(attempt * 2, 10)
            logger.warning("NATS connection failed (%s), retry %s/%s in %ss", exc, attempt, 10, wait)
            await asyncio.sleep(wait)

    # Retry Redis connection with timeout
    for attempt in range(1, 11):
        try:
            await asyncio.wait_for(redis.connect(), timeout=connect_timeout)
            logger.info("Redis connection established")
            break
        except asyncio.TimeoutError:
            if attempt == 10:
                raise
            wait = min(attempt * 2, 10)
            logger.warning("Redis connection timeout, retry %s/%s in %ss", attempt, 10, wait)
            await asyncio.sleep(wait)
        except Exception as exc:
            if attempt == 10:
                raise
            wait = min(attempt * 2, 10)
            logger.warning("Redis connection failed (%s), retry %s/%s in %ss", exc, attempt, 10, wait)
            await asyncio.sleep(wait)

    # Retry PostgreSQL connection with timeout
    for attempt in range(1, 11):
        try:
            await asyncio.wait_for(pg.connect(), timeout=connect_timeout)
            logger.info("PostgreSQL connection established")
            break
        except asyncio.TimeoutError:
            if attempt == 10:
                raise
            wait = min(attempt * 2, 10)
            logger.warning("PostgreSQL connection timeout, retry %s/%s in %ss", attempt, 10, wait)
            await asyncio.sleep(wait)
        except Exception as exc:
            if attempt == 10:
                raise
            wait = min(attempt * 2, 10)
            logger.warning("PostgreSQL connection failed (%s), retry %s/%s in %ss", exc, attempt, 10, wait)
            await asyncio.sleep(wait)

    # Run system bootstrap (integrity check + repair)
    bootstrapper = SystemBootstrapper(bus, redis, pg)
    await bootstrapper.run()

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

    metacognition = None
    if enable_metacognition:
        strategy = DecisionStrategySelector()
        load_manager = CognitiveLoadManager()
        prioritizer = ModulePrioritizer()
        trace_analyzer = ThoughtTraceAnalyzer()
        metacognition = MetaCognitionEngine(
            bus=bus,
            redis=redis,
            strategy=strategy,
            load_manager=load_manager,
            prioritizer=prioritizer,
            trace_analyzer=trace_analyzer,
        )
        logger.info("Meta-Cognition Engine initialized")

    autonomy = None
    if enable_autonomy:
        curiosity = CuriosityEngine()
        weakness = WeaknessDetector()
        environment = EnvironmentAnalyzer()
        autonomy = AutonomyLoopController(bus=bus, redis=redis)
        logger.info("Autonomy Loop Controller initialized")

    # Create composite state backend for Kernel (Clean Architecture)
    state = CompositeStateBackend(redis, pg)
    
    kernel = CognitiveKernel(
        bus=bus,
        state=state,
        registry=registry,
        goals=goals,
        scheduler=scheduler,
        learning=learning,
        metacognition=metacognition,
        autonomy=autonomy,
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