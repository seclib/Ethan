"""WebUI domain store — persistent, Core-owned records for WebUI-facing domains.

Historically `interfaces/api/routers/v1.py` kept goals, facts, skills, events,
settings, providers and plugins in a process-local `MemoryStore`.  That logic
belonged to the interface, which violates the ETHAN architecture rule: all
business state must live in Core or Runtime.

This store moves those records into the Core persistence boundary
(`CoreRecordStore`) so they survive restarts (PostgreSQL) and are cached
(Redis), with the same in-process fallback used by agents, missions,
knowledge and RAG.  The v1 router becomes a thin HTTP gateway over this
store — no business logic of its own.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any
from uuid import uuid4

from .record_store import CoreRecordStore

logger = logging.getLogger(__name__)

# Record domains in the shared CoreRecordStore.
_DOMAIN_GOALS = "webui_goals"
_DOMAIN_FACTS = "webui_facts"
_DOMAIN_EVENTS = "webui_events"
_DOMAIN_CHAT = "webui_chat"
_DOMAIN_SETTINGS = "webui_settings"
_DOMAIN_PROVIDERS = "webui_providers"
_DOMAIN_PLUGINS = "webui_plugins"


class CoreWebUIStore:
    """Core-owned store for WebUI-facing records.

    Args:
        store: A shared CoreRecordStore instance (PG durable + Redis cache +
            in-memory fallback).  Created once by the API composition root.
    """

    def __init__(self, store: CoreRecordStore) -> None:
        self._store = store

    # ── Goals ──────────────────────────────────────────────────────────

    async def list_goals(self) -> list[dict[str, Any]]:
        return await self._store.list(_DOMAIN_GOALS)

    async def get_goal(self, goal_id: str) -> dict[str, Any] | None:
        return await self._store.get(_DOMAIN_GOALS, goal_id)

    async def create_goal(
        self,
        *,
        title: str,
        description: str = "",
        priority: str = "normal",
    ) -> dict[str, Any]:
        goal_id = str(uuid4())
        now = _utc_now()
        record = {
            "id": goal_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "created_at": now,
        }
        await self._store.save(_DOMAIN_GOALS, goal_id, record)
        return deepcopy(record)

    async def update_goal(self, goal_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = await self._store.get(_DOMAIN_GOALS, goal_id)
        if record is None:
            return None
        record.update(data)
        record["id"] = goal_id
        await self._store.save(_DOMAIN_GOALS, goal_id, record)
        return deepcopy(record)

    async def delete_goal(self, goal_id: str) -> bool:
        return await self._store.delete(_DOMAIN_GOALS, goal_id)

    # ── Facts ──────────────────────────────────────────────────────────

    async def list_facts(self, category: str | None = None) -> list[dict[str, Any]]:
        facts = await self._store.list(_DOMAIN_FACTS)
        if category:
            facts = [f for f in facts if f.get("category") == category]
        return facts

    async def get_fact(self, fact_id: str) -> dict[str, Any] | None:
        return await self._store.get(_DOMAIN_FACTS, fact_id)

    async def search_facts(self, q: str) -> list[dict[str, Any]]:
        q_lower = q.lower()
        facts = await self._store.list(_DOMAIN_FACTS)
        return [
            f for f in facts
            if q_lower in f.get("subject", "").lower()
            or q_lower in f.get("predicate", "").lower()
            or q_lower in f.get("object", "").lower()
        ]

    async def create_fact(self, data: dict[str, Any]) -> dict[str, Any]:
        fact_id = str(uuid4())
        record = {
            "id": fact_id,
            "subject": data.get("subject", ""),
            "predicate": data.get("predicate", ""),
            "object": data.get("object", ""),
            "category": data.get("category", "knowledge"),
            "confidence": data.get("confidence", 0.5),
            "created_at": _utc_now(),
            **{k: v for k, v in data.items() if k not in {"subject", "predicate", "object", "category", "confidence"}},
        }
        await self._store.save(_DOMAIN_FACTS, fact_id, record)
        return deepcopy(record)

    # ── Events (Flux) ──────────────────────────────────────────────────

    async def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        event_id = str(uuid4())
        record = {
            "id": event_id,
            "type": event.get("type", "event"),
            "content": event.get("content", ""),
            "metadata": event.get("metadata", {}),
            "timestamp": _utc_now(),
        }
        await self._store.save(_DOMAIN_EVENTS, event_id, record)
        return deepcopy(record)

    async def list_events(self, type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        events = await self._store.list(_DOMAIN_EVENTS)
        if type:
            events = [e for e in events if e.get("type") == type]
        return list(reversed(events[-limit:]))

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        return await self._store.get(_DOMAIN_EVENTS, event_id)

    async def search_memory(self, q: str) -> list[dict[str, Any]]:
        q_lower = q.lower()
        results: list[dict[str, Any]] = []
        events = await self._store.list(_DOMAIN_EVENTS)
        for ev in events:
            if q_lower in str(ev).lower():
                results.append(ev)
        facts = await self._store.list(_DOMAIN_FACTS)
        for f in facts:
            if q_lower in str(f).lower():
                results.append(f)
        return results[:50]

    async def get_memory_entry(self, memory_id: str) -> dict[str, Any] | None:
        event = await self._store.get(_DOMAIN_EVENTS, memory_id)
        if event is None:
            event = await self._store.get(_DOMAIN_FACTS, memory_id)
        return event

    # ── Chat messages ──────────────────────────────────────────────────

    async def append_chat_message(self, message: dict[str, Any]) -> dict[str, Any]:
        message_id = str(uuid4())
        record: dict[str, Any] = {
            "id": message_id,
            "role": message.get("role", ""),
            "content": message.get("content", message.get("message", "")),
            "timestamp": _utc_now(),
            "metadata": message.get("metadata", {}),
        }
        # Preserve extra fields (e.g. "message" used by /v1/chat responses)
        # while never overriding the canonical fields above.
        for key, value in message.items():
            if key not in {"role", "content", "message", "timestamp", "metadata"}:
                record[key] = value
        await self._store.save(_DOMAIN_CHAT, message_id, record)
        return deepcopy(record)

    async def list_chat_messages(self, limit: int = 50) -> list[dict[str, Any]]:
        messages = await self._store.list(_DOMAIN_CHAT)
        return list(reversed(messages[-limit:]))

    # ── Settings ───────────────────────────────────────────────────────

    _DEFAULT_SETTINGS: dict[str, Any] = {
        "llm": {"provider": "openai", "model": "gpt-4", "temperature": 0.7},
        "permissions": {"allow_autonomy": False, "allow_network": True},
        "budget": {"daily_limit_usd": 10.0, "alert_threshold": 0.8},
        "system": {"log_level": "INFO", "max_workers": 4},
    }

    async def get_settings(self) -> dict[str, Any]:
        record = await self._store.get(_DOMAIN_SETTINGS, "default")
        if record is not None:
            # Merge to absorb new default keys across upgrades.
            merged = deepcopy(self._DEFAULT_SETTINGS)
            merged.update(record)
            return merged
        return deepcopy(self._DEFAULT_SETTINGS)

    async def update_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        current = await self.get_settings()
        current.update(data)
        await self._store.save(_DOMAIN_SETTINGS, "default", current)
        return deepcopy(current)

    # ── Providers ──────────────────────────────────────────────────────

    _DEFAULT_PROVIDERS: list[dict[str, Any]] = [
        {"id": "openai", "name": "OpenAI", "type": "LLM", "status": "connected", "configured": True},
        {"id": "anthropic", "name": "Anthropic", "type": "LLM", "status": "connected", "configured": True},
        {"id": "huggingface", "name": "HuggingFace", "type": "LLM", "status": "disconnected", "configured": False},
        {"id": "pinecone", "name": "Pinecone", "type": "VectorDB", "status": "connected", "configured": True},
    ]

    async def list_providers(self) -> list[dict[str, Any]]:
        records = await self._store.list(_DOMAIN_PROVIDERS)
        if not records:
            # Seed defaults once on first access (idempotent).
            for idx, provider in enumerate(self._DEFAULT_PROVIDERS):
                await self._store.save(_DOMAIN_PROVIDERS, provider["id"], provider)
            return deepcopy(self._DEFAULT_PROVIDERS)
        return records

    async def get_provider(self, provider_id: str) -> dict[str, Any] | None:
        record = await self._store.get(_DOMAIN_PROVIDERS, provider_id)
        if record is not None:
            return record
        # Fall back to the static defaults for backward compatibility.
        for provider in self._DEFAULT_PROVIDERS:
            if provider["id"] == provider_id:
                return deepcopy(provider)
        return None

    async def update_provider(self, provider_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        record = await self._store.get(_DOMAIN_PROVIDERS, provider_id)
        if record is None:
            # Create from defaults if it is a known default.
            known = None
            for provider in self._DEFAULT_PROVIDERS:
                if provider["id"] == provider_id:
                    known = deepcopy(provider)
                    break
            record = known
            if record is None:
                return None
        record.update(data)
        record["id"] = provider_id
        await self._store.save(_DOMAIN_PROVIDERS, provider_id, record)
        return deepcopy(record)

    # ── Plugins ────────────────────────────────────────────────────────

    _DEFAULT_PLUGINS: list[dict[str, Any]] = [
        {"id": "github", "name": "GitHub Integration", "status": "active", "version": "1.0.0"},
        {"id": "slack", "name": "Slack Notifier", "status": "inactive", "version": "1.2.0"},
    ]

    async def list_plugins(self) -> list[dict[str, Any]]:
        records = await self._store.list(_DOMAIN_PLUGINS)
        if not records:
            for plugin in self._DEFAULT_PLUGINS:
                await self._store.save(_DOMAIN_PLUGINS, plugin["id"], plugin)
            return deepcopy(self._DEFAULT_PLUGINS)
        return records

    async def get_plugin(self, plugin_id: str) -> dict[str, Any] | None:
        record = await self._store.get(_DOMAIN_PLUGINS, plugin_id)
        if record is not None:
            return record
        for plugin in self._DEFAULT_PLUGINS:
            if plugin["id"] == plugin_id:
                return deepcopy(plugin)
        return None

    async def install_plugin(self, data: dict[str, Any]) -> dict[str, Any]:
        plugin_id = data.get("id") or str(uuid4())
        record = {
            "id": plugin_id,
            "name": data.get("name", "Unknown Plugin"),
            "status": "inactive",
            "version": "0.1.0",
        }
        await self._store.save(_DOMAIN_PLUGINS, plugin_id, record)
        return deepcopy(record)

    async def toggle_plugin(self, plugin_id: str) -> dict[str, Any] | None:
        record = await self._store.get(_DOMAIN_PLUGINS, plugin_id)
        if record is None:
            for plugin in self._DEFAULT_PLUGINS:
                if plugin["id"] == plugin_id:
                    record = deepcopy(plugin)
                    break
        if record is None:
            return None
        record["status"] = "active" if record.get("status") == "inactive" else "inactive"
        record["id"] = plugin_id
        await self._store.save(_DOMAIN_PLUGINS, plugin_id, record)
        return deepcopy(record)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["CoreWebUIStore"]