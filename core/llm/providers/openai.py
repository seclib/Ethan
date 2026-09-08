"""OpenAI Provider — Implémentation du provider OpenAI.

Capabilities: LLM, Vision (GPT-4V), Embeddings, Transcription (Whisper).
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.base import LLMProvider
from core.llm.types import (
    ChatMessage,
    ChatResponse,
    ModelInfo,
    TranscriptionRequest,
    TranscriptionResponse,
    VisionRequest,
    VisionResponse,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """Provider OpenAI.

    Supports: chat, embeddings, vision (gpt-4-v), transcription (whisper).
    """

    name = "openai"
    default_model = "gpt-4"
    supports_vision = True
    supports_transcription = True

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = None  # Initialisé dans initialize()

    async def initialize(self) -> None:
        """Initialise le client."""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._api_key)
            logger.info("OpenAI provider initialized")
        except ImportError:
            logger.warning("openai package not installed")

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        """Chat completion."""
        if not self._client:
            raise RuntimeError("OpenAI provider not initialized")

        response = await self._client.chat.completions.create(
            model=model or self.default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        return ChatResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
        )

    async def chat_stream(self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7, max_tokens: int | None = None):
        """Streaming chat."""
        if not self._client:
            raise RuntimeError("OpenAI provider not initialized")

        stream = await self._client.chat.completions.create(
            model=model or self.default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings."""
        if not self._client:
            raise RuntimeError("OpenAI provider not initialized")

        response = await self._client.embeddings.create(
            model=model or "text-embedding-ada-002",
            input=texts,
        )

        return [item.embedding for item in response.data]

    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        if not self._client:
            return []

        models = [
            ModelInfo(
                id="gpt-4",
                provider=self.name,
                name="GPT-4",
                model="gpt-4",
                context_length=8192,
                pricing={"input": 0.03, "output": 0.06},
                quality_score=0.95,
                avg_latency_ms=2000.0,
                capabilities=["chat", "code", "reasoning"],
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                provider=self.name,
                name="GPT-3.5 Turbo",
                model="gpt-3.5-turbo",
                context_length=4096,
                pricing={"input": 0.0015, "output": 0.002},
                quality_score=0.85,
                avg_latency_ms=500.0,
                capabilities=["chat", "code"],
            ),
            ModelInfo(
                id="gpt-4-vision-preview",
                provider=self.name,
                name="GPT-4 Vision",
                model="gpt-4-vision-preview",
                context_length=128000,
                pricing={"input": 0.01, "output": 0.03},
                quality_score=0.93,
                avg_latency_ms=3000.0,
                capabilities=["chat", "vision"],
            ),
        ]

        return models

    async def vision_analyze(self, request: VisionRequest) -> VisionResponse:
        """Analyze an image via OpenAI Vision API (GPT-4V)."""
        if not self._client:
            raise RuntimeError("OpenAI provider not initialized")

        model = request.model or "gpt-4-vision-preview"

        # Build multi-content message with text + images
        content: list[dict[str, Any]] = [{"type": "text", "text": request.prompt}]
        for img in request.images:
            if img.is_url:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img.data},
                })
            else:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img.mime_type};base64,{img.data}",
                    },
                })

        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=request.max_tokens or 1024,
        )

        return VisionResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        )

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """Transcribe audio via OpenAI Whisper API."""
        if not self._client:
            raise RuntimeError("OpenAI provider not initialized")

        import io

        model = request.model or "whisper-1"
        audio_file = io.BytesIO(request.audio_data)
        audio_file.name = f"audio.{request.mime_type.split('/')[-1]}"

        kwargs: dict[str, Any] = {
            "file": audio_file,
            "model": model,
            "response_format": "json",
        }
        if request.language:
            kwargs["language"] = request.language

        response = await self._client.audio.transcriptions.create(**kwargs)

        return TranscriptionResponse(
            text=response.text,
            model=model,
            provider=self.name,
            language=request.language,
        )
