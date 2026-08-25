"""Provider Factory — Crée une instance LLMProvider depuis une config.

Supporte : ollama, openai, azure, anthropic, vllm, llamacpp, lmstudio,
gemini, OpenRouter, openai-compatible, custom.
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.base import LLMProvider
from core.llm.providers.ollama import OllamaProvider
from core.llm.providers.openai import OpenAIProvider
from core.llm.providers.anthropic import AnthropicProvider
from core.llm.providers.vllm import VLLMProvider
from core.llm.providers.llamacpp import LlamaCppProvider
from core.llm.providers.lmstudio import LMStudioProvider
from core.llm.providers.gemini import GeminiProvider
from core.llm.providers.openai_compatible import OpenAICompatibleProvider
from core.llm.providers.openrouter import OpenRouterProvider
from core.llm.providers.azure import AzureOpenAIProvider

logger = logging.getLogger(__name__)

# Types de providers supportés par la factory
SUPPORTED_PROVIDER_TYPES = {
    "ollama",
    "openai",
    "azure",
    "anthropic",
    "vllm",
    "llamacpp",
    "lmstudio",
    "gemini",
    "openai-compatible",
    "openrouter",
    "custom",
}


def create_provider_from_config(config: dict[str, Any]) -> LLMProvider:
    """Crée une instance LLMProvider depuis un dict de config.

    Args:
        config: Configuration du provider avec au minimum:
            - ``type``: type de provider (ollama, openai, ...)
            - ``name``: nom unique du provider
            - ``enabled``: booléen
            - ``base_url``: URL de base (providers locaux)
            - ``api_key``: clé API (providers cloud)
            - ``default_model``: modèle par défaut

    Returns:
        Instance LLMProvider configurée.

    Raises:
        ValueError: Si le type de provider est inconnu ou si la config est invalide.
    """
    provider_type = config.get("type", "").lower()
    name = config.get("name", provider_type)
    base_url = config.get("base_url", "")
    api_key = config.get("api_key", "")
    default_model = config.get("default_model", "")

    if provider_type not in SUPPORTED_PROVIDER_TYPES:
        raise ValueError(
            f"Unsupported provider type '{provider_type}'. "
            f"Supported: {sorted(SUPPORTED_PROVIDER_TYPES)}"
        )

    # Providers locaux (pas de clé API requise)
    if provider_type == "ollama":
        provider: LLMProvider = OllamaProvider(base_url=base_url or "http://localhost:11434")
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "vllm":
        provider = VLLMProvider(base_url=base_url or "http://localhost:8000")
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "llamacpp":
        provider = LlamaCppProvider(base_url=base_url or "http://localhost:8080")
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "lmstudio":
        provider = LMStudioProvider(base_url=base_url or "http://localhost:1234")
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "openai":
        provider = OpenAIProvider(api_key=api_key)
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "azure":
        # Azure typically requires api_version in config. We fallback to default if not provided.
        api_version = config.get("api_version", "2023-05-15")
        provider = AzureOpenAIProvider(
            api_key=api_key,
            base_url=base_url,
            api_version=api_version,
            default_model=default_model or "gpt-4",
        )
        return provider

    if provider_type == "anthropic":
        provider = AnthropicProvider(api_key=api_key)
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "gemini":
        provider = GeminiProvider(api_key=api_key)
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "openrouter":
        options = config.get("options") or {}
        routing = options.get("routing", options.get("provider", {}))
        if not isinstance(routing, dict):
            raise ValueError("OpenRouter routing options must be an object")
        provider = OpenRouterProvider(
            api_key=api_key,
            default_model=default_model or "openrouter/auto",
            site_url=options.get("site_url", ""),
            site_name=options.get("site_name", "Ethan"),
            routing=routing,
        )
        return provider

    # openai-compatible / custom → générique
    provider = OpenAICompatibleProvider(
        base_url=base_url or "http://localhost:8000/v1",
        api_key=api_key,
        default_model=default_model or "gpt-4",
    )
    # Le nom de l'instance doit rester celui fourni dans la config
    provider.name = name or "openai-compatible"
    return provider


def create_default_providers() -> list[LLMProvider]:
    """Crée les providers par défaut (tous désactivables).

    Returns:
        Liste d'instances providers pour ollama, openai, anthropic, vllm, openai-compatible.
    """
    return [
        create_provider_from_config({"type": "ollama", "name": "ollama", "enabled": True}),
        create_provider_from_config({"type": "openai", "name": "openai", "enabled": False}),
        create_provider_from_config({"type": "azure", "name": "azure", "enabled": False}),
        create_provider_from_config({"type": "anthropic", "name": "anthropic", "enabled": False}),
        create_provider_from_config({"type": "vllm", "name": "vllm", "enabled": False}),
        create_provider_from_config({"type": "openrouter", "name": "openrouter", "enabled": False}),
        create_provider_from_config(
            {"type": "openai-compatible", "name": "custom", "enabled": False, "default_model": ""}
        ),
    ]
