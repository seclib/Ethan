"""Core-owned automation engine — rules, triggers, actions."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class AutomationManager:
    """Own automation rules, triggers and scheduled actions."""

    _DOMAIN = "automations"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create(
        self,
        name: str,
        trigger: dict[str, Any],
        actions: list[dict[str, Any]],
        description: str = "",
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new automation rule."""
        rule = {
            "id": str(uuid4()),
            "name": name.strip(),
            "description": description,
            "trigger": trigger,
            "actions": list(actions),
            "enabled": enabled,
            "last_triggered_at": None,
            "trigger_count": 0,
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, rule["id"], rule)
        await self._publish(EventType.AUTOMATION_CREATED, "automation.created", {"rule": rule})
        return rule

    async def get(self, rule_id: str) -> dict[str, Any] | None:
        """Retrieve an automation rule by id."""
        return await self._store.get(self._DOMAIN, rule_id)

    async def list(self, enabled: bool | None = None) -> list[dict[str, Any]]:
        """List automation rules, optionally filtered by enabled state."""
        rules = await self._store.list(self._DOMAIN)
        if enabled is not None:
            rules = [r for r in rules if r.get("enabled") == enabled]
        return rules

    async def update(self, rule_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update an automation rule."""
        rule = await self.get(rule_id)
        if rule is None:
            return None
        for key in ("name", "description", "trigger", "actions", "enabled", "metadata"):
            if key in data:
                rule[key] = data[key]
        rule["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, rule_id, rule)
        await self._publish(EventType.AUTOMATION_UPDATED, "automation.updated", {"rule_id": rule_id})
        return rule

    async def delete(self, rule_id: str) -> bool:
        """Delete an automation rule."""
        existed = await self._store.delete(self._DOMAIN, rule_id)
        if existed:
            await self._publish(EventType.AUTOMATION_DELETED, "automation.deleted", {"rule_id": rule_id})
        return existed

    async def trigger(self, rule_id: str) -> dict[str, Any] | None:
        """Manually trigger an automation rule."""
        rule = await self.get(rule_id)
        if rule is None or not rule.get("enabled"):
            return None
        rule["last_triggered_at"] = datetime.utcnow().isoformat()
        rule["trigger_count"] = rule.get("trigger_count", 0) + 1
        await self._store.save(self._DOMAIN, rule_id, rule)
        await self._publish(
            EventType.AUTOMATION_TRIGGERED,
            "automation.triggered",
            {"rule_id": rule_id, "actions": rule["actions"]},
        )
        return rule

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="automation-manager", payload=payload))
