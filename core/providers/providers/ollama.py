"""Ollama Provider — Local LLM inference via Ollama API."""

import json
import logging
from typing import Any, AsyncIterator

import httpx

from core.llm import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ModelInfo,
    registry,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference."""

    def __init__(self, host: str = "http://localhost:11434", default_model: str = "llama3.2"):
        self._host = host.rstrip("/")
        self._default_model = default_model
        self._client = httpx.AsyncClient(timeout=120.0)

    @property
    def name(self) -> str:
        return "ollama"

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

        payload = {
            "model": model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "options": {
                "temperature": temperature,
            },
            "stream": False,
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        response = await self._client.post(
            f"{self._host}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data["message"]["content"],
            model=data.get("model", model_name),
            provider=self.name,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        model_name = model or self._default_model

        payload = {
            "model": model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "options": {"temperature": temperature},
            "stream": True,
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        async with self._client.stream(
            "POST", f"{self._host}/api/chat", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        model_name = model or "nomic-embed-text"

        payload = {
            "model": model_name,
            "input": texts,
        }

        response = await self._client.post(
            f"{self._host}/api/embed",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        return data.get("embeddings", [])

    async def list_models(self) -> list[ModelInfo]:
        response = await self._client.get(f"{self._host}/api/tags")
        response.raise_for_status()
        data = response.json()

        models = []
        for model in data.get("models", []):
            models.append(ModelInfo(
                id=model["name"],
                provider=self.name,
                context_length=model.get("details", {}).get("context_length", 4096),
            ))
        return models

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        payload = {"name": model, "stream": False}
        response = await self._client.post(
            f"{self._host}/api/pull",
            json=payload,
        )
        return response.is_success

    async def close(self) -> None:
        await self._client.aclose()


# Auto-register
ollama_provider = OllamaProvider()
registry.register(ollama_provider)