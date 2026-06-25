"""Integrity Checker — Validates system components before boot."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.state.redis_state import RedisLiveState
from kernel.state.postgres_state import PostgresPersistentState
from sdk.event import Event

logger = logging.getLogger(__name__)


@dataclass
class IntegrityReport:
    """Result of system integrity check."""
    ok: bool = True
    modules_ok: bool = True
    event_bus_ok: bool = True
    state_ok: bool = True
    missing_dependencies: List[str] = field(default_factory=list)
    failed_modules: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    checked_at: str = ""
    duration_ms: float = 0.0

    def dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "modules_ok": self.modules_ok,
            "event_bus_ok": self.event_bus_ok,
            "state_ok": self.state_ok,
            "missing_dependencies": self.missing_dependencies,
            "failed_modules": self.failed_modules,
            "issues": self.issues,
            "checked_at": self.checked_at,
            "duration_ms": self.duration_ms,
        }


class IntegrityChecker:
    """Validates event bus, modules, and state systems."""

    def __init__(self, bus: EventBus, redis: RedisLiveState, pg: PostgresPersistentState):
        self.bus = bus
        self.redis = redis
        self.pg = pg

    async def check_all(self) -> IntegrityReport:
        """Run all checks and return report."""
        start = asyncio.get_event_loop().time()
        report = IntegrityReport()

        # 1. Check event bus
        try:
            await self.bus.publish("bootstrap.integrity.check", Event(
                type="bootstrap.integrity.check",
                source="integrity-checker",
                data={},
            ))
            report.event_bus_ok = True
        except Exception as e:
            report.event_bus_ok = False
            report.issues.append(f"Event bus check failed: {e}")

        # 2. Check state systems
        try:
            await self.redis.set("bootstrap:healthcheck", {"status": "ok"}, ttl=60)
            pg_ok = await self.pg.execute("SELECT 1") is not None
            report.state_ok = bool(pg_ok)
            if not report.state_ok:
                report.issues.append("State system check failed")
        except Exception as e:
            report.state_ok = False
            report.issues.append(f"State check failed: {e}")

        # 3. Check modules
        try:
            from kernel.registry.module_registry import ModuleRegistry
            registry = ModuleRegistry(self.bus, self.pg, self.redis)
            modules = await registry.discover()
            for m in modules:
                if not m.capabilities:
                    report.failed_modules.append(m.id)
                    report.modules_ok = False
            if not modules:
                report.missing_dependencies.append("No modules registered")
        except Exception as e:
            report.modules_ok = False
            report.issues.append(f"Module check failed: {e}")

        report.ok = report.event_bus_ok and report.state_ok and report.modules_ok
        report.checked_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        report.duration_ms = (asyncio.get_event_loop().time() - start) * 1000

        logger.info(f"Integrity check completed: ok={report.ok} issues={len(report.issues)}")
        return report