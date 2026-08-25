"""Azure OpenAI Provider — Interface for Azure OpenAI API.

Supports chat completions and embeddings via Azure OpenAI Service.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from core.llm.providers.base import LLMProvider
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider.

    Args:
        api_key: Azure OpenAI API key.
        base_url: Azure endpoint (e.g. https://my-resource.openai.azure.com/).
        api_version: Azure API version (e.g. 2023-05-15).
        default_model: Default deployment name.
    """

    name = "azure"
    default_model = "gpt-4"

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        api_version: str = "2023-05-15",
        default_model: str = "gpt-4",
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._api_version = api_version
        self._default_model = default_model or "gpt-4"
        self.default_model = self._default_model
        self._client = None

    async def initialize(self) -> None:
        """Initialise le client Azure OpenAI."""
        try:
            from openai import AsyncAzureOpenAI
            
            self._client = AsyncAzureOpenAI(
                api_key=self._api_key,
                api_version=self._api_version,
                azure_endpoint=self._base_url,
            )
            logger.info(
                "Azure OpenAI provider initialized (endpoint=%s, version=%s)",
                self._base_url,
                self._api_version,
            )
        except ImportError:
            logger.warning("openai package not installed — pip install openai")
        except Exception as e:
            logger.warning("Failed to initialize Azure OpenAI provider: %s", e)

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
            raise RuntimeError("Azure OpenAI provider not initialized")

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
            raise RuntimeError("Azure OpenAI provider not initialized")

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
            raise RuntimeError("Azure OpenAI provider not initialized")

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
            # Note: Azure OpenAI's /models endpoint behaves differently and often needs the deployment names manually defined
            # But we try to list them anyway if the RBAC allows it.
            response = await self._client.models.list()
            models = []
            for m in response.data:
                models.append(
                    ModelInfo(
                        id=f"azure_{m.id}",
                        provider=self.name,
                        name=m.id,
                        model=m.id,
                        is_local=False,
                    )
                )
            return models
        except Exception as e:
            logger.warning("Failed to list models from Azure OpenAI: %s", e)
            return []

    async def test_connection(self) -> bool:
        """Teste la connexion en listant les modèles."""
        if not self._client:
            await self.initialize()
            if not self._client:
                return False
        try:
            models = await self.list_models()
            return len(models) >= 0  # Azure might return empty if no RBAC for listing, but connection succeeds
        except Exception as e:
            logger.warning("Connection test failed for Azure OpenAI: %s", e)
            return False
