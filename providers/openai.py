"""OpenAI Provider — Cloud LLM inference via OpenAI API."""

import logging
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from core.llm import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ModelInfo,
    registry,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI provider for cloud LLM inference."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o",
    ):
        self._default_model = default_model
        self._client = AsyncOpenAI(api_key=api_key or None, base_url=base_url)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self._default_model

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        model_name = model or self._default_model

        kwargs = {
            "model": model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason,
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        model_name = model or self._default_model

        kwargs = {
            "model": model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        model_name = model or "text-embedding-3-small"

        response = await self._client.embeddings.create(
            model=model_name,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def list_models(self) -> list[ModelInfo]:
        response = await self._client.models.list()
        models = []
        for model in response.data:
            models.append(ModelInfo(
                id=model.id,
                provider=self.name,
            ))
        return models

    async def close(self) -> None:
        await self._client.close()


# Auto-register (requires OPENAI_API_KEY env var)
import os
api_key = os.environ.get("OPENAI_API_KEY", "")
if api_key:
    openai_provider = OpenAIProvider(api_key=api_key)
    registry.register(openai_provider)
    logger.info("OpenAI provider registered")