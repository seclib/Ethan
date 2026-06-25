"""Ollama Provider — Implémentation du provider Ollama (local)."""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.base import LLMProvider
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Provider Ollama (local)."""

    name = "ollama"
    default_model = "llama2:70b"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url
        self._client = None

    async def initialize(self) -> None:
        """Initialise le client."""
        try:
            import httpx
            self._client = httpx.AsyncClient(timeout=300.0)
            logger.info(f"Ollama provider initialized ({self._base_url})")
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
            raise RuntimeError("Ollama provider not initialized")

        response = await self._client.post(
            f"{self._base_url}/api/chat",
            json={
                "model": model or self.default_model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )

        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data["message"]["content"],
            model=data.get("model", model or self.default_model),
            provider=self.name,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            },
        )

    async def chat_stream(self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7, max_tokens: int | None = None):
        """Streaming chat."""
        if not self._client:
            raise RuntimeError("Ollama provider not initialized")

        async with self._client.stream(
            "POST",
            f"{self._base_url}/api/chat",
            json={
                "model": model or self.default_model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Generate embeddings."""
        if not self._client:
            raise RuntimeError("Ollama provider not initialized")

        embeddings = []
        for text in texts:
            response = await self._client.post(
                f"{self._base_url}/api/embeddings",
                json={
                    "model": model or "llama2:70b",
                    "prompt": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])

        return embeddings

    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        if not self._client:
            return []

        try:
            response = await self._client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("models", []):
                model_name = model_data["name"]
                models.append(ModelInfo(
                    id=model_name,
                    provider=self.name,
                    name=model_name,
                    context_length=4096,  # Ollama ne retourne pas cette info
                    quality_score=0.80,  # Par défaut
                    avg_latency_ms=100.0,  # Local = rapide
                    is_local=True,
                    is_private=True,
                    capabilities=["chat", "embedding"],
                ))

            return models
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return []