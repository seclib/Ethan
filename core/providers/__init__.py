"""ETHAN Core — Providers (conformité Première Loi d'ETHAN / AGENTS.md).

La source de vérité pour tous les providers IA dans ETHAN réside dans `core/providers/`.
Ré-expose les providers implémentés et le gestionnaire unifié de providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ReasoningProvider(ABC):
    """Abstract base class for reasoning providers (technology independence)."""

    @abstractmethod
    async def reason(self, prompt: str, **kwargs) -> str:
        """Execute reasoning trace."""
        raise NotImplementedError


from core.llm.provider_manager import ProviderManager

_global_provider_manager: ProviderManager | None = None


def get_provider_manager() -> ProviderManager:
    """Retourne l'instance singleton du ProviderManager."""
    global _global_provider_manager
    if _global_provider_manager is None:
        _global_provider_manager = ProviderManager()
    return _global_provider_manager
from core.llm.providers.anthropic import AnthropicProvider
from core.llm.providers.azure import AzureOpenAIProvider
from core.llm.providers.base import LLMProvider
from core.llm.providers.gemini import GeminiProvider
from core.llm.providers.llamacpp import LlamaCppProvider
from core.llm.providers.lmstudio import LMStudioProvider
from core.llm.providers.ollama import OllamaProvider
from core.llm.providers.openai import OpenAIProvider
from core.llm.providers.openrouter import OpenRouterProvider
from core.llm.providers.sglang import SGLangProvider
from core.llm.providers.vllm import VLLMProvider

__all__ = [
    "AnthropicProvider",
    "AzureOpenAIProvider",
    "GeminiProvider",
    "LLMProvider",
    "LMStudioProvider",
    "LlamaCppProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "ProviderManager",
    "ReasoningProvider",
    "SGLangProvider",
    "VLLMProvider",
    "get_provider_manager",
]
