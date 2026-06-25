"""OpenAI Provider — Implémentation du provider OpenAI."""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.base import LLMProvider
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """Provider OpenAI."""

    name = "openai"
    default_model = "gpt-4"

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
                context_length=4096,
                pricing={"input": 0.0015, "output": 0.002},
                quality_score=0.85,
                avg_latency_ms=500.0,
                capabilities=["chat", "code"],
            ),
        ]

        return models