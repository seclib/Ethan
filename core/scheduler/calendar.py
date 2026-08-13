"""Core-owned calendar — scheduled events and reminders.

ETHAN Core owns calendar persistence.  The WebUI only renders calendar
events and sends CRUD actions through the API.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class CalendarManager:
    """Own calendar events and reminders."""

    _DOMAIN = "calendar-events"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create(
        self,
        title: str,
        start_time: str,
        end_time: str | None = None,
        description: str = "",
        all_day: bool = False,
        reminders: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a calendar event."""
        event = {
            "id": str(uuid4()),
            "title": title.strip(),
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "all_day": all_day,
            "reminders": list(reminders or []),
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, event["id"], event)
        await self._publish(EventType.SCHEDULE_TRIGGER, "schedule.trigger", {"event": event})
        return event

    async def get(self, event_id: str) -> dict[str, Any] | None:
        """Retrieve a calendar event by id."""
        return await self._store.get(self._DOMAIN, event_id)

    async def list(self) -> list[dict[str, Any]]:
        """List all calendar events."""
        return await self._store.list(self._DOMAIN)

    async def update(self, event_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a calendar event."""
        event = await self.get(event_id)
        if event is None:
            return None
        for key in ("title", "description", "start_time", "end_time", "all_day", "reminders", "metadata"):
            if key in data:
                event[key] = data[key]
        event["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, event_id, event)
        return event

    async def delete(self, event_id: str) -> bool:
        """Delete a calendar event."""
        return await self._store.delete(self._DOMAIN, event_id)

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(subject, Event(type=event_type, source="calendar-manager", payload=payload))
