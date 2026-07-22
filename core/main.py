"""ETHAN Core — Entry point isolated.

Reçoit la configuration en paramètre.
ZÉRO dépendance OS (pas de os.getenv, sys.path, signal).
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
    goals = GoalManager(bus, state, state)
    scheduler = Scheduler(bus)
    
    kernel = CognitiveKernel(
        bus=bus,
        state=state,
        registry=registry,
        goals=goals,
        scheduler=scheduler,
    )
    return kernel


# Entrypoint pour tests/dev
if __name__ == "__main__":
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