"""Memory Agent — Gestion de la mémoire persistante"""

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.events import Event

logger = logging.getLogger(__name__)


class MemoryAgent(Agent):
    """Agent spécialisé dans la gestion de la mémoire persistante."""

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="memory",
            description="Gestion de la mémoire persistante et vectorielle",
            **kwargs
        )
        super().__init__(config)

    async def _subscribe_events(self) -> None:
        self.bus.subscribe("memory:store", self._handle_store)
        self.bus.subscribe("memory:retrieve", self._handle_retrieve)
        self.bus.subscribe("memory:search", self._handle_search)

    async def _handle_store(self, event: Event) -> None:
        result = await self.run({"action": "store", **event.data})
        await self.publish("memory:stored", result)

    async def _handle_retrieve(self, event: Event) -> None:
        result = await self.run({"action": "retrieve", **event.data})
        await self.publish("memory:retrieved", result)

    async def _handle_search(self, event: Event) -> None:
        result = await self.run({"action": "search", **event.data})
        await self.publish("memory:searched", result)

    async def run(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        data = input_data or {}
        action = data.get("action", "store")
        key = data.get("key", "")
        value = data.get("value", "")
        namespace = data.get("namespace", "default")
        query = data.get("query", "")

        if action == "store":
            prompt = f"""Summarize this information for memory storage:
Key: {key}
Value: {value}
Namespace: {namespace}
Provide a concise summary (max 200 words)."""
            summary = await self.think(prompt)
            return {"action": "store", "key": key, "summary": summary, "namespace": namespace}

        elif action == "retrieve":
            return {"action": "retrieve", "key": key, "namespace": namespace}

        elif action == "search":
            prompt = f"""Analyze this search query and extract key concepts:
Query: {query}
Namespace: {namespace}
Provide search keywords and expected result type."""
            analysis = await self.think(prompt)
            return {"action": "search", "query": query, "analysis": analysis, "namespace": namespace}

        return {"action": action, "status": "unknown_action"}