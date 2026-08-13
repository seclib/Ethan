"""Prompt manager — Core-owned predefined prompts.

Prompt definitions are business records: they must live in Core, not in an
interface.  The manager uses the shared CoreRecordStore so prompts survive
restarts (PostgreSQL) and are cached (Redis), with the same in-process
fallback used by the other Core domains.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

_DOMAIN_PROMPTS = "webui_prompts"


class PromptManager:
    """Store and retrieve predefined prompts."""

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def create(
        self,
        name: str,
        text: str,
        description: str = "",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt_id = str(uuid4())
        record = {
            "id": prompt_id,
            "name": name.strip(),
            "text": text,
            "description": description,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": _utc_now(),
        }
        await self._store.save(_DOMAIN_PROMPTS, prompt_id, record)
        return deepcopy(record)

    async def get(self, prompt_id: str) -> dict[str, Any] | None:
        return await self._store.get(_DOMAIN_PROMPTS, prompt_id)

    async def list(self) -> list[dict[str, Any]]:
        return await self._store.list(_DOMAIN_PROMPTS)

    async def update(self, prompt_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = await self._store.get(_DOMAIN_PROMPTS, prompt_id)
        if record is None:
            return None
        record.update(data)
        record["id"] = prompt_id
        await self._store.save(_DOMAIN_PROMPTS, prompt_id, record)
        return deepcopy(record)

    async def delete(self, prompt_id: str) -> bool:
        return await self._store.delete(_DOMAIN_PROMPTS, prompt_id)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["PromptManager"]