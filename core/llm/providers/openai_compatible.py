"""OpenAI-Compatible Provider — Pour tout service exposant une API compatible OpenAI.

Ce provider permet d'utiliser n'importe quel endpoint compatible OpenAI
(local ou distant) avec une base_url personnalisée.
Exemples : LiteLLM, OpenRouter, LM Studio (compatible), etc.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from core.llm.providers.base import LLMProvider
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """Provider générique compatible OpenAI API.

    Args:
        base_url: URL de base du service (ex: http://localhost:8000/v1)
        api_key: Clé API (peut être vide pour les services locaux)
        default_model: Modèle par défaut
    """

    name = "openai-compatible"
    default_model = "gpt-4"

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "",
        default_model: str = "gpt-4",
    ):
        self._base_url = base_url
        self._api_key = api_key
        self._default_model = default_model or "gpt-4"
        self._client = None

    async def initialize(self) -> None:
        """Initialise le client OpenAI."""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self._api_key or "not-needed",
                base_url=self._base_url,
            )
            logger.info(
                "OpenAI-compatible provider initialized (base_url=%s, model=%s)",
                self._base_url,
                self._default_model,
            )
        except ImportError:
            logger.warning("openai package not installed — pip install openai")

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
            raise RuntimeError("OpenAI-compatible provider not initialized")

        response = await self._client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        return ChatResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Streaming chat."""
        if not self._client:
            raise RuntimeError("OpenAI-compatible provider not initialized")

        stream_resp = await self._client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream_resp:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings."""
        if not self._client:
            raise RuntimeError("OpenAI-compatible provider not initialized")

        response = await self._client.embeddings.create(
            model=model or "text-embedding-ada-002",
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def list_models(self) -> list[ModelInfo]:
        """List available models via l'endpoint /models."""
        if not self._client:
            return []

        try:
            response = await self._client.models.list()
            models = []
            for m in response.data:
                models.append(
                    ModelInfo(
                        id=m.id,
                        provider=self.name,
                        name=m.id,
                        is_local=True,
                    )
                )
            return models
        except Exception as e:
            logger.warning("Failed to list models from %s: %s", self._base_url, e)
            return []

    async def test_connection(self) -> bool:
        """Teste la connexion en listant les modèles."""
        if not self._client:
            await self.initialize()
            if not self._client:
                return False
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception as e:
            logger.warning("Connection test failed for %s: %s", self._base_url, e)
            return False