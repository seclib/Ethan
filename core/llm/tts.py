"""Core-owned TTS/STT — text-to-speech and speech-to-text.

ETHAN Core owns audio capabilities.  The WebUI only renders the audio
controls and sends text through the API.
"""

from __future__ import annotations

import logging
import struct
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
        """Synthesize text to speech audio bytes (WAV).

        Providers:
        - "builtin-tone" : offline placeholder that renders a short chime
          per sentence.  Clearly a dev/test fallback so the full audio
          pipeline can be exercised without external services.
        - "openai" / "elevenlabs" / others : NOT implemented yet — raises
          NotImplementedError until a dedicated integration lands (RFC).
        """
        cfg = config or await self.get_config()
        if cfg is None:
            raise RuntimeError("TTS not configured")
        provider = str(cfg.get("provider", ""))
        speed = float(cfg.get("speed", 1.0)) or 1.0
        logger.info("TTS synthesize requested for %d chars via %s", len(text), provider)

        if provider == "builtin-tone":
            return _render_tone_wav(text, speed)

        if provider in ("openai", "openai-compatible"):
            return await _synthesize_openai_compatible(text, cfg)

        raise NotImplementedError(
            f"TTS provider '{provider}' is not implemented yet"
        )


async def _synthesize_openai_compatible(text: str, cfg: dict[str, Any]) -> bytes:
    """OpenAI-compatible /audio/speech call (stdlib only, off event loop).

    Config keys: api_key, voice, metadata.base_url (def openai), metadata.model.
    """
    import asyncio
    import json as _json
    import urllib.request

    meta = cfg.get("metadata") or {}
    base_url = str(meta.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    api_key = cfg.get("api_key")
    if not api_key:
        raise RuntimeError(
            "Le provider TTS 'openai' exige une clé API — la configurer via "
            "POST /v1/audio/config (jamais dans le code ni git)"
        )
    model = str(meta.get("model") or "tts-1")
    voice = str(cfg.get("voice") or "alloy")
    if voice == "default":
        voice = "alloy"
    payload = _json.dumps({
        "model": model,
        "input": text[:4096],
        "voice": voice,
        "response_format": "wav",
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/audio/speech",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    def _call() -> bytes:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 — URL issue de la config admin
            return resp.read()

    return await asyncio.to_thread(_call)


def _render_tone_wav(text: str, speed: float = 1.0) -> bytes:
    """Render a short pleasant chime per sentence as a 16-bit mono WAV.

    Dev/test placeholder only — no speech is produced.
    """
    import io
    import math
    import wave

    sample_rate = 22050
    sentences = [s for s in text.replace("\n", ". ").split(".") if s.strip()]
    sentences = sentences or [text]

    notes = [523.25, 659.25, 783.99]  # C5 E5 G5
    frames = bytearray()
    for i, _sentence in enumerate(sentences[:8]):
        freq = notes[i % len(notes)]
        duration = min(0.35 * max(1, len(_sentence) // 40 + 1) / speed, 0.9)
        n_samples = int(sample_rate * duration)
        for n in range(n_samples):
            t = n / sample_rate
            envelope = math.sin(math.pi * n / n_samples)  # fade in/out
            value = int(32767 * 0.25 * envelope * math.sin(2 * math.pi * freq * t))
            frames += struct.pack("<h", value)
        # small gap between sentences
        frames += b"\x00\x00" * int(sample_rate * 0.08)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(frames))
    return buf.getvalue()
