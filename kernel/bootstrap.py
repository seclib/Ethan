"""Bootstrap — Entry point for the Cognitive Kernel service."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.autonomy.controller import AutonomyLoopController
from kernel.autonomy.curiosity import CuriosityEngine
from kernel.autonomy.environment import EnvironmentAnalyzer
from kernel.autonomy.healing import SelfHealingSystem
from kernel.autonomy.idle import IdleStateIntelligence
from kernel.autonomy.scheduler import PriorityScheduler
from kernel.autonomy.weakness import WeaknessDetector
from kernel.bootstrap.bootstrapper import SystemBootstrapper
from kernel.bus.nats_bus import NatsEventBus
from kernel.goals.manager import GoalManager
from kernel.kernel import CognitiveKernel
from kernel.learning.engine import LearningEngine
from kernel.learning.modeler import SelfModelUpdater
from kernel.learning.store import ExperienceStore
from kernel.learning.detector import PatternDetector
from kernel.learning.generator import RuleGenerator
from kernel.metacognition.engine import MetaCognitionEngine
from kernel.metacognition.load import CognitiveLoadManager
from kernel.metacognition.prioritizer import ModulePrioritizer
from kernel.metacognition.strategy import DecisionStrategySelector
from kernel.metacognition.trace import ThoughtTraceAnalyzer
from kernel.registry.module_registry import ModuleRegistry
from kernel.scheduler.scheduler import Scheduler
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from kernel.telemetry.logger import setup_logging

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

    setup_logging(log_level)
    logger.info("Cognitive Kernel bootstrapping... learning=%s metacognition=%s autonomy=%s",
                enable_learning, enable_metacognition, enable_autonomy)

    bus = NatsEventBus()
    redis = RedisLiveState(redis_url)
    pg = PostgresPersistentState(database_url)

    await bus.connect(nats_url)
    await redis.connect()
    await pg.connect()

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

    kernel = CognitiveKernel(
        bus=bus,
        redis=redis,
        pg=pg,
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