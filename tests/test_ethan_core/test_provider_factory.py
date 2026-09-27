"""Tests for Core-owned provider construction and OpenRouter routing."""

import pytest
from core.llm.provider_factory import (
    DEFAULT_BASE_URLS,
    SUPPORTED_PROVIDER_TYPES,
    create_provider_from_config,
)
from core.llm.provider_manager import ProviderManager
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
from core.llm.types import ChatMessage

# Classe attendue pour CHAQUE type supporté par la factory. ``custom`` n'a pas
# de branche dédiée : il tombe sur le fallback générique openai-compatible.
EXPECTED_CLASSES: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "azure": AzureOpenAIProvider,
    "anthropic": AnthropicProvider,
    "vllm": VLLMProvider,
    "llamacpp": LlamaCppProvider,
    "lmstudio": LMStudioProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
    "openai-compatible": OpenAICompatibleProvider,
    "custom": OpenAICompatibleProvider,
}


def test_factory_configures_openrouter_routing_and_technical_default_model():
    provider = create_provider_from_config(
        {
            "type": "openrouter",
            "api_key": "test-key",
            "default_model": "anthropic/claude-sonnet-4",
            "options": {
                "site_url": "https://ethan.example",
                "site_name": "ETHAN",
                "routing": {"order": ["Anthropic", "OpenAI"], "allow_fallbacks": True},
            },
        }
    )

    assert isinstance(provider, OpenRouterProvider)
    assert provider.default_model == "anthropic/claude-sonnet-4"
    assert provider._routing == {"order": ["Anthropic", "OpenAI"], "allow_fallbacks": True}


def test_factory_configures_azure_deployment_name():
    provider = create_provider_from_config(
        {
            "type": "azure",
            "api_key": "test-key",
            "base_url": "https://example.azure.com",
            "default_model": "prod-gpt4",
        }
    )

    assert isinstance(provider, AzureOpenAIProvider)
    assert provider.default_model == "prod-gpt4"


def test_manager_bootstraps_azure_and_openrouter_without_persisted_secrets():
    configs = ProviderManager()._default_provider_configs()

    assert configs["azure"]["type"] == "azure"
    assert configs["openrouter"]["type"] == "openrouter"
    assert configs["openrouter"]["options"]["routing"]["allow_fallbacks"] is True


@pytest.mark.asyncio
async def test_openrouter_forwards_core_routing_to_provider_request():
    captured: dict[str, object] = {}

    class Completions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return type(
                "Response",
                (),
                {
                    "model": "openai/gpt-4.1-mini",
                    "usage": None,
                    "choices": [
                        type(
                            "Choice",
                            (),
                            {
                                "message": type("Message", (), {"content": "ok"})(),
                                "finish_reason": "stop",
                            },
                        )()
                    ],
                },
            )()

    provider = OpenRouterProvider(
        api_key="test-key",
        routing={"order": ["OpenAI"], "allow_fallbacks": True},
    )
    provider._client = type(
        "Client", (), {"chat": type("Chat", (), {"completions": Completions()})()}
    )()

    await provider.chat([ChatMessage(role="user", content="hello")])

    assert captured["model"] == "openrouter/auto"
    assert captured["extra_body"] == {"provider": {"order": ["OpenAI"], "allow_fallbacks": True}}


# ── Chaque provider réellement supporté par la factory ─────────────────────


def test_factory_type_set_is_exactly_the_expected_classes():
    """Le mapping testé couvre EXACTEMENT les types supportés (aucun oubli)."""
    assert set(EXPECTED_CLASSES) == SUPPORTED_PROVIDER_TYPES


@pytest.mark.parametrize("provider_type", sorted(SUPPORTED_PROVIDER_TYPES))
def test_factory_builds_every_supported_type(provider_type: str):
    """Chaque type supporté produit une instance valide du bon adapter Core."""
    provider = create_provider_from_config(
        {
            "type": provider_type,
            "name": f"p-{provider_type}",
            "api_key": "test-key",
            "default_model": "unit-model",
        }
    )

    assert isinstance(provider, LLMProvider)
    assert isinstance(provider, EXPECTED_CLASSES[provider_type])
    assert provider.default_model == "unit-model"


@pytest.mark.parametrize("provider_type", sorted(DEFAULT_BASE_URLS))
def test_factory_applies_default_base_url_for_local_types(provider_type: str):
    """Les types locaux reçoivent l'URL par défaut de la table Core unique."""
    provider = create_provider_from_config({"type": provider_type, "name": f"u-{provider_type}"})
    assert provider._base_url == DEFAULT_BASE_URLS[provider_type]


def test_factory_all_types_have_auth_capability_metadata_in_catalog():
    """L'instance construite et le catalogue restent cohérents pour tout type."""
    manager = ProviderManager()
    catalog = manager.get_catalog()
    for entry in catalog["types"]:
        provider = create_provider_from_config({"type": entry["id"], "name": f"m-{entry['id']}"})
        assert isinstance(provider, LLMProvider)
        assert entry["auth_methods"]
        assert "llm" in entry["capabilities"]
