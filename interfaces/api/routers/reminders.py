"""Reminders Router — Core-owned reminder system.

The Core owns scheduling logic. This router only delegates to ReminderManager.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.auth import Permission
from core.reminders import ReminderManager
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reminders", tags=["reminders"])

_manager: ReminderManager | None = None


def set_reminder_manager(manager: ReminderManager) -> None:
    global _manager
    _manager = manager


def get_reminder_manager() -> ReminderManager:
    if _manager is None:
        raise HTTPException(503, "Reminder manager not initialized")
    return _manager


@router.get("", dependencies=[Depends(require_permission(Permission.READ))])
async def list_reminders(enabled: bool | None = None) -> list[dict[str, Any]]:
    """List reminders."""
    manager = get_reminder_manager()
    return await manager.list(enabled=enabled)


@router.get("/{reminder_id}", dependencies=[Depends(require_permission(Permission.READ))])
async def get_reminder(reminder_id: str) -> dict[str, Any]:
    """Get a reminder by id."""
    manager = get_reminder_manager()
    reminder = await manager.get(reminder_id)
    if reminder is None:
        raise HTTPException(404, f"Reminder {reminder_id} not found")
    return reminder


@router.post("", status_code=201, dependencies=[Depends(require_permission(Permission.WRITE))])
async def create_reminder(data: dict[str, Any]) -> dict[str, Any]:
    """Create a reminder."""
    manager = get_reminder_manager()
    try:
        return await manager.create(
            title=data.get("title", ""),
            schedule=data.get("schedule"),
            fire_at=data.get("fire_at"),
            timezone=data.get("timezone", "UTC"),
            message=data.get("message", ""),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.put("/{reminder_id}", dependencies=[Depends(require_permission(Permission.WRITE))])
async def update_reminder(reminder_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Update a reminder."""
    manager = get_reminder_manager()
    reminder = await manager.update(reminder_id, data)
    if reminder is None:
        raise HTTPException(404, f"Reminder {reminder_id} not found")
    return reminder


@router.delete("/{reminder_id}", dependencies=[Depends(require_permission(Permission.WRITE))])
async def delete_reminder(reminder_id: str) -> dict[str, Any]:
    """Delete a reminder."""
    manager = get_reminder_manager()
    existed = await manager.delete(reminder_id)
    if not existed:
        raise HTTPException(404, f"Reminder {reminder_id} not found")
    return {"status": "deleted", "reminder_id": reminder_id}


@router.post("/{reminder_id}/enable", dependencies=[Depends(require_permission(Permission.WRITE))])
async def enable_reminder(reminder_id: str) -> dict[str, Any]:
    """Enable a reminder."""
    manager = get_reminder_manager()
    reminder = await manager.enable(reminder_id)
    if reminder is None:
        raise HTTPException(404, f"Reminder {reminder_id} not found")
    return reminder


@router.post("/{reminder_id}/disable", dependencies=[Depends(require_permission(Permission.WRITE))])
async def disable_reminder(reminder_id: str) -> dict[str, Any]:
    """Disable a reminder."""
    manager = get_reminder_manager()
    reminder = await manager.disable(reminder_id)
    if reminder is None:
        raise HTTPException(404, f"Reminder {reminder_id} not found")
    return reminder


@router.post("/{reminder_id}/fire", dependencies=[Depends(require_permission(Permission.WRITE))])
async def fire_reminder(reminder_id: str) -> dict[str, Any]:
    """Manually fire a reminder."""
    manager = get_reminder_manager()
    reminder = await manager.fire(reminder_id)
    if reminder is None:
        raise HTTPException(404, f"Reminder {reminder_id} not found")
    return reminder
