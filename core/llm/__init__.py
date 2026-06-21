# Jarvis OS — LLM Provider Interface
# Abstraction unifiée pour tous les fournisseurs LLM

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ChatMessage:
    """Message de chat standardisé."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class ChatResponse:
    """Réponse de chat standardisée."""
    content: str
    model: str
    provider: str
    usage: dict | None = None
    finish_reason: str | None = None


@dataclass
class ModelInfo:
    """Informations sur un modèle."""
    id: str
    provider: str
    context_length: int = 4096
    pricing: dict | None = None


class LLMProvider(ABC):
    """Interface abstraite pour les fournisseurs LLM.

    Tous les providers doivent implémenter cette interface.
    Le changement de fournisseur se fait uniquement via la configuration.
    """

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
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Chat completion with streaming."""
        if False:
            yield ""  # Make this an async generator
        ...

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Generate embeddings."""
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'ollama', 'openai')."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""
        ...


class ProviderRegistry:
    """Registry des fournisseurs LLM."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        """Register a provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> LLMProvider:
        """Get a provider by name."""
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not found. Available: {list(self._providers.keys())}")
        return self._providers[name]

    def list(self) -> list[str]:
        """List all registered providers."""
        return list(self._providers.keys())

    def get_default(self) -> LLMProvider:
        """Get the default provider."""
        if not self._providers:
            raise ValueError("No providers registered")
        # Return the first registered provider as default
        return next(iter(self._providers.values()))


# Global registry instance
registry = ProviderRegistry()


def get_provider(name: str | None = None) -> LLMProvider:
    """Get a provider by name, or the default if not specified.

    Usage:
        provider = get_provider("ollama")
        response = await provider.chat(messages=[...])
    """
    if name is None:
        return registry.get_default()
    return registry.get(name)