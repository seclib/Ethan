"""Core-owned TTS/STT — text-to-speech and speech-to-text.

ETHAN Core owns audio capabilities.  The WebUI only renders the audio
controls and sends text through the API.
"""

from __future__ import annotations

import logging
from typing import Any

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class TTSEngine:
    """Own TTS/STT provider configuration and synthesis."""

    _DOMAIN = "tts-config"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def configure(
        self,
        provider: str,
        voice: str = "default",
        speed: float = 1.0,
        api_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Configure the TTS engine."""
        config = {
            "provider": provider,
            "voice": voice,
            "speed": speed,
            "api_key": api_key,
            "enabled": True,
            "metadata": dict(metadata or {}),
        }
        await self._store.save(self._DOMAIN, "default", config)
        return config

    async def get_config(self) -> dict[str, Any] | None:
        """Retrieve the current TTS configuration."""
        return await self._store.get(self._DOMAIN, "default")

    async def synthesize(self, text: str, config: dict[str, Any] | None = None) -> bytes:
        """Synthesize text to speech audio bytes.

        This is a stub — real implementations delegate to the configured
        provider (OpenAI, ElevenLabs, etc.).
        """
        cfg = config or await self.get_config()
        if cfg is None:
            raise RuntimeError("TTS not configured")
        logger.info("TTS synthesize requested for %d chars via %s", len(text), cfg.get("provider"))
        return b""
