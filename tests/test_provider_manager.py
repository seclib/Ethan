"""tests/test_provider_manager.py — tests unitaires du ProviderManager LLM.

Ces tests n'exercent AUCUN service externe (pas de NATS, Redis, Postgres,
ni provider réel) : le ProviderStore est en mémoire et le provider est une
implémentation factice. Ils valident la logique de gestion, de persistance
et d'injection de secrets du ProviderManager.
"""

import asyncio
import os
import sys
from pathlib import Path

# Le projet racine doit être sur le chemin d'import (conftest.py le fait déjà,
# mais on est explicites pour pouvoir lancer le fichier seul).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.llm.providers.base import LLMProvider
from core.llm.store import ProviderStore
from core.llm.provider_manager import ProviderManager
from core.llm.types import ChatMessage, ChatResponse, ModelInfo


class FakeProvider(LLMProvider):
    """Provider factice non réseau implémentant l'interface LLMProvider."""

    name = "fake"
    default_model = "m1"

    def __init__(self):
        self.initialized = False
        self.chat_calls = 0

    async def initialize(self) -> None:
        self.initialized = True

    async def chat(
        self,
        messages,
        model=None,
        temperature=0.7,
        max_tokens=None,
        stream=False,
    ) -> ChatResponse:
        self.chat_calls += 1
        return ChatResponse(
            content="hello from fake",
            model=model or self.default_model,
            provider=self.name,
        )

    async def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=None):
        yield "hello"

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


def _new_manager():
    """ProviderManager avec un store en mémoire (pas de Redis/Postgres)."""
    return ProviderManager(store=ProviderStore())


# ── ProviderStore (mémoire) ─────────────────────────────────────────────

def test_store_save_get_delete_roundtrip():
    """Le store en mémoire persiste / lit / supprime les configs."""

    async def run():
        store = ProviderStore()
        assert await store.get_all() == {}
        assert await store.get("missing") is None

        await store.save("ollama", {"type": "ollama", "enabled": True})
        assert (await store.get("ollama"))["type"] == "ollama"

        deleted = await store.delete("ollama")
        assert deleted is True
        assert await store.get("ollama") is None
        # Supprimer un absent renvoie False
        assert await store.delete("nope") is False

    asyncio.run(run())


def test_store_default_provider_fallback():
    """get_default() renvoie le premier provider activé."""

    async def run():
        store = ProviderStore()
        await store.save("a", {"enabled": False})
        await store.save("b", {"enabled": True})
        assert await store.get_default() == "b"
        assert await store.get_default() == "b"  # mis en cache mémoire

    asyncio.run(run())


# ── ProviderManager ─────────────────────────────────────────────────────

def test_manager_constructs_without_services():
    """Le manager s'installe sans Redis/Postgres."""
    manager = _new_manager()
    assert manager._providers_config == {}
    assert manager._default_provider is None
    assert manager._registry.list_providers() == []


def test_default_provider_configs_shape():
    """Les configs par défaut seedent ollama activé + cloud désactivés."""
    manager = _new_manager()
    configs = manager._default_provider_configs()
    assert set(configs.keys()) == {"ollama", "openai", "anthropic", "vllm", "custom"}
    assert configs["ollama"]["enabled"] is True
    assert configs["openai"]["enabled"] is False
    assert configs["openai"]["type"] == "openai"
    assert configs["custom"]["type"] == "openai-compatible"
    # Aucune clé API dans les configs seedées
    for cfg in configs.values():
        assert "api_key" not in cfg


def test_inject_secrets_enables_openai(monkeypatch=None):
    """Une clé env OPENAI_API_KEY active openai ET injecte la clé en mémoire."""

    async def run():
        os.environ["OPENAI_API_KEY"] = "sk-test-123"
        try:
            manager = _new_manager()
            manager._providers_config = manager._default_provider_configs()
            await manager._inject_secrets()
            openai = manager._providers_config["openai"]
            assert openai["enabled"] is True
            assert openai["api_key"] == "sk-test-123"
            # Anthropic reste désactivé tant qu'il n'a pas de clé
            assert manager._providers_config["anthropic"]["enabled"] is False
        finally:
            del os.environ["OPENAI_API_KEY"]

    asyncio.run(run())


def test_register_provider_strips_api_key():
    """register_provider persiste la config SANS la clé API."""

    async def run():
        manager = _new_manager()
        fake = FakeProvider()
        result = await manager.register_provider(
            provider=fake,
            config={
                "name": "fake",
                "type": "fake",
                "enabled": True,
                "display_name": "Fake",
                "default_model": "m1",
                "api_key": "super-secret",
            },
        )
        assert result["id"] == "fake"
        assert result["enabled"] is True
        assert result["status"] == "connected"
        # La clé API ne doit jamais être renvoyée ni persistée
        assert result.get("api_key") is None
        persisted = manager._store._memory.get("fake", {})
        assert "api_key" not in persisted
        # Le provider est bien enregistré dans le registry
        assert manager._registry.get_provider("fake") is fake

    asyncio.run(run())


def test_list_providers_exposes_state():
    async def run():
        manager = _new_manager()
        await manager.register_provider(
            provider=FakeProvider(),
            config={"name": "fake", "type": "fake", "display_name": "Fake", "default_model": "m1"},
        )
        providers = await manager.list_providers()
        assert len(providers) == 1
        p = providers[0]
        assert p["id"] == "fake"
        assert p["name"] == "Fake"
        assert p["status"] == "connected"
        assert p["models"] == ["m1"]

    asyncio.run(run())


def test_test_connection_ok():
    async def run():
        manager = _new_manager()
        await manager.register_provider(
            provider=FakeProvider(),
            config={"name": "fake", "type": "fake", "default_model": "m1"},
        )
        result = await manager.test_connection("fake")
        assert result["connected"] is True
        assert result["status"] == "connected"

    asyncio.run(run())


def test_default_model_and_set_default():
    async def run():
        manager = _new_manager()
        await manager.register_provider(
            provider=FakeProvider(),
            config={"name": "fake", "type": "fake", "default_model": "m1"},
        )
        # Définir explicitement le provider par défaut
        await manager.set_default_provider("fake")
        default = await manager.get_default_provider()
        assert default is not None
        assert default["id"] == "fake"
        assert default["is_default"] is True
        # Le modèle actif correspond au default_model configuré
        assert await manager.get_active_model() == "m1"

    asyncio.run(run())


def test_unregister_provider():
    async def run():
        manager = _new_manager()
        await manager.register_provider(
            provider=FakeProvider(),
            config={"name": "fake", "type": "fake", "default_model": "m1"},
        )
        assert await manager.unregister_provider("fake") is True
        assert manager._registry.get_provider("fake") is None
        assert manager._store._memory.get("fake") is None
        # Supprimer un absent → False
        assert await manager.unregister_provider("nope") is False

    asyncio.run(run())


def test_set_enabled_toggles_provider():
    async def run():
        manager = _new_manager()
        # Type supporté par la factory (nécessaire pour le ré-enable via
        # create_provider_from_config). base_url sur un port refusé → refus
        # instantané, aucun service réel requis.
        cfg = {
            "name": "compat",
            "type": "openai-compatible",
            "base_url": "http://127.0.0.1:9/v1",
            "default_model": "gpt-4",
            "display_name": "Compat",
            "enabled": True,
        }
        await manager.register_provider(config=cfg)
        assert manager._registry.get_provider("compat") is not None

        # Désactiver → retire du registry, persiste enabled=False
        await manager.set_enabled("compat", False)
        assert manager._registry.get_provider("compat") is None
        assert manager._providers_config["compat"]["enabled"] is False

        # Réactiver → ré-installe via la factory et ré-enregistre
        await manager.set_enabled("compat", True)
        assert manager._registry.get_provider("compat") is not None
        desc = await manager.describe_provider("compat")
        assert desc["enabled"] is True

    asyncio.run(run())


def test_test_connection_unknown_provider_raises():
    async def run():
        manager = _new_manager()
        try:
            await manager.test_connection("does-not-exist")
            assert False, "should have raised"
        except ValueError:
            pass

    asyncio.run(run())


def test_initialize_seeds_in_memory_and_registers_ollama():
    """initialize() seed les configs et instancie ollama (mémoire)."""

    async def run():
        manager = _new_manager()
        await manager.initialize()
        ids = manager._registry.list_providers()
        assert "ollama" in ids
        # Le store mémoire a bien les configs seedées
        all_configs = await manager._store.get_all()
        assert "ollama" in all_configs
        assert all_configs["ollama"]["enabled"] is True
        # Le provider par défaut est ollama
        assert manager._default_provider == "ollama"

    asyncio.run(run())


def test_close_does_not_raise_without_services():
    async def run():
        manager = _new_manager()
        await manager.initialize()
        # close() doit être safe même si le store n'a pas de redis/pg
        await manager.close()

    asyncio.run(run())


if __name__ == "__main__":
    # Permet de lancer le fichier directement : python tests/test_provider_manager.py
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)
    test_store_save_get_delete_roundtrip()
    test_store_default_provider_fallback()
    test_manager_constructs_without_services()
    test_default_provider_configs_shape()
    test_inject_secrets_enables_openai()
    test_register_provider_strips_api_key()
    test_list_providers_exposes_state()
    test_test_connection_ok()
    test_default_model_and_set_default()
    test_unregister_provider()
    test_set_enabled_toggles_provider()
    test_test_connection_unknown_provider_raises()
    test_initialize_seeds_in_memory_and_registers_ollama()
    test_close_does_not_raise_without_services()
    print("All provider_manager tests passed.")
