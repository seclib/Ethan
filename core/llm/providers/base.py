"""LLM Provider Base — Interface abstraite pour tous les providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from core.llm.types import ChatMessage, ChatResponse, ModelInfo


class LLMProvider(ABC):
    """Interface abstraite pour les fournisseurs LLM.

    Tous les providers doivent implémenter cette interface.
    Le changement de fournisseur se fait uniquement via la configuration.
    """

    name: str = "base"
    default_model: str = "default"

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        """Chat completion."""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Chat completion with streaming."""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Generate embeddings."""
        pass

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        pass