"""Core-owned image generation — DALL-E, Stable Diffusion, etc.

ETHAN Core owns image generation capabilities.  The WebUI only renders
the generated images and sends prompts through the API.
"""

from __future__ import annotations

import logging
from typing import Any

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Own image generation provider configuration and synthesis."""

    _DOMAIN = "image-config"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def configure(
        self,
        provider: str,
        model: str = "dall-e-3",
        api_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Configure the image generation engine."""
        config = {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "enabled": True,
            "metadata": dict(metadata or {}),
        }
        await self._store.save(self._DOMAIN, "default", config)
        return config

    async def get_config(self) -> dict[str, Any] | None:
        """Retrieve the current image generation configuration."""
        return await self._store.get(self._DOMAIN, "default")

    async def generate(self, prompt: str, config: dict[str, Any] | None = None) -> bytes:
        """Generate an image from a text prompt.

        This is a stub — real implementations delegate to the configured
        provider (OpenAI, Stability AI, etc.).
        """
        cfg = config or await self.get_config()
        if cfg is None:
            raise RuntimeError("Image generation not configured")
        logger.info("Image generation requested for prompt via %s", cfg.get("provider"))
        return b""
