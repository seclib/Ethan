"""Persistent skill store — Core-owned skills records.

ETHAN Core owns skill definitions.  Historically `/v1/skills` used a duplicated
``webui_skills`` domain inside ``CoreWebUIStore``.  This store is the canonical
replacement: it persists via ``CoreRecordStore`` (PostgreSQL + Redis cache with
in-memory fallback) and exposes the fields required by the Open-WebUI UX
(``content``, ``meta.tags``, ``is_active``) while keeping backward-compatible
fields (``version``, ``status``).
"""

from __future__ import annotations

from copy import deepcopy
import logging
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_SKILLS = "skills"


class SkillStore:
    """Persistent store for skill definitions.

    Args:
        store: A shared CoreRecordStore instance (PG durable + Redis cache +
            in-memory fallback).  Created once by the API composition root.
    """

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    # ── CRUD ──────────────────────────────────────────────────────────

    async def list_skills(self) -> list[dict[str, Any]]:
        """List all skills, most recently updated first."""
        return await self._store.list(_DOMAIN_SKILLS)

    async def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Retrieve a skill by id."""
        return await self._store.get(_DOMAIN_SKILLS, skill_id)

    async def create_skill(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a skill definition."""
        skill_id = str(uuid4())
        now = _utc_now()
        record = {
            "id": skill_id,
            "name": data.get("name", "unnamed"),
            "description": data.get("description", ""),
            "content": data.get("content", ""),
            "version": data.get("version", "1.0.0"),
            "status": "active",
            "is_active": bool(data.get("is_active", True)),
            "tags": list(data.get("tags", data.get("meta", {}).get("tags", []))),
            "meta": dict(data.get("meta", {})),
            "created_at": now,
            "updated_at": now,
        }
        await self._store.save(_DOMAIN_SKILLS, skill_id, record)
        return deepcopy(record)

    async def update_skill(self, skill_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a skill definition."""
        record = await self._store.get(_DOMAIN_SKILLS, skill_id)
        if record is None:
            return None
        for key in ("name", "description", "content", "version", "status", "is_active", "tags", "meta"):
            if key in data:
                record[key] = data[key]
        record["id"] = skill_id
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_SKILLS, skill_id, record)
        return deepcopy(record)

    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill definition."""
        return await self._store.delete(_DOMAIN_SKILLS, skill_id)

    async def toggle_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Toggle the active state of a skill."""
        record = await self._store.get(_DOMAIN_SKILLS, skill_id)
        if record is None:
            return None
        record["is_active"] = not bool(record.get("is_active", True))
        record["status"] = "active" if record["is_active"] else "inactive"
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_SKILLS, skill_id, record)
        return deepcopy(record)

    # ── Search ────────────────────────────────────────────────────────

    async def search_skills(self, q: str) -> list[dict[str, Any]]:
        """Search skills by name, description or tags."""
        q_lower = q.lower()
        skills = await self._store.list(_DOMAIN_SKILLS)
        return [
            s for s in skills
            if q_lower in s.get("name", "").lower()
            or q_lower in s.get("description", "").lower()
            or any(q_lower in str(tag).lower() for tag in s.get("tags", []))
        ]


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["SkillStore"]