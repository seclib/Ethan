"""Developer Agent — Génération et analyse de code"""

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.events import Event

logger = logging.getLogger(__name__)


class DeveloperAgent(Agent):
    """Agent spécialisé dans la génération et l'analyse de code."""

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="developer",
            description="Génération et analyse de code",
            **kwargs
        )
        super().__init__(config)

    async def _subscribe_events(self) -> None:
        self.bus.subscribe("dev:generate", self._handle_generate)
        self.bus.subscribe("dev:review", self._handle_review)

    async def _handle_generate(self, event: Event) -> None:
        result = await self.run({"task": "generate", **event.data})
        await self.publish("dev:generated", result)

    async def _handle_review(self, event: Event) -> None:
        result = await self.run({"task": "review", **event.data})
        await self.publish("dev:reviewed", result)

    async def run(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        data = input_data or {}
        task = data.get("task", "generate")
        language = data.get("language", "python")
        specification = data.get("specification", "")

        if task == "generate":
            prompt = f"""Generate {language} code for the following specification:

{specification}

Provide:
1. Complete code
2. Dependencies
3. Usage example
4. Error handling"""
        else:
            code = data.get("code", "")
            prompt = f"""Review this {language} code:

{code}

Provide:
1. Code quality assessment
2. Potential bugs
3. Performance issues
4. Security concerns
5. Improvement suggestions"""

        response = await self.think(prompt)
        return {"task": task, "language": language, "result": response}