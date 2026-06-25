"""Meta-Cognition Engine — Entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from kernel.bus.nats_bus import NatsEventBus
from kernel.metacognition.engine import MetaCognitionEngine
from kernel.metacognition.load import CognitiveLoadManager
from kernel.metacognition.prioritizer import ModulePrioritizer
from kernel.metacognition.strategy import DecisionStrategySelector
from kernel.metacognition.trace import ThoughtTraceAnalyzer
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

    strategy = DecisionStrategySelector()
    load_manager = CognitiveLoadManager()
    prioritizer = ModulePrioritizer()
    trace_analyzer = ThoughtTraceAnalyzer()

    engine = MetaCognitionEngine(
        bus=bus,
        redis=redis,
        strategy=strategy,
        load_manager=load_manager,
        prioritizer=prioritizer,
        trace_analyzer=trace_analyzer,
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