"""Core-owned evaluation engine — model and agent evaluations.

ETHAN Core owns evaluation logic.  The WebUI only renders evaluation
results and sends run requests through the API.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class EvaluationManager:
    """Own evaluation definitions and results."""

    _DOMAIN = "evaluations"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def create(
        self,
        name: str,
        criteria: list[dict[str, Any]],
        target: str = "",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new evaluation definition."""
        evaluation = {
            "id": str(uuid4()),
            "name": name.strip(),
            "description": description,
            "target": target,
            "criteria": list(criteria),
            "results": [],
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, evaluation["id"], evaluation)
        return evaluation

    async def get(self, eval_id: str) -> dict[str, Any] | None:
        """Retrieve an evaluation by id."""
        return await self._store.get(self._DOMAIN, eval_id)

    async def list(self) -> list[dict[str, Any]]:
        """List all evaluations."""
        return await self._store.list(self._DOMAIN)

    async def add_result(self, eval_id: str, result: dict[str, Any]) -> dict[str, Any] | None:
        """Append a result to an evaluation."""
        evaluation = await self.get(eval_id)
        if evaluation is None:
            return None
        result["timestamp"] = datetime.utcnow().isoformat()
        evaluation["results"].append(result)
        evaluation["updated_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, eval_id, evaluation)
        return evaluation
