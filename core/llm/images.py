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
        # Clé API en mémoire d'instance UNIQUEMENT — jamais persistée.
        self._api_key: str | None = None

    async def configure(
        self,
        provider: str,
        model: str = "dall-e-3",
        api_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Configure the image generation engine.

        Note sécurité : la clé API est stockée en mémoire d'instance
        uniquement — jamais persistée en clair ni renvoyée par
        ``get_config``.
        """
        if api_key:
            self._api_key = api_key
        config = {
            "provider": provider,
            "model": model,
            "enabled": True,
            "metadata": dict(metadata or {}),
        }
        await self._store.save(self._DOMAIN, "default", config)
        return {**config, "has_api_key": bool(self._api_key)}

    async def get_config(self) -> dict[str, Any] | None:
        """Retrieve the current image generation configuration.

        La clé API n'est jamais renvoyée : ``has_api_key`` indique si une
        clé est configurée en mémoire.
        """
        cfg = await self._store.get(self._DOMAIN, "default")
        if cfg is None:
            return None
        # Ne JAMAIS renvoyer une clé résiduelle du store (anciennes configs).
        public = {k: v for k, v in cfg.items() if k not in ("api_key", "apiKey")}
        return {**public, "has_api_key": bool(self._api_key or cfg.get("api_key"))}

    async def _raw_config(self) -> dict[str, Any] | None:
        """Config interne brute (avec clé) — usage interne uniquement."""
        cfg = await self._store.get(self._DOMAIN, "default")
        if cfg is None:
            return None
        if self._api_key:
            cfg = {**cfg, "api_key": self._api_key}
        return cfg

    async def generate(self, prompt: str, config: dict[str, Any] | None = None) -> bytes:
        """Generate an image from a text prompt.

        This is a stub — real implementations delegate to the configured
        provider (OpenAI, Stability AI, etc.).
        """
        cfg = config or await self._raw_config()
        if cfg is None:
            raise RuntimeError("Image generation not configured")
        logger.info("Image generation requested for prompt via %s", cfg.get("provider"))
        return b""
