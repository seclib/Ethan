"""ETHAN Core — compatibility CLI entry point.

Reçoit la configuration en paramètre.
ZÉRO dépendance OS (pas de os.getenv, sys.path, signal).

The production Compose entrypoints are deliberately split: ``core/ethan_bootstrap.py``
starts the kernel and ``python -m core.modules`` starts the four NATS cognitive
modules. This CLI remains a minimal in-process harness and does not duplicate
that module service wiring.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os

from core.bus.memory_bus import MemoryEventBus
from core.goals.manager import GoalManager
from core.kernel import CognitiveKernel
from core.registry.module import ModuleRegistry
from core.scheduler.scheduler import Scheduler
from core.state.interface import StateBackend
from core.state.memory_backend import MemoryStateBackend


logger = logging.getLogger(__name__)


# Ensure project root is importable when running from source checkouts
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_here, "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


async def create_kernel(
    bus,
    state: StateBackend,
    registry: ModuleRegistry,
    config: dict,
) -> CognitiveKernel:
    """Crée et retourne un kernel (sans démarrage automatique).

    Args:
        bus: EventBus (déjà connecté)
        state: StateBackend (déjà connecté)
        registry: ModuleRegistry
        config: Configuration (dict injecté)

    Returns:
        Kernel prêt à démarrer
    """
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

    from core.autonomy.controller import AutonomyLoopController

    enable_learning = config.get("enable_learning", False)
    enable_metacognition = config.get("enable_metacognition", False)
    enable_autonomy = config.get("enable_autonomy", False)

    learning = None
    if enable_learning:
        store = ExperienceStore(state, state)
        detector = PatternDetector(threshold=3)
        generator = RuleGenerator()
        modeler = SelfModelUpdater(state)
        learning = LearningEngine(bus, store, detector, generator, modeler)

    metacognition = None
    if enable_metacognition:
        strategy = DecisionStrategySelector()
        load_manager = CognitiveLoadManager()
        prioritizer = ModulePrioritizer()
        trace_analyzer = ThoughtTraceAnalyzer()
        metacognition = MetaCognitionEngine(
            bus=bus,
            redis=state,
            strategy=strategy,
            load_manager=load_manager,
            prioritizer=prioritizer,
            trace_analyzer=trace_analyzer,
        )

    autonomy = None
    if enable_autonomy:
        autonomy = AutonomyLoopController(bus=bus, redis=state)

    goals = GoalManager(bus, state, state)
    scheduler = Scheduler(bus)
    
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
    return kernel


def main() -> None:
    """Entry point CLI (pyproject.toml: core.main:main).

    Démarre un kernel minimal avec backend mémoire pour tests.
    """
    logging.basicConfig(level=logging.INFO)

    async def _main():
        bus = MemoryEventBus()
        state = MemoryStateBackend()
        registry = ModuleRegistry(bus, state)

        config = {
            "nats_url": "nats://localhost:4222",
            "redis_url": "redis://localhost:6379/0",
            "postgres_url": "postgresql://localhost:5432/ethan",
            "grpc_port": 50051,
            "log_level": "INFO",
        }

        kernel = await create_kernel(bus, state, registry, config)
        await kernel.start()

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await kernel.stop()

    asyncio.run(_main())


if __name__ == "__main__":
    main()
