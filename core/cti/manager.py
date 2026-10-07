"""Core-owned ETHAN-CTI foundation.

This first slice stores a small, user-scoped STIX 2.1 object collection using
the shared CoreRecordStore. It intentionally does not introduce a CTI database,
graph engine, LLM, RAG pipeline, project store, or connector runtime.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN = "cti_stix_objects"
_MAX_OBJECT_BYTES = 1_000_000
_STIX_ID = re.compile(r"^(?P<type>[a-z][a-z0-9-]*)--(?P<uuid>[0-9a-fA-F-]{36})$")
_MANIFEST_PATH = Path(__file__).with_name("manifest.json")


class CTIError(ValueError):
    """Invalid or inaccessible CTI data."""


class CTIManager:
    """Validate, persist and expose minimal STIX 2.1 objects through Core."""

    def __init__(self, store: CoreRecordStore, event_bus: EventBus | None = None) -> None:
        self._store = store
        self._event_bus = event_bus

    @staticmethod
    def manifest() -> dict[str, Any]:
        return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _record_id(owner_id: str, stix_id: str) -> str:
        return f"{owner_id}:{stix_id}"

    @staticmethod
    def _validate_object(stix_object: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(stix_object, dict):
            raise CTIError("A STIX object must be a JSON object")
        if len(json.dumps(stix_object, ensure_ascii=False).encode("utf-8")) > _MAX_OBJECT_BYTES:
            raise CTIError("STIX object exceeds the 1 MB limit")

        object_type = stix_object.get("type")
        if not isinstance(object_type, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", object_type):
            raise CTIError("STIX object type is required")
        spec_version = stix_object.get("spec_version")
        if spec_version not in (None, "2.1"):
            raise CTIError("Only STIX 2.1 objects are supported")

        normalized = dict(stix_object)
        normalized["spec_version"] = "2.1"
        stix_id = normalized.get("id")
        if stix_id is None:
            stix_id = f"{object_type}--{uuid4()}"
            normalized["id"] = stix_id
        match = _STIX_ID.fullmatch(stix_id) if isinstance(stix_id, str) else None
        if match is None or match.group("type") != object_type:
            raise CTIError("STIX id must be '<type>--<UUID>' and match the object type")
        try:
            UUID(match.group("uuid"))
        except ValueError as exc:
            raise CTIError("STIX id must contain a valid UUID") from exc

        if object_type == "relationship":
            for reference in ("relationship_type", "source_ref", "target_ref"):
                if not isinstance(normalized.get(reference), str) or not normalized[reference]:
                    raise CTIError(f"STIX relationship requires {reference}")
        return normalized

    async def list_objects(
        self, owner_id: str, *, object_type: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not owner_id:
            raise CTIError("Authenticated owner is required")
        records = await self._store.list(_DOMAIN)
        owned = [record for record in records if record.get("owner_id") == owner_id]
        if object_type:
            owned = [record for record in owned if record["stix_object"].get("type") == object_type]
        return owned[:limit]

    async def get_object(self, owner_id: str, stix_id: str) -> dict[str, Any] | None:
        if not owner_id:
            raise CTIError("Authenticated owner is required")
        record = await self._store.get(_DOMAIN, self._record_id(owner_id, stix_id))
        return record if record and record.get("owner_id") == owner_id else None

    async def create_object(
        self, owner_id: str, stix_object: dict[str, Any]
    ) -> dict[str, Any]:
        if not owner_id:
            raise CTIError("Authenticated owner is required")
        normalized = self._validate_object(stix_object)
        stix_id = normalized["id"]

        if normalized["type"] == "relationship":
            for reference in (normalized["source_ref"], normalized["target_ref"]):
                if await self.get_object(owner_id, reference) is None:
                    raise CTIError(f"Relationship reference is not available: {reference}")

        record_id = self._record_id(owner_id, stix_id)
        if await self._store.get(_DOMAIN, record_id) is not None:
            raise CTIError(f"STIX object already exists: {stix_id}")

        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": stix_id,
            "owner_id": owner_id,
            "stix_object": normalized,
            "created_at": now,
            "updated_at": now,
        }
        await self._store.save(_DOMAIN, record_id, record)

        if self._event_bus is not None:
            event = Event(
                type=EventType.CTI_OBJECT_CREATED,
                source="core.cti",
                payload={"object_id": stix_id, "object_type": normalized["type"]},
                metadata={"owner_id": owner_id},
            )
            try:
                await self._event_bus.publish("ethan.cti.object.created", event)
            except Exception:
                # Persistence has succeeded; do not report a failed create and
                # invite a duplicate retry when the event bus is temporarily down.
                logger.exception("Could not publish CTI object-created event for %s", stix_id)
        return record
