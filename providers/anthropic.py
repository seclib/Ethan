"""Anthropic Provider — Cloud LLM inference via Anthropic API."""

import logging
import os
from typing import Any, AsyncIterator

from core.llm import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ModelInfo,
    registry,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic provider for cloud LLM inference."""

    def __init__(
        self,
        api_key: str = "",
        default_model: str = "claude-sonnet-4-20250514",
    ):
        self._default_model = default_model
        self._api_key = api_key

        try:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=api_key or None)
        except ImportError:
            logger.warning("anthropic package not installed. Install: pip install anthropic")
            self._client = None

    @property
    def name(self) -> str:
        return "anthropic"

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
        if not self._client:
            raise RuntimeError("Anthropic client not initialized. Install: pip install anthropic")

        model_name = model or self._default_model

        # Convert messages to Anthropic format
        system_msg = None
        anthropic_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                anthropic_messages.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": model_name,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        if system_msg:
            kwargs["system"] = system_msg

        response = await self._client.messages.create(**kwargs)

        return ChatResponse(
            content=response.content[0].text if response.content else "",
            model=response.model,
            provider=self.name,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        if not self._client:
            raise RuntimeError("Anthropic client not initialized")

        model_name = model or self._default_model

        system_msg = None
        anthropic_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                anthropic_messages.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": model_name,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        if system_msg:
            kwargs["system"] = system_msg

        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not support embeddings via API")

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id="claude-sonnet-4-20250514", provider=self.name),
            ModelInfo(id="claude-3-5-sonnet-20241022", provider=self.name),
            ModelInfo(id="claude-3-opus-20240229", provider=self.name),
            ModelInfo(id="claude-3-haiku-20240307", provider=self.name),
        ]

    async def close(self) -> None:
        if self._client:
            await self._client.close()


# Auto-register
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if api_key:
    anthropic_provider = AnthropicProvider(api_key=api_key)
    registry.register(anthropic_provider)
    logger.info("Anthropic provider registered")