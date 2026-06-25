"""Configuration Evolution Engine — Applies safe structural changes."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event

logger = logging.getLogger(__name__)


@dataclass
class ConfigChange:
    """Proposed configuration change."""
    change_id: str = ""
    component: str = ""
    old_value: Any = None
    new_value: Any = None
    reason: str = ""
    checksum: str = ""
    applied: bool = False
    rolled_back: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.change_id:
            self.change_id = hashlib.sha256(f"{self.component}:{self.old_value}:{self.new_value}".encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        if not self.checksum:
            self.checksum = hashlib.sha256(str(self.new_value).encode()).hexdigest()[:16]

    def dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "component": self.component,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "checksum": self.checksum,
            "applied": self.applied,
            "rolled_back": self.rolled_back,
            "created_at": self.created_at,
        }


class ConfigEvolutionEngine:
    """Applies safe configuration changes with rollback capability."""

    def __init__(self, bus: EventBus, redis: RedisLiveState):
        self.bus = bus
        self.redis = redis
        self._changes: Dict[str, ConfigChange] = {}

    async def propose_change(self, component: str, old_value: Any, new_value: Any, reason: str = "") -> ConfigChange:
        """Propose a configuration change (not applied yet)."""
        change = ConfigChange(
            component=component,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
        )
        self._changes[change.change_id] = change
        logger.info(f"Config change proposed: {component} {old_value} -> {new_value}")
        return change

    async def apply_change(self, change_id: str) -> bool:
        """Apply a proposed configuration change."""
        change = self._changes.get(change_id)
        if not change:
            logger.warning(f"Unknown config change: {change_id}")
            return False

        try:
            # Store in Redis for rollback
            await self.redis.set(f"config:backup:{change.component}", {
                "old_value": change.old_value,
                "change_id": change.change_id,
            }, ttl=86400)

            # Apply change (in real system, update actual config)
            await self.redis.set(f"config:{change.component}", change.new_value)
            change.applied = True
            logger.info(f"Config change applied: {change.component}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply config change {change_id}: {e}")
            return False

    async def rollback_change(self, change_id: str) -> bool:
        """Rollback a configuration change."""
        change = self._changes.get(change_id)
        if not change or not change.applied:
            return False

        try:
            backup = await self.redis.get(f"config:backup:{change.component}")
            if backup:
                await self.redis.set(f"config:{change.component}", backup.get("old_value"))
                change.rolled_back = True
                logger.info(f"Config change rolled back: {change.component}")
                return True
        except Exception as e:
            logger.error(f"Rollback failed for {change_id}: {e}")
        return False

    async def validate_change(self, change: ConfigChange) -> bool:
        """Validate a configuration change before applying."""
        # Add schema validation, dependency checks, etc.
        if change.component in ["kernel", "nats", "redis", "postgres"]:
            return True
        return False