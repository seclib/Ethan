"""Tests API — catalogue des providers (route /providers/catalog).

Valide la passerelle HTTP du catalogue Core :
- la liste des types vient de la factory Core (aucune liste parallèle) ;
- chaque type expose URL par défaut, méthodes d'authentification et
  capacités canoniques ;
- la route est déclarée AVANT /{provider_id} (sinon « catalog » serait
  interprété comme un identifiant de provider) ;
- un provider inconnu/inactif est signalé sans lever 500 ;
- aucun secret n'est exposé.
"""

# Ruff : les imports suivent l'insertion de ROOT dans sys.path.
# ruff: noqa: E402

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import pytest_asyncio
from core.llm.provider_factory import DEFAULT_BASE_URLS
from core.llm.provider_manager import ProviderManager
from core.llm.store import ProviderStore
from fastapi import HTTPException
from interfaces.api.routers import providers as providers_router


@pytest_asyncio.fixture()
async def manager():
    """ProviderManager en mémoire, injecté dans le routeur (état réel)."""
    mgr = ProviderManager(store=ProviderStore())
    providers_router.set_provider_manager(mgr)
    yield mgr
    providers_router.set_provider_manager(None)  # type: ignore[arg-type]


# ── Catalogue ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_catalog_endpoint_returns_core_types(manager):
    """GET /providers/catalog expose les types supportés par le Core."""
    from core.llm.provider_factory import SUPPORTED_PROVIDER_TYPES

    catalog = await providers_router.get_provider_catalog()
    ids = [entry["id"] for entry in catalog["types"]]
    assert ids == sorted(SUPPORTED_PROVIDER_TYPES)
    assert "ollama" in ids and "openai-compatible" in ids


@pytest.mark.asyncio
async def test_catalog_endpoint_exposes_default_urls_and_auth(manager):
    """Chaque type expose URL par défaut, auth methods et capacités."""
    catalog = await providers_router.get_provider_catalog()
    by_id = {entry["id"]: entry for entry in catalog["types"]}

    assert by_id["ollama"]["default_base_url"] == DEFAULT_BASE_URLS["ollama"]
    assert by_id["ollama"]["auth_methods"] == ["api_key"]
    assert "llm" in by_id["ollama"]["capabilities"]

    assert catalog["provider_capabilities"] == [
        "llm",
        "vision",
        "embedding",
        "speech_to_text",
        "transcription",
    ]


@pytest.mark.asyncio
async def test_catalog_endpoint_never_exposes_secrets(manager):
    """Pas de champ clé API ni valeur secrète dans la réponse."""
    catalog = await providers_router.get_provider_catalog()
    payload = str(catalog).lower()
    assert "'api_key':" not in payload
    for forbidden in ("secret", "token", "password", "sk-"):
        assert forbidden not in payload


def test_catalog_route_declared_before_provider_id_route():
    """Régression : /catalog doit être matché avant /{provider_id}."""
    paths = [route.path for route in providers_router.router.routes]
    catalog_index = paths.index("/providers/catalog")
    provider_id_index = paths.index("/providers/{provider_id}")
    assert catalog_index < provider_id_index


@pytest.mark.asyncio
async def test_catalog_endpoint_503_without_manager():
    """Sans ProviderManager, le catalogue répond 503 (pas 500)."""
    providers_router.set_provider_manager(None)  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as exc_info:
        await providers_router.get_provider_catalog()
    assert exc_info.value.status_code == 503


# ── Provider indisponible ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_models_endpoint_inactive_provider_returns_404(manager):
    """GET /providers/{id}/models : provider inactif → 404 explicite."""
    await manager._store.save("sleepy", {"name": "sleepy", "type": "ollama", "enabled": False})
    manager._providers_config["sleepy"] = {
        "name": "sleepy",
        "type": "ollama",
        "enabled": False,
    }
    with pytest.raises(HTTPException) as exc_info:
        await providers_router.list_provider_models("sleepy")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_providers_survives_unavailable_provider(manager):
    """Un provider en erreur n'empêche pas la liste (cause racine exposée)."""
    await manager._store.save(
        "down",
        {
            "name": "down",
            "type": "ollama",
            "enabled": True,
            "base_url": "http://127.0.0.1:1",
        },
    )
    manager._providers_config["down"] = {
        "name": "down",
        "type": "ollama",
        "enabled": True,
        "base_url": "http://127.0.0.1:1",
    }

    described = await manager.describe_provider("down")
    assert described["status"] == "error"
    assert described["models"] == []

    listed = await providers_router.list_providers()
    assert any(p.id == "down" for p in listed)
