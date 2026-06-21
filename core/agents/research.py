"""Research Agent — Recherche et synthèse d'information"""

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.events import Event

logger = logging.getLogger(__name__)


class ResearchAgent(Agent):
    """Agent spécialisé dans la recherche et la synthèse d'information.

    Effectue des recherches web, analyse des documents et synthétise l'information.
    """

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="research",
            description="Recherche et synthèse d'information",
            **kwargs
        )
        super().__init__(config)

    async def _subscribe_events(self) -> None:
        self.bus.subscribe("research:query", self._handle_research_query)

    async def _handle_research_query(self, event: Event) -> None:
        query = event.data.get("query", "")
        depth = event.data.get("depth", "basic")
        result = await self.run({"query": query, "depth": depth})
        await self.publish("research:result", result)

    async def run(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        query = (input_data or {}).get("query", "")
        depth = (input_data or {}).get("depth", "basic")

        prompt = f"""Research the following topic and provide a comprehensive summary.

Query: {query}
Depth: {depth}

Provide:
1. Key findings
2. Sources and references
3. Main arguments
4. Conclusions"""

        response = await self.think(prompt)

        return {
            "query": query,
            "depth": depth,
            "result": response,
            "status": "completed",
        }