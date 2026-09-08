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
    ProviderCapability,
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
    # Speech-to-Text est l'alias normalisé de transcription (même méthode
    # ``transcribe``) — rares sont les providers qui distinguent les deux.
    supports_speech_to_text: bool | None = None

    def capabilities(self) -> list[str]:
        """Liste canonique et sérialisable des capacités de ce provider.

        Retourne une liste normalisée (``ProviderCapability``) :
        ``[llm, vision?, embedding?, speech_to_text?, transcription?]``.
        C'est la forme exposée à l'API ``/providers`` et à la WebUI —
        jamais les secrets ni la config brute.
        """
        return ProviderCapability.from_flags(
            supports_vision=self.supports_vision,
            supports_embedding=self.supports_embedding,
            supports_transcription=self.supports_transcription,
            supports_speech_to_text=self.supports_speech_to_text,
        )

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
