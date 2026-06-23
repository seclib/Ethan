"""Module Registry — Discover modules via NATS heartbeat + PostgreSQL."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from kernel.bus.interface import EventBus
from kernel.state.postgres_state import PostgresPersistentState
from kernel.state.redis_state import RedisLiveState
from sdk.event import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class ModuleManifest:
    """Identity and capabilities declaration for a cognitive module."""
    id: str
    name: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    topics_subscribed: List[str] = field(default_factory=list)
    topics_published: List[str] = field(default_factory=list)
    status: str = "active"
    last_heartbeat: Optional[str] = None


class ModuleRegistry:
    """Discovers, registers, and monitors cognitive modules."""

    def __init__(
        self,
        bus: EventBus,
        pg: PostgresPersistentState,
        redis: RedisLiveState,
    ):
        self.bus = bus
        self.pg = pg
        self.redis = redis
        self._modules: Dict[str, ModuleManifest] = {}

    async def discover(self) -> List[ModuleManifest]:
        """Discover modules from PostgreSQL registry."""
        try:
            rows = await self.pg.execute(
                "SELECT * FROM modules WHERE status = 'active'"
            )
            for row in rows:
                manifest = ModuleManifest(
                    id=row["id"],
                    name=row["name"],
                    version=row["version"],
                    capabilities=row.get("capabilities", []),
                    topics_subscribed=row.get("topics_subscribed", []),
                    topics_published=row.get("topics_published", []),
                    status=row.get("status", "active"),
                )
                self._modules[manifest.id] = manifest
            logger.info(f"Discovered {len(rows)} modules from PostgreSQL")
        except Exception as e:
            logger.warning(f"Module discovery failed: {e}")
        return list(self._modules.values())

    async def register(self, manifest: ModuleManifest) -> None:
        """Register a module (from heartbeat or API)."""
        self._modules[manifest.id] = manifest
        await self.pg.insert("modules", {
            "id": manifest.id,
            "name": manifest.name,
            "version": manifest.version,
            "capabilities": manifest.capabilities,
            "topics_subscribed": manifest.topics_subscribed,
            "topics_published": manifest.topics_published,
            "status": "active",
        })
        await self.bus.publish(EventType.SYSTEM_MODULE_REGISTERED, Event(
            type=EventType.SYSTEM_MODULE_REGISTERED,
            source="registry",
            data={"module_id": manifest.id, "capabilities": manifest.capabilities},
        ))
        logger.info(f"Module registered: {manifest.id} v{manifest.version}")

    async def unregister(self, module_id: str) -> None:
        """Mark module as inactive."""
        if module_id in self._modules:
            del self._modules[module_id]
        await self.pg.execute(
            "UPDATE modules SET status = 'inactive' WHERE id = $1", module_id
        )
        await self.bus.publish(EventType.SYSTEM_MODULE_UNREGISTERED, Event(
            type=EventType.SYSTEM_MODULE_UNREGISTERED,
            source="registry",
            data={"module_id": module_id},
        ))
        logger.info(f"Module unregistered: {module_id}")

    async def health_check(self, module_id: str) -> bool:
        """Check if module is alive via Redis heartbeat."""
        return await self.redis.exists(f"module:{module_id}:heartbeat")

    def find_by_capability(self, capability: str) -> List[ModuleManifest]:
        """Find modules that provide a specific capability."""
        return [
            m for m in self._modules.values()
            if capability in m.capabilities
        ]

    def get(self, module_id: str) -> Optional[ModuleManifest]:
        """Get module by ID."""
        return self._modules.get(module_id)

    def list_modules(self) -> List[ModuleManifest]:
        """List all registered modules."""
        return list(self._modules.values())