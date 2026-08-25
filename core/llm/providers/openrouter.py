"""OpenRouter Provider — Interface for OpenRouter multi-provider API.

Supports multi-model fallback and standard OpenAI completions via OpenRouter.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from core.llm.providers.base import LLMProvider
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider.

    Args:
        api_key: OpenRouter API key.
        default_model: Default model.
        site_url: URL of the site calling OpenRouter (for rankings).
        site_name: Name of the site calling OpenRouter.
    """

    name = "openrouter"
    default_model = "openrouter/auto"

    def __init__(
        self,
        api_key: str = "",
        default_model: str = "openrouter/auto",
        site_url: str = "",
        site_name: str = "Ethan",
        routing: dict[str, Any] | None = None,
    ):
        self._api_key = api_key
        self._default_model = default_model or "openrouter/auto"
        self.default_model = self._default_model
        self._site_url = site_url
        self._site_name = site_name
        # OpenRouter accepts this object as the ``provider`` request field.
        # It can express ordered providers and allow_fallbacks without the
        # WebUI implementing any routing logic of its own.
        self._routing = dict(routing or {})
        self._base_url = "https://openrouter.ai/api/v1"
        self._client = None

    async def initialize(self) -> None:
        """Initialise le client OpenRouter."""
        try:
            from openai import AsyncOpenAI
            
            headers = {}
            if self._site_url:
                headers["HTTP-Referer"] = self._site_url
            if self._site_name:
                headers["X-Title"] = self._site_name
                
            self._client = AsyncOpenAI(
                api_key=self._api_key or "not-needed",
                base_url=self._base_url,
                default_headers=headers if headers else None,
            )
            logger.info(
                "OpenRouter provider initialized (model=%s)",
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
            raise RuntimeError("OpenRouter provider not initialized")

        request: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if self._routing:
            request["extra_body"] = {"provider": self._routing}
        response = await self._client.chat.completions.create(
            **request,
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
            raise RuntimeError("OpenRouter provider not initialized")

        request: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if self._routing:
            request["extra_body"] = {"provider": self._routing}
        stream_resp = await self._client.chat.completions.create(**request)

        async for chunk in stream_resp:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings. (OpenRouter does not support native embeddings currently but forwards them)."""
        if not self._client:
            raise RuntimeError("OpenRouter provider not initialized")

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
                        id=f"openrouter_{m.id}",
                        provider=self.name,
                        name=m.name if hasattr(m, 'name') else m.id,
                        model=m.id,
                        context_length=m.context_length if hasattr(m, 'context_length') else 4096,
                        is_local=False,
                        pricing={"prompt": getattr(m, "pricing", {}).get("prompt", "0.0"), "completion": getattr(m, "pricing", {}).get("completion", "0.0")} if hasattr(m, "pricing") else None
                    )
                )
            return models
        except Exception as e:
            logger.warning("Failed to list models from OpenRouter: %s", e)
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
            logger.warning("Connection test failed for OpenRouter: %s", e)
            return False
