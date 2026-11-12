"""Secrets des providers LLM — jamais persistés, jamais renvoyés (mandat sécurité).

``core/llm/provider_manager.py`` résout les clés API (secret manager/env, ou
saisie d'un rôle privilégié via l'API).  Ce sont des secrets : ils doivent
vivre en mémoire de processus uniquement (règle « secret » d'AGENTS.md).

Régression couverte (faille confirmée par audit) :

- ``_inject_secrets`` écrivait la clé env dans ``_providers_config`` ;
- ``ProviderManager.set_enabled`` persistait ensuite ``_providers_config`` tel
  quel via ``ProviderStore.save`` → la clé se retrouvait en PostgreSQL/Redis,
  en contradiction avec la doc du store (« les clés API ne sont JAMAIS
  persistées ici »).

Garantis ici :

- clé en mémoire (``_api_keys``) mais absente de la config sérialisable ;
- toute sauvegarde (``set_enabled``, ``register_provider``) persiste sans clé ;
- ``describe_provider`` n'expose qu'un booléen ``has_api_key`` ;
- une clé saisie pour un provider est mémorisée pour la session (un toggle ne
  la perd pas, et la factory la reçoit à la ré-instanciation).

Aucun service externe : store en mémoire + provider factice (pattern de
``tests/test_provider_manager.py``).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from core.llm.provider_manager import ProviderManager
from core.llm.providers.base import LLMProvider
from core.llm.store import ProviderStore
from core.llm.types import ChatResponse, ModelInfo


class FakeProvider(LLMProvider):
    """Provider factice non réseau implémentant l'interface LLMProvider."""

    name = "fake"
    default_model = "m1"

    def __init__(self) -> None:
        self.initialized = False

    async def initialize(self) -> None:
        self.initialized = True

    async def chat(
        self, messages, model=None, temperature=0.7, max_tokens=None, stream=False
    ) -> ChatResponse:
        return ChatResponse(content="ok", model=model or self.default_model, provider=self.name)

    async def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=None):
        yield "ok"

    async def embed(self, texts, model=None):
        return [[0.0 for _ in range(4)] for _ in texts]

    async def list_models(self):
        return [
            ModelInfo(
                id="m1",
                provider="fake",
                name="Fake Model",
                context_length=4096,
                is_local=True,
                is_private=True,
            )
        ]

    async def test_connection(self) -> bool:
        return True

    async def close(self) -> None:
        pass


def _manager() -> ProviderManager:
    """ProviderManager avec un store en mémoire (aucun service externe)."""
    return ProviderManager(store=ProviderStore())


def _set_openai_env() -> str:
    os.environ["OPENAI_API_KEY"] = "sk-audit-secret"
    return "sk-audit-secret"


def _clear_openai_env() -> None:
    os.environ.pop("OPENAI_API_KEY", None)


# ── Injection de secrets (env / secret manager) ─────────────────────────────


def test_inject_secrets_keeps_key_out_of_serializable_config():
    """La clé env vit dans ``_api_keys``, jamais dans ``_providers_config``."""

    async def run():
        secret = _set_openai_env()
        try:
            manager = _manager()
            manager._providers_config = manager._default_provider_configs()
            await manager._inject_secrets()

            config = manager._providers_config["openai"]
            assert config["enabled"] is True  # auto-activé par la clé
            assert "api_key" not in config  # config sérialisable = sans secret
            assert manager.api_key_for("openai") == secret
            assert "api_key" not in manager._public_config("openai")
        finally:
            _clear_openai_env()

    asyncio.run(run())


def test_set_enabled_persists_config_without_api_key():
    """Le bug confirmé : un toggle ne doit JAMAIS écrire la clé dans le store."""

    async def run():
        secret = _set_openai_env()
        try:
            manager = _manager()
            manager._providers_config = manager._default_provider_configs()
            await manager._inject_secrets()

            result = await manager.set_enabled("openai", False)

            persisted = await manager._store.get("openai")
            assert persisted is not None
            assert "api_key" not in persisted
            assert persisted["enabled"] is False
            # La clé reste disponible pour la session, sans être sérialisée.
            assert manager.api_key_for("openai") == secret
            assert "api_key" not in result
            assert result["has_api_key"] is True
        finally:
            _clear_openai_env()

    asyncio.run(run())


def test_reenable_passes_memorized_key_to_factory(monkeypatch):
    """La ré-instanciation reçoit la clé mémorisée — sans réécrire le store."""

    async def run():
        secret = _set_openai_env()
        try:
            import core.llm.provider_manager as pm

            captured: dict[str, Any] = {}

            def _fake_factory(config):
                captured.update(config)
                return FakeProvider()

            monkeypatch.setattr(pm, "create_provider_from_config", _fake_factory)

            manager = _manager()
            manager._providers_config = manager._default_provider_configs()
            await manager._inject_secrets()
            await manager.set_enabled("openai", False)
            await manager.set_enabled("openai", True)

            assert captured.get("api_key") == secret
            assert "api_key" not in await manager._store.get("openai")
        finally:
            _clear_openai_env()

    asyncio.run(run())


# ── Clés saisies par un rôle privilégié (POST/PUT /providers) ───────────────


def test_register_provider_memorizes_key_but_persists_clean():
    """Une clé saisie est utilisable en session, jamais persistée/renvoyée."""

    async def run():
        manager = _manager()
        result = await manager.register_provider(
            provider=FakeProvider(),
            config={
                "name": "fake",
                "type": "fake",
                "enabled": True,
                "display_name": "Fake",
                "default_model": "m1",
                "api_key": "sk-typed-by-admin",
            },
        )

        assert manager.api_key_for("fake") == "sk-typed-by-admin"
        persisted = await manager._store.get("fake")
        assert "api_key" not in persisted
        assert "api_key" not in result
        assert result["has_api_key"] is True

    asyncio.run(run())


def test_describe_provider_never_serializes_the_key():
    """``describe_provider`` : booléen uniquement, jamais la valeur."""

    async def run():
        manager = _manager()
        manager._providers_config["openai"] = {
            "name": "openai",
            "type": "openai",
            "enabled": False,
            "base_url": "",
            "default_model": "gpt-4o-mini",
        }
        manager.remember_api_key("openai", "sk-hidden-value")

        desc = await manager.describe_provider("openai")
        assert desc["has_api_key"] is True
        assert "api_key" not in desc
        assert "sk-hidden-value" not in str(desc)

    asyncio.run(run())


def test_public_config_strips_legacy_residual_key():
    """Défense en profondeur : un résidu de clé en config n'est jamais persisté."""
    manager = _manager()
    manager._providers_config["legacy"] = {
        "name": "legacy",
        "type": "openai",
        "enabled": False,
        "api_key": "old-leak",
    }
    public = manager._public_config("legacy")
    assert "api_key" not in public
    assert public["name"] == "legacy"
