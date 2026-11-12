"""Tests for ``LLMClient`` default-model resolution.

Régression : ``LLMClient.chat()`` échouait quand le ``default_model`` configuré
ne correspondait à aucun identifiant exact du registre (ex. « llama3.1 » déclaré
en configuration, « llama3.1:latest » renvoyé par le provider).  ``get_model()``
renvoyait alors ``None`` et l'appel HTTP partait sans modèle → 502 côté API.

Les tests utilisent un faux provider (aucun réseau) et vérifient :
- la résolution exacte, par préfixe de tag, et le repli déterministe ;
- l'appel effectif du provider avec le BON identifiant de modèle ;
- l'absence de ``AttributeError`` dans le suivi de coût quand aucun modèle
  n'est connu du registre.
"""

from __future__ import annotations

import asyncio

from core.llm.client import LLMClient
from core.llm.registry import LLMProviderRegistry
from core.llm.selector import LLMSelector
from core.llm.types import ChatMessage, ChatResponse, ModelInfo


class _FakeProvider:
    """Provider minimal : expose des modèles et mémorise le modèle appelé."""

    name = "ollama"

    def __init__(self, default_model: str | None = "llama3.1") -> None:
        self.default_model = default_model
        self.models = [
            ModelInfo(id="llama3.1:latest", provider="ollama", name="Llama 3.1"),
            ModelInfo(id="qwen2.5:7b", provider="ollama", name="Qwen 2.5"),
        ]
        self.calls: list[str | None] = []

    def list_models(self) -> list[ModelInfo]:
        return self.models

    async def chat(self, messages: list[ChatMessage], model: str | None = None) -> ChatResponse:
        self.calls.append(model)
        return ChatResponse(
            content="ok",
            model=model or "",
            provider=self.name,
            usage={"total_tokens": 3},
        )


def _build_client(provider: _FakeProvider) -> tuple[LLMClient, LLMProviderRegistry]:
    registry = LLMProviderRegistry()
    registry.register_provider(provider)
    return LLMClient(registry, LLMSelector()), registry


# ── Résolution du modèle par défaut ────────────────────────────────────────


def test_exact_default_model_is_used():
    provider = _FakeProvider(default_model="qwen2.5:7b")
    client, _ = _build_client(provider)

    model, _ = client._select_model(None)

    assert model is not None
    assert model.id == "qwen2.5:7b"


def test_default_model_without_tag_resolves_to_registry_id():
    """« llama3.1 » (config) doit résoudre « llama3.1:latest » (registre)."""
    provider = _FakeProvider(default_model="llama3.1")
    client, _ = _build_client(provider)

    model, _ = client._select_model(None)

    assert model is not None
    assert model.id == "llama3.1:latest"


def test_unknown_default_model_falls_back_to_first_provider_model():
    provider = _FakeProvider(default_model="inexistant")
    client, _ = _build_client(provider)

    model, _ = client._select_model(None)

    assert model is not None
    assert model.id == "llama3.1:latest"


def test_absent_default_model_falls_back_to_first_provider_model():
    provider = _FakeProvider(default_model=None)
    client, _ = _build_client(provider)

    model, _ = client._select_model(None)

    assert model is not None
    assert model.id == "llama3.1:latest"


def test_no_model_available_returns_none():
    provider = _FakeProvider(default_model="llama3.1")
    provider.models = []
    client, _ = _build_client(provider)

    model, _ = client._select_model(None)

    assert model is None


# ── Appel effectif du provider ─────────────────────────────────────────────


def test_chat_sends_resolved_model_id_to_provider():
    """Non-régression : le provider reçoit l'identifiant résolu, jamais None."""
    provider = _FakeProvider(default_model="llama3.1")
    client, _ = _build_client(provider)

    response = asyncio.run(client.chat([ChatMessage(role="user", content="hi")]))

    assert response.content == "ok"
    assert provider.calls == ["llama3.1:latest"]


def test_chat_without_any_model_passes_none_and_tracks_cost():
    """Aucun modèle au registre → le provider reçoit ``None`` sans planter.

    Régression : ``_cost_tracker.track(model.provider, model.id, …)`` levait un
    ``AttributeError`` quand ``model`` était ``None`` ; le repli doit utiliser le
    nom du provider effectivement appelé.
    """
    provider = _FakeProvider()
    provider.models = []
    client, _ = _build_client(provider)

    asyncio.run(client.initialize())
    response = asyncio.run(client.chat([ChatMessage(role="user", content="hi")]))

    assert response.content == "ok"
    assert provider.calls == [None]
    # Le suivi de coût ne doit plus lever d'AttributeError (régression) :
    # l'appel est bien comptabilisé, sous la clé de repli du provider.
    assert sum(entry["calls"] for entry in client._cost_tracker.get_usage().values()) == 1


def test_cost_tracking_uses_resolved_model():
    """Le suivi de coût reçoit le modèle résolu, jamais « unknown »."""
    provider = _FakeProvider(default_model="llama3.1")
    client, _ = _build_client(provider)

    asyncio.run(client.initialize())
    asyncio.run(client.chat([ChatMessage(role="user", content="hi")]))

    assert client._cost_tracker is not None
    assert client._cost_tracker.get_usage("ollama:llama3.1:latest")["calls"] == 1
