"""Anthropic Provider — Implémentation du provider Anthropic.

Capabilities: LLM, Vision (Claude 3+), no native embeddings/transcription.
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.base import LLMProvider
from core.llm.types import (
    ChatMessage,
    ChatResponse,
    ModelInfo,
    VisionRequest,
    VisionResponse,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Provider Anthropic.

    Supports: chat, vision (claude-3). No native embeddings or transcription.
    """

    name = "anthropic"
    default_model = "claude-3-sonnet"
    supports_vision = True
    supports_transcription = False
    supports_embedding = False

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = None

    async def initialize(self) -> None:
        """Initialise le client."""
        try:
            import anthropic
            self._client = anthropic.AsyncClient(api_key=self._api_key)
            logger.info("Anthropic provider initialized")
        except ImportError:
            logger.warning("anthropic package not installed")

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
            raise RuntimeError("Anthropic provider not initialized")

        # Convertir les messages au format Anthropic
        system_msg = None
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        kwargs = {
            "model": model or self.default_model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 1024,
        }

        if system_msg:
            kwargs["system"] = system_msg

        response = await self._client.messages.create(**kwargs)

        return ChatResponse(
            content=response.content[0].text,
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )

    async def chat_stream(self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7, max_tokens: int | None = None):
        """Streaming chat."""
        if not self._client:
            raise RuntimeError("Anthropic provider not initialized")

        system_msg = None
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        kwargs = {
            "model": model or self.default_model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 1024,
            "stream": True,
        }

        if system_msg:
            kwargs["system"] = system_msg

        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings."""
        # Anthropic n'a pas d'API d'embedding native
        raise NotImplementedError("Anthropic does not provide embeddings API")

    async def vision_analyze(self, request: VisionRequest) -> VisionResponse:
        """Analyze an image via Claude 3 Vision API."""
        if not self._client:
            raise RuntimeError("Anthropic provider not initialized")

        model = request.model or "claude-3-sonnet"

        # Build multi-content message with text + images
        content: list[dict[str, Any]] = [{"type": "text", "text": request.prompt}]
        for img in request.images:
            if img.is_url:
                source = {"type": "url", "url": img.data}
            else:
                source = {
                    "type": "base64",
                    "media_type": img.mime_type,
                    "data": img.data,
                }
            content.append({"type": "image", "source": source})

        response = await self._client.messages.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=request.max_tokens or 1024,
        )

        return VisionResponse(
            content=response.content[0].text,
            model=response.model,
            provider=self.name,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        models = [
            ModelInfo(
                id="claude-3-opus",
                provider=self.name,
                name="Claude 3 Opus",
                model="claude-3-opus",
                context_length=200000,
                pricing={"input": 0.015, "output": 0.075},
                quality_score=0.96,
                avg_latency_ms=3000.0,
                capabilities=["chat", "code", "reasoning"],
            ),
            ModelInfo(
                id="claude-3-sonnet",
                provider=self.name,
                name="Claude 3 Sonnet",
                model="claude-3-sonnet",
                context_length=200000,
                pricing={"input": 0.003, "output": 0.015},
                quality_score=0.90,
                avg_latency_ms=1500.0,
                capabilities=["chat", "code", "reasoning"],
            ),
        ]

        return models
