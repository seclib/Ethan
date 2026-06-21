"""Vision Agent — Analyse d'images et vidéo"""

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.events import Event

logger = logging.getLogger(__name__)


class VisionAgent(Agent):
    """Agent spécialisé dans l'analyse d'images et vidéo."""

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="vision",
            description="Analyse d'images, OCR et vision par ordinateur",
            **kwargs
        )
        super().__init__(config)

    async def _subscribe_events(self) -> None:
        self.bus.subscribe("vision:analyze", self._handle_analyze)
        self.bus.subscribe("vision:ocr", self._handle_ocr)

    async def _handle_analyze(self, event: Event) -> None:
        result = await self.run({"action": "analyze", **event.data})
        await self.publish("vision:analyzed", result)

    async def _handle_ocr(self, event: Event) -> None:
        result = await self.run({"action": "ocr", **event.data})
        await self.publish("vision:ocr_result", result)

    async def run(self, input_data: dict[str, Any] | None = None) -> dict[str, Any]:
        data = input_data or {}
        action = data.get("action", "analyze")
        image_url = data.get("image_url", "")
        description = data.get("description", "")

        if action == "analyze":
            prompt = f"""Analyze this image and provide a detailed description.
Image: {image_url}
Context: {description}
Describe: objects, people, text, colors, composition, mood."""
        elif action == "ocr":
            prompt = f"""Extract and transcribe all text from this image.
Image: {image_url}
Provide the text exactly as it appears."""
        else:
            prompt = f"Process vision task: {action}"

        response = await self.think(prompt)
        return {"action": action, "image_url": image_url, "result": response}