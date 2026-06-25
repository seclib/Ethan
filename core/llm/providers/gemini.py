"""Gemini Provider — Implémentation du provider Google Gemini."""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.base import LLMProvider
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Provider Google Gemini."""

    name = "gemini"
    default_model = "gemini-pro"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = None

    async def initialize(self) -> None:
        """Initialise le client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._client = genai
            logger.info("Gemini provider initialized")
        except ImportError:
            logger.warning("google-generativeai package not installed")

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
            raise RuntimeError("Gemini provider not initialized")

        # Convertir les messages au format Gemini
        gemini_messages = []
        for msg in messages:
            gemini_messages.append({
                "role": msg.role,
                "parts": [msg.content],
            })

        model_instance = self._client.GenerativeModel(model or self.default_model)

        response = await model_instance.generate_content_async(
            gemini_messages,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return ChatResponse(
            content=response.text,
            model=model or self.default_model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            },
        )

    async def chat_stream(self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7, max_tokens: int | None = None):
        """Streaming chat."""
        if not self._client:
            raise RuntimeError("Gemini provider not initialized")

        gemini_messages = []
        for msg in messages:
            gemini_messages.append({
                "role": msg.role,
                "parts": [msg.content],
            })

        model_instance = self._client.GenerativeModel(model or self.default_model)

        response = await model_instance.generate_content_async(
            gemini_messages,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings."""
        if not self._client:
            raise RuntimeError("Gemini provider not initialized")

        model_name = model or "text-embedding-004"
        embeddings = []

        for text in texts:
            result = await self._client.embed_content_async(
                model=model_name,
                content=text,
            )
            embeddings.append(result.embedding.values)

        return embeddings

    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        models = [
            ModelInfo(
                id="gemini-pro",
                provider=self.name,
                name="Gemini Pro",
                context_length=32000,
                quality_score=0.88,
                avg_latency_ms=1000.0,
                capabilities=["chat", "code", "reasoning"],
            ),
            ModelInfo(
                id="gemini-ultra",
                provider=self.name,
                name="Gemini Ultra",
                context_length=32000,
                quality_score=0.92,
                avg_latency_ms=2000.0,
                capabilities=["chat", "code", "reasoning"],
            ),
        ]

        return models