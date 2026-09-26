"""Provider Factory — Crée une instance LLMProvider depuis une config.

Supporte : ollama, openai, azure, anthropic, vllm, llamacpp, lmstudio,
gemini, OpenRouter, openai-compatible, custom.
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.providers.anthropic import AnthropicProvider
from core.llm.providers.azure import AzureOpenAIProvider
from core.llm.providers.base import LLMProvider
from core.llm.providers.gemini import GeminiProvider
from core.llm.providers.llamacpp import LlamaCppProvider
from core.llm.providers.lmstudio import LMStudioProvider
from core.llm.providers.ollama import OllamaProvider
from core.llm.providers.openai import OpenAIProvider
from core.llm.providers.openai_compatible import OpenAICompatibleProvider
from core.llm.providers.openrouter import OpenRouterProvider
from core.llm.providers.vllm import VLLMProvider

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

# URLs de base par défaut des providers locaux — source unique Core.
# Utilisées par ``create_provider_from_config`` ET exposées aux interfaces via
# ``ProviderManager.get_catalog()`` : aucune interface ne doit dupliquer cette
# connaissance (règle AGENTS.md — pas de registre parallèle côté WebUI).
DEFAULT_BASE_URLS: dict[str, str] = {
    "ollama": "http://localhost:11434",
    "vllm": "http://localhost:8000",
    "llamacpp": "http://localhost:8080",
    "lmstudio": "http://localhost:1234",
    "openai-compatible": "http://localhost:8000/v1",
}


def default_base_url(provider_type: str) -> str:
    """URL de base par défaut d'un type de provider.

    Args:
        provider_type: Type de provider (ex: ``ollama``).

    Returns:
        L'URL par défaut, ou ``""`` si le type n'impose aucun endpoint
        (providers cloud : openai, anthropic, gemini, …).
    """
    return DEFAULT_BASE_URLS.get((provider_type or "").lower(), "")


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
        provider: LLMProvider = OllamaProvider(base_url=base_url or DEFAULT_BASE_URLS["ollama"])
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "vllm":
        provider = VLLMProvider(base_url=base_url or DEFAULT_BASE_URLS["vllm"])
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "llamacpp":
        provider = LlamaCppProvider(base_url=base_url or DEFAULT_BASE_URLS["llamacpp"])
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "lmstudio":
        provider = LMStudioProvider(base_url=base_url or DEFAULT_BASE_URLS["lmstudio"])
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "openai":
        provider = OpenAIProvider(api_key=api_key)
        if default_model:
            provider.default_model = default_model
        return provider

    if provider_type == "azure":
        # Azure requires api_version. Elle peut être fournie au niveau racine
        # (config historique) ou dans ``options`` (format exposé aux interfaces
        # qui ne peuvent pas écrire de clé racine inconnue du schéma API).
        options = config.get("options") or {}
        api_version = (
            config.get("api_version")
            or (options.get("api_version") if isinstance(options, dict) else None)
            or "2023-05-15"
        )
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
        base_url=base_url or DEFAULT_BASE_URLS["openai-compatible"],
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
