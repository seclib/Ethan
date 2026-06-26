"""ETHAN Core — Entry point isolated.

Reçoit la configuration en paramètre.
ZÉRO dépendance OS (pas de os.getenv, sys.path, signal).
"""

from __future__ import annotations

import asyncio
import logging

from core.bus.memory_bus import MemoryEventBus
from core.kernel.engine import CognitiveKernel
from core.registry.module import ModuleRegistry
from core.state.interface import StateBackend


logger = logging.getLogger(__name__)


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
    kernel = CognitiveKernel(
        bus=bus,
        state=state,
        registry=registry,
        config=config,
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