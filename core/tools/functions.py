"""Core-owned function/pipeline management — reusable tool functions.

ETHAN Core owns function definitions and pipeline composition.  The WebUI
only renders the function list and sends execution requests through the API.
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


class FunctionManager:
    """Own function definitions and pipeline composition."""

    _DOMAIN = "functions"
    _PIPELINES_DOMAIN = "pipelines"

    def __init__(
        self,
        event_bus: EventBus | None = None,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._bus = event_bus
        self._store = store or CoreRecordStore()

    async def create_function(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        code: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new function definition."""
        func = {
            "id": str(uuid4()),
            "name": name.strip(),
            "description": description,
            "parameters": parameters,
            "code": code,
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, func["id"], func)
        return func

    async def get_function(self, func_id: str) -> dict[str, Any] | None:
        """Retrieve a function by id."""
        return await self._store.get(self._DOMAIN, func_id)

    async def list_functions(self) -> list[dict[str, Any]]:
        """List all functions."""
        return await self._store.list(self._DOMAIN)

    async def delete_function(self, func_id: str) -> bool:
        """Delete a function."""
        return await self._store.delete(self._DOMAIN, func_id)

    async def create_pipeline(
        self,
        name: str,
        steps: list[dict[str, Any]],
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new pipeline (ordered function composition)."""
        pipeline = {
            "id": str(uuid4()),
            "name": name.strip(),
            "description": description,
            "steps": list(steps),
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._PIPELINES_DOMAIN, pipeline["id"], pipeline)
        return pipeline

    async def get_pipeline(self, pipeline_id: str) -> dict[str, Any] | None:
        """Retrieve a pipeline by id."""
        return await self._store.get(self._PIPELINES_DOMAIN, pipeline_id)

    async def list_pipelines(self) -> list[dict[str, Any]]:
        """List all pipelines."""
        return await self._store.list(self._PIPELINES_DOMAIN)

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline."""
        return await self._store.delete(self._PIPELINES_DOMAIN, pipeline_id)
