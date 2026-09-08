"""Reminders — Core-owned reminder system.

Uses the ETHAN Scheduler for timing. Supports:
- create / edit / delete
- enable / disable
- cron scheduling with timezone
- one-shot reminders at a specific datetime

Never creates a browser-only scheduler — all timing is Core-owned.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

__all__ = ["ReminderManager"]

_DOMAIN = "reminders"


class ReminderManager:
    """Own reminders with scheduling, timezone, and enable/disable."""

    def __init__(
        self,
        store: CoreRecordStore | None = None,
        event_bus: EventBus | None = None,
        scheduler: Any = None,
    ) -> None:
        self._store = store or CoreRecordStore()
        self._bus = event_bus
        self._scheduler = scheduler

    async def create(
        self,
        title: str,
        *,
        schedule: str | None = None,
        fire_at: str | None = None,
        timezone: str = "UTC",
        message: str = "",
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a reminder.

        Args:
            title: Reminder title.
            schedule: Cron expression (5-field) for recurring reminders.
            fire_at: ISO datetime for one-shot reminders.
            timezone: IANA timezone for cron scheduling.
            message: Optional reminder message.
            enabled: Whether the reminder is active.
            metadata: Optional metadata.
        """
        if schedule and fire_at:
            raise ValueError("Cannot specify both schedule and fire_at")
        if not schedule and not fire_at:
            raise ValueError("Must specify either schedule or fire_at")

        reminder = {
            "id": str(uuid4()),
            "title": title.strip(),
            "message": message,
            "schedule": schedule,
            "fire_at": fire_at,
            "timezone": timezone,
            "enabled": enabled,
            "last_fired_at": None,
            "fire_count": 0,
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(_DOMAIN, reminder["id"], reminder)

        if enabled and self._scheduler is not None:
            await self._schedule_reminder(reminder)

        await self._publish(EventType.SCHEDULE_TRIGGER, "reminder.created", {"reminder": reminder})
        return reminder

    async def get(self, reminder_id: str) -> dict[str, Any] | None:
        """Get a reminder by id."""
        return await self._store.get(_DOMAIN, reminder_id)

    async def list(self, enabled: bool | None = None) -> list[dict[str, Any]]:
        """List reminders, optionally filtered by enabled state."""
        reminders = await self._store.list(_DOMAIN)
        if enabled is not None:
            reminders = [r for r in reminders if r.get("enabled") == enabled]
        return reminders

    async def update(self, reminder_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a reminder."""
        reminder = await self.get(reminder_id)
        if reminder is None:
            return None

        for key in ("title", "message", "schedule", "fire_at", "timezone", "enabled", "metadata"):
            if key in data:
                reminder[key] = data[key]
        reminder["updated_at"] = datetime.utcnow().isoformat()

        await self._store.save(_DOMAIN, reminder_id, reminder)

        # Reschedule if timing-related fields changed
        if self._scheduler is not None:
            await self._scheduler.cancel(f"reminder-{reminder_id}")
            if reminder.get("enabled"):
                await self._schedule_reminder(reminder)

        await self._publish(EventType.SCHEDULE_TRIGGER, "reminder.updated", {"reminder_id": reminder_id})
        return reminder

    async def delete(self, reminder_id: str) -> bool:
        """Delete a reminder and cancel its schedule."""
        existed = await self._store.delete(_DOMAIN, reminder_id)
        if existed and self._scheduler is not None:
            await self._scheduler.cancel(f"reminder-{reminder_id}")
        if existed:
            await self._publish(EventType.SCHEDULE_TRIGGER, "reminder.deleted", {"reminder_id": reminder_id})
        return existed

    async def enable(self, reminder_id: str) -> dict[str, Any] | None:
        """Enable a reminder."""
        return await self.update(reminder_id, {"enabled": True})

    async def disable(self, reminder_id: str) -> dict[str, Any] | None:
        """Disable a reminder."""
        return await self.update(reminder_id, {"enabled": False})

    async def fire(self, reminder_id: str) -> dict[str, Any] | None:
        """Manually fire a reminder (triggers the event)."""
        reminder = await self.get(reminder_id)
        if reminder is None:
            return None
        reminder["last_fired_at"] = datetime.utcnow().isoformat()
        reminder["fire_count"] = reminder.get("fire_count", 0) + 1
        await self._store.save(_DOMAIN, reminder_id, reminder)
        await self._publish(
            EventType.SCHEDULE_TRIGGER,
            "reminder.fired",
            {"reminder_id": reminder_id, "title": reminder["title"], "message": reminder.get("message", "")},
        )
        return reminder

    async def _schedule_reminder(self, reminder: dict[str, Any]) -> None:
        """Register the reminder with the scheduler."""
        if self._scheduler is None:
            return
        name = f"reminder-{reminder['id']}"
        payload = {"reminder_id": reminder["id"], "title": reminder["title"], "message": reminder.get("message", "")}
        if reminder.get("schedule"):
            await self._scheduler.schedule_cron(
                name=name,
                cron_expr=reminder["schedule"],
                topic="reminder.fired",
                payload=payload,
                tz=reminder.get("timezone", "UTC"),
            )
        elif reminder.get("fire_at"):
            try:
                fire_at = datetime.fromisoformat(reminder["fire_at"])
                await self._scheduler.schedule_once(
                    name=name,
                    fire_at=fire_at,
                    topic="reminder.fired",
                    payload=payload,
                )
            except (ValueError, TypeError) as exc:
                logger.error(f"Invalid fire_at for reminder {reminder['id']}: {exc}")

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="reminder-manager", payload=payload))
