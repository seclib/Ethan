"""Tests du surface IA Providers ↔ Models (core/llm/provider_manager).

Contrat de distinction (refonte AI — sans architecture parallèle) :

- **Providers** = services/instances : la clé du registry est l'ID
  D'INSTANCE ; l'adapter ne connaît que son type (« azure », « ollama »…).
- **Models** = modèles exposés par ces providers : `ModelInfo.provider` est
  réconcilié vers l'id d'instance au fil de l'eau — c'est ce champ qui
  pilote le routage Core (`LLMClient` → `registry.get_provider(model.provider)`),
  le filtre `preferred_providers` de `core/chat/pipeline.py` et la
  résolution provider↔modèle de la WebUI.
- **Capabilities** = métadonnées réellement fournies (instance → flags ;
  provider désactivé → type déclaré par le Core) — jamais inventées.
- **Indisponibilité** = état honnête (`status=error`, `models=[]`), sans 500.

Réseau contrôlé : un vrai serveur HTTP local pour le « disponible » et un
port fermé pour l'« indisponible » — aucun accès Internet requis.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest
from core.llm.provider_manager import ProviderManager
from core.llm.store import ProviderStore
from core.llm.types import ModelInfo

pytestmark = pytest.mark.asyncio

# URL dont la connexion est refusée immédiatement (port fermé, localhost).
_CLOSED_PORT = "http://127.0.0.1:9"


class FakeProvider:
    """Adapter factice dont le ``name`` (type) diffère de l'id d'instance.

    C'est exactement le cas des providers créés avec un id personnalisé
    (« mon-azure ») : l'adapter stampe « azure » dans ``ModelInfo.provider``.
    """

    name = "azure"  # type d'adapter — ce que l'adapter stampait avant fix
    default_model = "gpt-4"

    def __init__(self) -> None:
        self.initialized = False

    async def initialize(self) -> None:
        self.initialized = True

    async def list_models(self) -> list[ModelInfo]:
        # Nouvelle instance à chaque appel (comme un vrai adapter) : le
        # stamping doit survivre à la ré-instanciation.
        return [
            ModelInfo(
                id="gpt-4o",
                provider=self.name,
                name="GPT-4o",
                model="gpt-4o",
                pricing={"input": 2.5, "output": 10.0},
                avg_latency_ms=2000.0,
            ),
            ModelInfo(
                id="gpt-4o-mini",
                provider=self.name,
                name="GPT-4o mini",
                model="gpt-4o-mini",
                pricing={"input": 0.15, "output": 0.6},
                avg_latency_ms=500.0,
            ),
        ]

    async def test_connection(self) -> bool:
        return True


@pytest.fixture()
def manager() -> ProviderManager:
    """ProviderManager en mémoire (aucun PG/Redis requis)."""
    return ProviderManager(store=ProviderStore())


# ── Providers (instances) vs Models (exposés) ─────────────────────────────
class TestInstanceVsType:
    async def test_list_models_rattache_a_instance(self, manager: ProviderManager) -> None:
        """Un modèle découvert appartient à l'INSTANCE, jamais au type."""
        fake = FakeProvider()
        manager._registry._providers["mon-azure"] = fake

        models = await manager.list_models()
        assert models, "le fake doit exposer des modèles"
        assert {m.provider for m in models} == {"mon-azure"}

        # Résolution Core : LLMClient fait registry.get_provider(m.provider)
        # — avec le type (« azure ») elle retournait None (chat en échec).
        assert manager._registry.get_provider(models[0].provider) is fake

    async def test_list_models_filtre_par_instance(self, manager: ProviderManager) -> None:
        manager._registry._providers["mon-azure"] = FakeProvider()
        manager._providers_config["mon-azure"] = {
            "name": "mon-azure",
            "type": "azure",
            "enabled": True,
        }

        models = await manager.list_models("mon-azure")
        assert models, "le filtre par instance doit trouver les modèles"
        assert all(m.provider == "mon-azure" for m in models)

    async def test_register_stampe_registry(self, manager: ProviderManager) -> None:
        """L'enregistrement stamppe aussi le registre de modèles partagé."""
        fake = FakeProvider()
        config = {"name": "mon-azure", "type": "azure", "enabled": True}
        await manager.register_provider(provider=fake, config=config)

        stored = manager._registry.get_model("gpt-4o")
        assert stored is not None
        assert stored.provider == "mon-azure"
        assert manager._registry.get_provider(stored.provider) is fake

    async def test_stamping_idempotent(self, manager: ProviderManager) -> None:
        """Deux lectures consécutives restent cohérentes (aucune bascule)."""
        manager._registry._providers["mon-azure"] = FakeProvider()
        first = await manager.list_models()
        second = await manager.list_models()
        assert [m.provider for m in first] == [m.provider for m in second] == ["mon-azure"] * 2


# ── Provider indisponible : état honnête, jamais de crash ─────────────────
_UNAVAILABLE_CONFIG: dict[str, Any] = {
    "name": "custom",
    "type": "openai-compatible",
    "enabled": True,
    "base_url": _CLOSED_PORT,
    "default_model": "local-model",
    "api_key": "test-key",  # mémoire uniquement — jamais persistée ici
}


class TestProviderIndisponible:
    async def test_test_connection_honnete(self, manager: ProviderManager) -> None:
        manager._providers_config["custom"] = dict(_UNAVAILABLE_CONFIG)
        result = await manager.test_connection("custom")
        assert result["connected"] is False
        assert result["status"] == "error"
        assert result["message"]

    async def test_describe_sans_crash_et_capacites_reelles(
        self, manager: ProviderManager
    ) -> None:
        manager._providers_config["custom"] = dict(_UNAVAILABLE_CONFIG)
        desc = await manager.describe_provider("custom")
        assert desc["status"] == "error"  # honnête : injoignable
        assert desc["enabled"] is True
        assert desc["models"] == []  # aucun modèle inventé
        # Capacités déclarées par le type Core — jamais vides pour un type connu
        assert "llm" in desc["capabilities"]
        # La clé n'est jamais sérialisée (booléen seulement)
        assert desc["has_api_key"] is True

    async def test_list_models_indisponible_vide(self, manager: ProviderManager) -> None:
        manager._providers_config["custom"] = dict(_UNAVAILABLE_CONFIG)
        assert await manager.list_models("custom") == []
        # La vue globale reste vide sans lever (registry vide)
        assert await manager.list_models() == []

    async def test_describe_desactive_sans_healthcheck(
        self, manager: ProviderManager
    ) -> None:
        manager._providers_config["anthropic"] = {
            "name": "anthropic",
            "type": "anthropic",
            "enabled": False,
        }
        desc = await manager.describe_provider("anthropic")
        assert desc["status"] == "unknown"  # pas de test pour un désactivé
        assert desc["capabilities"] == ["llm", "vision"]  # table de type Core
        assert desc["has_api_key"] is False


# ── Provider disponible : vrai HTTP local ─────────────────────────────────
class _OllamaStubHandler(BaseHTTPRequestHandler):
    """Endpoint /api/tags — contrat exact de l'adapter Ollama."""

    def do_GET(self) -> None:  # noqa: N802 — signature http.server
        if self.path == "/api/tags":
            body = json.dumps({"models": [{"name": "qwen2.5-coder:7b"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def log_message(self, *args: Any) -> None:
        """Silencieux — pas de bruit dans la sortie pytest."""


@pytest.fixture()
def ollama_stub():
    """Vrai serveur HTTP local (127.0.0.1, port éphémère)."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _OllamaStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


class TestProviderDisponible:
    async def test_ollama_connecte_et_modeles_exposes(
        self, manager: ProviderManager, ollama_stub: str
    ) -> None:
        await manager.register_provider(
            config={
                "name": "ollama",
                "type": "ollama",
                "enabled": True,
                "base_url": ollama_stub,
                "default_model": "qwen2.5-coder:7b",
            }
        )

        result = await manager.test_connection("ollama")
        assert result["connected"] is True
        assert result["status"] == "connected"

        models = await manager.list_models("ollama")
        assert [m.id for m in models] == ["qwen2.5-coder:7b"]
        assert all(m.provider == "ollama" for m in models)

        desc = await manager.describe_provider("ollama")
        assert desc["status"] == "connected"
        assert desc["models"] == ["qwen2.5-coder:7b"]
        assert desc["default_model"] == "qwen2.5-coder:7b"
        assert "llm" in desc["capabilities"]

    async def test_capabilities_instance_inscrites(
        self, manager: ProviderManager, ollama_stub: str
    ) -> None:
        await manager.register_provider(
            config={
                "name": "ollama",
                "type": "ollama",
                "enabled": True,
                "base_url": ollama_stub,
            }
        )
        caps = manager.get_provider_capabilities("ollama")
        assert "llm" in caps["capabilities"]
        assert caps["supports_embedding"] is True  # drapeau réel de l'adapter


# ── Modèle par défaut (provider = service exposant des modèles) ───────────
class TestDefaultModel:
    async def test_default_model_declare_et_resolu(
        self, manager: ProviderManager
    ) -> None:
        manager._providers_config["custom"] = {
            "name": "custom",
            "type": "openai-compatible",
            "enabled": True,
            "base_url": _CLOSED_PORT,
            "default_model": "local-model",
        }
        desc = await manager.describe_provider("custom")
        assert desc["default_model"] == "local-model"
        assert await manager.get_active_model("custom") == "local-model"
