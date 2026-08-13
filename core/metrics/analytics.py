"""Core-owned analytics — usage metrics, cost tracking, telemetry.

ETHAN Core owns analytics.  The WebUI only renders dashboards and sends
query requests through the API.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """Own usage metrics, cost tracking and telemetry events."""

    _DOMAIN = "analytics"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def record_event(
        self,
        event_type: str,
        user_id: str = "anonymous",
        provider: str | None = None,
        model: str | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a usage analytics event."""
        event = {
            "id": str(uuid4()),
            "event_type": event_type,
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "metadata": dict(metadata or {}),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._DOMAIN, event["id"], event)
        return event

    async def list_events(
        self,
        user_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List analytics events, optionally filtered."""
        events = await self._store.list(self._DOMAIN)
        if user_id is not None:
            events = [e for e in events if e.get("user_id") == user_id]
        if provider is not None:
            events = [e for e in events if e.get("provider") == provider]
        if model is not None:
            events = [e for e in events if e.get("model") == model]
        events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return events[:limit]

    async def get_usage_summary(self, user_id: str | None = None) -> dict[str, Any]:
        """Return a usage summary (total tokens, total cost)."""
        events = await self.list_events(user_id=user_id, limit=10000)
        total_tokens = sum(e.get("tokens_in", 0) + e.get("tokens_out", 0) for e in events)
        total_cost = sum(e.get("cost", 0.0) for e in events)
        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "event_count": len(events),
        }
