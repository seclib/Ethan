"""Persistent skill store — Core-owned skills records.

ETHAN Core owns skill definitions.  This store is the canonical source of
truth for the **unified Skills model** (fusion of the former in-memory
``SkillRegistry`` pipeline skills and the former prompt-only records):

* ``kind="prompt"``   — the ``content`` is injected as LLM instructions
  (ChatPipeline path, ``POST /skills/{id}/run``).
* ``kind="pipeline"`` — ordered ``steps`` calling tools through the
  ToolManager (SkillExecutor path, ``POST /skills/{id}/execute``).

Both kinds share:

* the activation gate ``is_active`` (consulted by every consumer),
* the tool declaration ``required_tools`` (validated against the
  ToolManager at save time),
* the folder/domain relations (references only — no duplication).

Records persist via ``CoreRecordStore`` (PostgreSQL + Redis cache with
in-memory fallback).  Pre-existing prompt-only records keep working:
missing fields fall back to ``kind="prompt"`` / empty steps.
"""

from __future__ import annotations

from copy import deepcopy
import logging
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_SKILLS = "skills"

#: Allowed skill kinds (the discriminator of the unified model).
SKILL_KINDS = ("prompt", "pipeline")

#: Fields of a skill record a client may write.
_SKILL_FIELDS = (
    "name", "description", "content", "version", "status", "is_active",
    "tags", "meta", "kind", "steps", "required_tools", "valves",
    "author", "is_builtin",
)


def _normalize(record: dict[str, Any]) -> dict[str, Any]:
    """Return the record with every unified-model field defaulted.

    Keeps backward compatibility with pre-fusion prompt-only records.
    """
    record = dict(record)
    record.setdefault("kind", "prompt")
    if record["kind"] not in SKILL_KINDS:
        record["kind"] = "prompt"
    record.setdefault("content", "")
    steps = record.get("steps") or []
    record["steps"] = [dict(s) for s in steps if isinstance(s, dict)]
    tools = record.get("required_tools") or []
    record["required_tools"] = [str(t) for t in tools if t]
    record.setdefault("valves", {})
    record.setdefault("author", "user")
    record.setdefault("is_builtin", False)
    record.setdefault("total_executions", 0)
    record.setdefault("success_count", 0)
    record.setdefault("last_run_at", None)
    record.setdefault("is_active", bool(record.get("status", "active") == "active"))
    return record


class SkillStore:
    """Persistent store for skill definitions (unified model).

    Args:
        store: A shared CoreRecordStore instance (PG durable + Redis cache +
            in-memory fallback).  Created once by the API composition root.
    """

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    # ── CRUD ──────────────────────────────────────────────────────────

    async def list_skills(
        self,
        active: bool | None = None,
        kind: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        """List skills, most recently updated first, with optional filters."""
        skills = [_normalize(s) for s in await self._store.list(_DOMAIN_SKILLS)]
        if active is not None:
            skills = [s for s in skills if bool(s.get("is_active")) is active]
        if kind is not None:
            skills = [s for s in skills if s.get("kind") == kind]
        if tag is not None:
            lowered = tag.lower()
            skills = [
                s for s in skills
                if any(lowered in str(t).lower() for t in s.get("tags", []))
            ]
        return skills

    async def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Retrieve a skill by id (normalized)."""
        record = await self._store.get(_DOMAIN_SKILLS, skill_id)
        return _normalize(record) if record is not None else None

    async def create_skill(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a skill definition (unified model)."""
        kind = data.get("kind", "prompt")
        if kind not in SKILL_KINDS:
            raise ValueError(f"kind invalide : {kind!r} (choix : {', '.join(SKILL_KINDS)})")
        skill_id = str(uuid4())
        now = _utc_now()
        record = _normalize({
            "id": skill_id,
            "name": data.get("name", "unnamed"),
            "description": data.get("description", ""),
            "content": data.get("content", ""),
            "version": data.get("version", "1.0.0"),
            "status": "active",
            "is_active": bool(data.get("is_active", True)),
            "tags": list(data.get("tags", data.get("meta", {}).get("tags", []))),
            "meta": dict(data.get("meta", {})),
            "kind": kind,
            "steps": list(data.get("steps", [])),
            "required_tools": list(data.get("required_tools", [])),
            "valves": dict(data.get("valves", {})),
            "author": data.get("author", "user"),
            "is_builtin": bool(data.get("is_builtin", False)),
            "created_at": now,
            "updated_at": now,
        })
        await self._store.save(_DOMAIN_SKILLS, skill_id, record)
        return deepcopy(record)

    async def update_skill(self, skill_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a skill definition."""
        record = await self._store.get(_DOMAIN_SKILLS, skill_id)
        if record is None:
            return None
        record = _normalize(record)
        if "kind" in data and data["kind"] not in SKILL_KINDS:
            raise ValueError(f"kind invalide : {data['kind']!r} (choix : {', '.join(SKILL_KINDS)})")
        for key in _SKILL_FIELDS:
            if key in data:
                record[key] = data[key]
        record["id"] = skill_id
        record["updated_at"] = _utc_now()
        record = _normalize(record)
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
        record = _normalize(record)
        record["is_active"] = not bool(record.get("is_active", True))
        record["status"] = "active" if record["is_active"] else "inactive"
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_SKILLS, skill_id, record)
        return deepcopy(record)

    # ── Search ────────────────────────────────────────────────────────

    async def search_skills(self, q: str) -> list[dict[str, Any]]:
        """Search skills by name, description or tags."""
        q_lower = q.lower()
        skills = await self.list_skills()
        return [
            s for s in skills
            if q_lower in s.get("name", "").lower()
            or q_lower in s.get("description", "").lower()
            or any(q_lower in str(tag).lower() for tag in s.get("tags", []))
        ]

    # ── Builtins sync (fusion registre mémoire → store persistant) ────

    async def sync_builtin_skills(self, specs: list[dict[str, Any]]) -> int:
        """Upsert idempotent des skills builtin (kind="pipeline").

        Le code des builtins reste la source de vérité de leur
        *définition* (steps, tools) — le store les rend persistantes,
        visibles dans ``/v1/skills`` et associables aux Agents.

        À chaque sync : ``steps``/``required_tools``/``content`` sont
        rafraîchis depuis le code ; ``is_active`` et ``valves`` de
        l'utilisateur sont préservés.
        """
        count = 0
        for spec in specs:
            skill_id = str(spec["id"])
            existing = await self.get_skill(skill_id)
            if existing is None:
                now = _utc_now()
                record = _normalize({**spec, "id": skill_id, "created_at": now, "updated_at": now})
                record["is_builtin"] = True
                record.setdefault("is_active", True)
                await self._store.save(_DOMAIN_SKILLS, skill_id, record)
            else:
                patch = {
                    key: spec[key]
                    for key in ("name", "description", "content", "version", "tags", "kind", "steps", "required_tools")
                    if key in spec
                }
                patch["is_builtin"] = True
                if spec.get("author"):
                    patch["author"] = spec["author"]
                # is_active / valves / meta utilisateur : préservés par update_skill
                await self.update_skill(skill_id, patch)
            count += 1
        return count

    # ── Stats d'exécution ─────────────────────────────────────────────

    async def record_execution(self, skill_id: str, success: bool) -> dict[str, Any] | None:
        """Incrémente les compteurs d'exécution d'une skill."""
        record = await self.get_skill(skill_id)
        if record is None:
            return None
        record["total_executions"] = int(record.get("total_executions", 0)) + 1
        if success:
            record["success_count"] = int(record.get("success_count", 0)) + 1
        record["last_run_at"] = _utc_now()
        await self._store.save(_DOMAIN_SKILLS, skill_id, record)
        return record

    # ── Import / Export (portabilité, pattern Open-WebUI) ─────────────

    async def export_skills(self) -> list[dict[str, Any]]:
        """Exporte toutes les skills (records complets, normalisés)."""
        return await self.list_skills()

    async def import_skills(
        self, records: list[dict[str, Any]] | dict[str, Any]
    ) -> dict[str, Any]:
        """Importe des skills exportées — nouvelles ids, never overwrite.

        Accepte une liste de records ou un export complet
        ``{"skills": [...]}``.  Les enregistrements sans ``name`` sont
        ignorés.  Retourne un résumé ``{imported, skipped}``.
        """
        if isinstance(records, dict):
            records = records.get("skills", [records])
        imported = 0
        skipped = 0
        for raw in records:
            if not isinstance(raw, dict) or not str(raw.get("name", "")).strip():
                skipped += 1
                continue
            payload = {
                key: raw[key]
                for key in _SKILL_FIELDS
                if key in raw and key != "is_builtin"
            }
            try:
                await self.create_skill(payload)
                imported += 1
            except ValueError:
                skipped += 1
        return {"imported": imported, "skipped": skipped}

    # ── Valves (configuration par skill, inspiré Open-WebUI) ──────────

    async def get_valves(self, skill_id: str) -> dict[str, Any] | None:
        """Retourne les valves d'une skill (None si skill inconnue)."""
        record = await self.get_skill(skill_id)
        return None if record is None else dict(record.get("valves", {}))

    async def update_valves(self, skill_id: str, valves: dict[str, Any]) -> dict[str, Any] | None:
        """Remplace les valves d'une skill (retourne les valves à jour)."""
        if not isinstance(valves, dict):
            raise ValueError("Les valves doivent être un objet JSON (dict).")
        updated = await self.update_skill(skill_id, {"valves": valves})
        return None if updated is None else dict(updated.get("valves", {}))


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["SkillStore", "SKILL_KINDS"]
