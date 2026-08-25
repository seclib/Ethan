"""Tests for Core-owned provider construction and OpenRouter routing."""

import pytest

from core.llm.provider_factory import create_provider_from_config
from core.llm.provider_manager import ProviderManager
from core.llm.providers.azure import AzureOpenAIProvider
from core.llm.providers.openrouter import OpenRouterProvider
from core.llm.types import ChatMessage


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
        {"type": "azure", "api_key": "test-key", "base_url": "https://example.azure.com", "default_model": "prod-gpt4"}
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
                    "choices": [type("Choice", (), {"message": type("Message", (), {"content": "ok"})(), "finish_reason": "stop"})()],
                },
            )()

    provider = OpenRouterProvider(
        api_key="test-key",
        routing={"order": ["OpenAI"], "allow_fallbacks": True},
    )
    provider._client = type("Client", (), {"chat": type("Chat", (), {"completions": Completions()})()})()

    await provider.chat([ChatMessage(role="user", content="hello")])

    assert captured["model"] == "openrouter/auto"
    assert captured["extra_body"] == {"provider": {"order": ["OpenAI"], "allow_fallbacks": True}}
