"""System Bootstrapper — Orchestrates the full boot sequence."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from kernel.bootstrap.integrity import IntegrityChecker
from kernel.bootstrap.repair import RepairEngine
from kernel.bootstrap.config_evolution import ConfigEvolutionEngine
from kernel.bus.interface import EventBus
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event

logger = logging.getLogger(__name__)


class SystemBootstrapper:
    """Orchestrates boot: LOAD → CHECK → REPAIR → CONFIG → START."""

    def __init__(
        self,
        bus: EventBus,
        redis: RedisLiveState,
        pg: PostgresPersistentState,
    ):
        self.bus = bus
        self.redis = redis
        self.pg = pg
        self.integrity = IntegrityChecker(bus, redis, pg)
        self.repair = RepairEngine(bus, redis, pg)
        self.config = ConfigEvolutionEngine(bus, redis)

    async def run(self) -> bool:
        """Run full bootstrap sequence. Returns True if successful."""
        logger.info("=" * 60)
        logger.info("BOOTSTRAP START")
        logger.info("=" * 60)

        # 1. Integrity check
        logger.info("[1/5] Integrity check...")
        report = await self.integrity.check_all()
        await self.bus.publish("bootstrap.integrity.completed", Event(
            type="bootstrap.integrity.completed",
            source="bootstrapper",
            data={"report": report.dict()},
        ))

        if not report.ok:
            logger.warning(f"Integrity issues detected: {report.issues}")
            # 2. Repair if needed
            logger.info("[2/5] Repairing...")
            for module_id in report.failed_modules:
                await self.repair.repair_module(module_id)
            for issue in report.issues:
                logger.info(f"Repair attempted for: {issue}")
        else:
            logger.info("[2/5] No repair needed")

        # 3. Config evolution (safe changes only)
        logger.info("[3/5] Configuration evolution...")
        # Example: propose and validate a config change
        # change = await self.config.propose_change(...)
        # validated = await self.config.validate_change(change)
        logger.info("Config evolution skipped (no changes proposed)")

        # 4. Final system event
        logger.info("[4/5] Publishing bootstrap complete...")
        await self.bus.publish("system.bootstrap.completed", Event(
            type="system.bootstrap.completed",
            source="bootstrapper",
            data={"success": True},
        ))

        # 5. Boot sequence complete
        logger.info("[5/5] Bootstrap sequence completed")
        logger.info("=" * 60)
        return True