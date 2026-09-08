"""LLM Provider Base — Interface abstraite unifiée pour tous les providers.

This is the SINGLE authoritative interface. All providers (LLM, Vision,
Embeddings, Speech-to-Text, Transcription) implement this contract.

Capabilities are optional — providers raise NotImplementedError for
unsupported operations. The ProviderManager routes requests to the right
provider based on declared capabilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from core.llm.types import (
    ChatMessage,
    ChatResponse,
    ModelInfo,
    TranscriptionRequest,
    TranscriptionResponse,
    VisionRequest,
    VisionResponse,
)


class LLMProvider(ABC):
    """Interface abstraite unifiée pour les fournisseurs LLM.

    Tous les providers doivent implémenter cette interface.
    Le changement de fournisseur se fait uniquement via la configuration.

    Capabilities (vision, transcription, embed) are optional. A provider
    that does not support a capability should raise NotImplementedError
    with a clear message.
    """

    name: str = "base"
    default_model: str = "default"

    # Capability flags — override in subclasses to declare support
    supports_vision: bool = False
    supports_transcription: bool = False
    supports_embedding: bool = True

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

    # ── Optional capabilities ───────────────────────────────────────────────

    async def vision_analyze(self, request: VisionRequest) -> VisionResponse:
        """Analyze an image with a vision-capable model.

        Raises:
            NotImplementedError: If this provider does not support vision.
        """
        raise NotImplementedError(
            f"Provider '{self.name}' does not support vision analysis"
        )

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """Transcribe audio to text.

        Raises:
            NotImplementedError: If this provider does not support transcription.
        """
        raise NotImplementedError(
            f"Provider '{self.name}' does not support audio transcription"
        )

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def test_connection(self) -> bool:
        """Teste la connexion au provider.

        Tente un `list_models()` — si cela réussit, le provider est joignable.

        Returns:
            True si la connexion est fonctionnelle, False sinon.
        """
        try:
            await self.list_models()
            return True
        except Exception:
            return False

    async def initialize(self) -> None:
        """Hook d'initialisation asynchrone — à surcharger si besoin.

        Les providers concrets préparent leur client HTTP ici. L'implémentation
        par défaut est un no-op afin de rester safe pour les providers qui
        n'ont rien à initialiser.
        """
        pass
