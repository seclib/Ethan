"""tests/test_provider_integration.py — Plan de tests d'intégration Provider Manager.

Couvre les 6 scénarios demandés :
1. Ollama local
2. Provider API OpenAI compatible
3. Provider désactivé
4. Mauvaise clé API
5. Perte réseau
6. Redémarrage ETHAN

Ces tests n'exercent AUCUN service externe réel : les providers sont mockés
pour simuler les comportements (succès, erreur, timeout, etc.).
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.llm.providers.base import LLMProvider
from core.llm.store import ProviderStore
from core.llm.provider_manager import ProviderManager
from core.llm.types import ChatMessage, ChatResponse, ModelInfo


# ── Helpers ──────────────────────────────────────────────────────────────

class FakeProvider(LLMProvider):
    """Provider factice configurable pour simuler les scénarios."""

    name = "fake"
    default_model = "m1"

    def __init__(self, chat_ok=True, list_ok=True, latency=0.0):
        self.chat_ok = chat_ok
        self.list_ok = list_ok
        self.latency = latency
        self.chat_calls = 0
        self.list_calls = 0

    async def initialize(self) -> None:
        pass

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=None, stream=False) -> ChatResponse:
        self.chat_calls += 1
        if self.latency:
            await asyncio.sleep(self.latency)
        if not self.chat_ok:
            raise RuntimeError("Provider chat failed")
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
        self.list_calls += 1
        if not self.list_ok:
            raise RuntimeError("Provider list_models failed")
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
        return self.list_ok

    async def close(self) -> None:
        pass


def _new_manager():
    return ProviderManager(store=ProviderStore())


# ═════════════════════════════════════════════════════════════════════════
# 1. OLLAMA LOCAL
# ═════════════════════════════════════════════════════════════════════════

def test_ollama_local_provider_initialized():
    """Le provider Ollama local est initialisé et listé par défaut."""

    async def run():
        manager = _new_manager()
        await manager.initialize()
        # Ollama est le provider par défaut
        assert manager._default_provider == "ollama"
        # Le provider est dans le registry
        assert manager._registry.get_provider("ollama") is not None
        # Le modèle par défaut est llama3.1
        assert manager._registry.get_provider("ollama").default_model == "llama3.1"

    asyncio.run(run())


def test_ollama_local_chat_uses_default_model():
    """Le chat Ollama utilise le modèle par défaut si aucun n'est spécifié."""

    async def run():
        manager = _new_manager()
        await manager.initialize()
        provider = manager._registry.get_provider("ollama")
        # Mock du client HTTP pour éviter tout appel réseau
        provider._client = AsyncMock()
        provider._client.post.return_value = MagicMock(
            raise_for_status=MagicMock(),
            json=MagicMock(return_value={
                "message": {"content": "bonjour"},
                "model": "llama3.1",
                "prompt_eval_count": 10,
                "eval_count": 5,
            }),
        )
        result = await provider.chat([ChatMessage(role="user", content="salut")])
        assert result.content == "bonjour"
        assert result.model == "llama3.1"
        assert result.provider == "ollama"
        # Vérifier que le modèle par défaut est bien envoyé
        call_kwargs = provider._client.post.call_args.kwargs
        assert call_kwargs["json"]["model"] == "llama3.1"

    asyncio.run(run())


# ═════════════════════════════════════════════════════════════════════════
# 2. PROVIDER API OPENAI COMPATIBLE
# ═════════════════════════════════════════════════════════════════════════

def test_openai_compatible_provider_registered():
    """Un provider openai-compatible peut être enregistré et utilisé."""

    async def run():
        manager = _new_manager()
        await manager.register_provider(
            config={
                "name": "my-compat",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "default_model": "gpt-4",
                "display_name": "My Compat",
                "enabled": True,
            },
        )
        provider = manager._registry.get_provider("my-compat")
        assert provider is not None
        assert provider.default_model == "gpt-4"
        # Le chat fonctionne via le client mocké
        provider._client = AsyncMock()
        provider._client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="réponse"), finish_reason="stop")],
            model="gpt-4",
            usage=MagicMock(prompt_tokens=5, completion_tokens=3, total_tokens=8),
        )
        result = await provider.chat([ChatMessage(role="user", content="test")])
        assert result.content == "réponse"
        assert result.model == "gpt-4"
        assert result.provider == "my-compat"

    asyncio.run(run())


# ═════════════════════════════════════════════════════════════════════════
# 3. PROVIDER DÉSACTIVÉ
# ═════════════════════════════════════════════════════════════════════════

def test_disabled_provider_not_in_registry():
    """Un provider désactivé n'est pas dans le registry et ne peut pas être utilisé."""

    async def run():
        manager = _new_manager()
        await manager.register_provider(
            config={
                "name": "disabled",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "default_model": "gpt-4",
                "enabled": False,
            },
        )
        # Désactivé → pas dans le registry
        assert manager._registry.get_provider("disabled") is None
        # La config est persistée avec enabled=False
        assert manager._providers_config["disabled"]["enabled"] is False
        # Le test de connexion échoue proprement
        result = await manager.test_connection("disabled")
        assert result["connected"] is False

    asyncio.run(run())


def test_disable_enabled_provider():
    """Désactiver un provider actif le retire du registry."""

    async def run():
        manager = _new_manager()
        await manager.register_provider(
            config={
                "name": "compat",
                "type": "openai-compatible",
                "base_url": "http://127.0.0.1:9/v1",
                "default_model": "gpt-4",
                "enabled": True,
            },
        )
        assert manager._registry.get_provider("compat") is not None
        await manager.set_enabled("compat", False)
        assert manager._registry.get_provider("compat") is None
        assert manager._providers_config["compat"]["enabled"] is False

    asyncio.run(run())


# ═════════════════════════════════════════════════════════════════════════
# 4. MAUVAISE CLÉ API
# ═════════════════════════════════════════════════════════════════════════

def test_bad_api_key_connection_fails():
    """Une mauvaise clé API → test_connection() retourne False."""

    async def run():
        manager = _new_manager()
        # Provider avec une clé invalide
        await manager.register_provider(
            config={
                "name": "bad-key",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "api_key": "sk-invalid",
                "default_model": "gpt-4",
                "enabled": True,
            },
        )
        provider = manager._registry.get_provider("bad-key")
        # Simuler une erreur 401 sur list_models
        provider._client = AsyncMock()
        provider._client.models.list.side_effect = Exception("401 Unauthorized")
        result = await manager.test_connection("bad-key")
        assert result["connected"] is False
        assert result["status"] == "error"

    asyncio.run(run())


def test_bad_api_key_chat_raises():
    """Une mauvaise clé API → chat() lève une erreur propre."""

    async def run():
        manager = _new_manager()
        await manager.register_provider(
            config={
                "name": "bad-key-2",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "api_key": "sk-invalid",
                "default_model": "gpt-4",
                "enabled": True,
            },
        )
        provider = manager._registry.get_provider("bad-key-2")
        provider._client = AsyncMock()
        provider._client.chat.completions.create.side_effect = Exception("401 Unauthorized")
        try:
            await provider.chat([ChatMessage(role="user", content="test")])
            assert False, "should have raised"
        except Exception as e:
            assert "401" in str(e)

    asyncio.run(run())


# ═════════════════════════════════════════════════════════════════════════
# 5. PERTE RÉSEAU
# ═════════════════════════════════════════════════════════════════════════

def test_network_loss_connection_fails():
    """Perte réseau → test_connection() retourne False sans crash."""

    async def run():
        manager = _new_manager()
        await manager.register_provider(
            config={
                "name": "offline",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "default_model": "gpt-4",
                "enabled": True,
            },
        )
        provider = manager._registry.get_provider("offline")
        provider._client = AsyncMock()
        provider._client.models.list.side_effect = Exception("Connection refused")
        result = await manager.test_connection("offline")
        assert result["connected"] is False
        assert result["status"] == "error"

    asyncio.run(run())


def test_network_loss_chat_raises():
    """Perte réseau → chat() lève une erreur propre."""

    async def run():
        manager = _new_manager()
        await manager.register_provider(
            config={
                "name": "offline-2",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "default_model": "gpt-4",
                "enabled": True,
            },
        )
        provider = manager._registry.get_provider("offline-2")
        provider._client = AsyncMock()
        provider._client.chat.completions.create.side_effect = Exception("Connection refused")
        try:
            await provider.chat([ChatMessage(role="user", content="test")])
            assert False, "should have raised"
        except Exception as e:
            assert "Connection refused" in str(e)

    asyncio.run(run())


def test_network_loss_list_models_returns_empty():
    """Perte réseau → list_models() retourne [] sans crash."""

    async def run():
        manager = _new_manager()
        await manager.register_provider(
            config={
                "name": "offline-3",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "default_model": "gpt-4",
                "enabled": True,
            },
        )
        provider = manager._registry.get_provider("offline-3")
        provider._client = AsyncMock()
        provider._client.models.list.side_effect = Exception("Connection refused")
        models = await provider.list_models()
        assert models == []

    asyncio.run(run())


# ═════════════════════════════════════════════════════════════════════════
# 6. REDÉMARRAGE ETHAN
# ═════════════════════════════════════════════════════════════════════════

def test_restart_preserves_provider_configs():
    """Après redémarrage, les configs providers sont restaurées depuis le store."""

    async def run():
        # Premier démarrage : enregistrer des providers
        store = ProviderStore()
        manager = ProviderManager(store=store)
        await manager.register_provider(
            config={
                "name": "persisted",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "default_model": "gpt-4",
                "display_name": "Persisted",
                "enabled": True,
            },
        )
        await manager.set_default_provider("persisted")

        # Simuler un redémarrage : nouveau manager avec le même store
        manager2 = ProviderManager(store=store)
        await manager2.initialize()
        # La config est restaurée
        assert "persisted" in manager2._providers_config
        assert manager2._providers_config["persisted"]["default_model"] == "gpt-4"
        # Le provider par défaut est restauré
        assert manager2._default_provider == "persisted"

    asyncio.run(run())


def test_restart_with_empty_store_seeds_defaults():
    """Après redémarrage avec store vide, les providers par défaut sont seedés."""

    async def run():
        store = ProviderStore()
        manager = ProviderManager(store=store)
        await manager.initialize()
        # Ollama est seedé et activé
        assert "ollama" in manager._providers_config
        assert manager._providers_config["ollama"]["enabled"] is True
        # Les providers cloud sont désactivés par défaut
        assert manager._providers_config["openai"]["enabled"] is False
        assert manager._providers_config["anthropic"]["enabled"] is False

    asyncio.run(run())


def test_restart_after_delete_removes_provider():
    """Après redémarrage, un provider supprimé n'est plus présent."""

    async def run():
        store = ProviderStore()
        manager = ProviderManager(store=store)
        await manager.register_provider(
            config={
                "name": "temp",
                "type": "openai-compatible",
                "base_url": "http://localhost:8000/v1",
                "default_model": "gpt-4",
                "enabled": True,
            },
        )
        await manager.unregister_provider("temp")

        # Redémarrage
        manager2 = ProviderManager(store=store)
        await manager2.initialize()
        assert "temp" not in manager2._providers_config

    asyncio.run(run())


# ═════════════════════════════════════════════════════════════════════════
# EXÉCUTION
# ═════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)

    tests = [
        test_ollama_local_provider_initialized,
        test_ollama_local_chat_uses_default_model,
        test_openai_compatible_provider_registered,
        test_disabled_provider_not_in_registry,
        test_disable_enabled_provider,
        test_bad_api_key_connection_fails,
        test_bad_api_key_chat_raises,
        test_network_loss_connection_fails,
        test_network_loss_chat_raises,
        test_network_loss_list_models_returns_empty,
        test_restart_preserves_provider_configs,
        test_restart_with_empty_store_seeds_defaults,
        test_restart_after_delete_removes_provider,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            print(f"  ✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")

    print(f"\n{passed}/{len(tests)} tests passed.")
    if passed != len(tests):
        sys.exit(1)