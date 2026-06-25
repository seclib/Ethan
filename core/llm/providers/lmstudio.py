"""LM Studio Provider — Implémentation du provider LM Studio (local)."""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.base import LLMProvider
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class LMStudioProvider(LLMProvider):
    """Provider LM Studio (local)."""

    name = "lmstudio"
    default_model = "local-model"

    def __init__(self, base_url: str = "http://localhost:1234"):
        self._base_url = base_url
        self._client = None

    async def initialize(self) -> None:
        """Initialise le client."""
        try:
            import httpx
            self._client = httpx.AsyncClient(timeout=300.0)
            logger.info(f"LM Studio provider initialized ({self._base_url})")
        except ImportError:
            logger.warning("httpx package not installed")

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
            raise RuntimeError("LM Studio provider not initialized")

        response = await self._client.post(
            f"{self._base_url}/v1/chat/completions",
            json={
                "model": model or self.default_model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            },
        )

        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", model or self.default_model),
            provider=self.name,
            usage=data.get("usage", {}),
        )

    async def chat_stream(self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7, max_tokens: int | None = None):
        """Streaming chat."""
        if not self._client:
            raise RuntimeError("LM Studio provider not initialized")

        async with self._client.stream(
            "POST",
            f"{self._base_url}/v1/chat/completions",
            json={
                "model": model or self.default_model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    import json
                    data = json.loads(line[6:])
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings."""
        if not self._client:
            raise RuntimeError("LM Studio provider not initialized")

        embeddings = []
        for text in texts:
            response = await self._client.post(
                f"{self._base_url}/v1/embeddings",
                json={
                    "model": model or self.default_model,
                    "input": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["data"][0]["embedding"])

        return embeddings

    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        if not self._client:
            return []

        try:
            response = await self._client.get(f"{self._base_url}/v1/models")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("data", []):
                model_id = model_data["id"]
                models.append(ModelInfo(
                    id=model_id,
                    provider=self.name,
                    name=model_id,
                    context_length=4096,
                    quality_score=0.80,
                    avg_latency_ms=100.0,
                    is_local=True,
                    is_private=True,
                    capabilities=["chat", "embedding"],
                ))

            return models
        except Exception as e:
            logger.warning(f"Failed to list LM Studio models: {e}")
            return []