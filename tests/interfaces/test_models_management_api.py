"""Tests pour les routes API de gestion, découverte et compatibilité des modèles."""

from __future__ import annotations

import pytest
from core.llm.model_store import ModelStore
from core.llm.provider_manager import ProviderManager
from core.state.record_store import CoreRecordStore
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from interfaces.api.routers.models import (
    router,
    set_model_store,
    set_provider_manager,
)


@pytest.fixture
def setup_models_env():
    """Initialise l'environnement de test avec ProviderManager et ModelStore."""
    manager = ProviderManager(store=None)
    set_provider_manager(manager)

    store = ModelStore(store=CoreRecordStore())
    set_model_store(store)

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_api_get_hardware(setup_models_env):
    """GET /models/hardware renvoie la configuration matérielle."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/models/hardware")
        assert res.status_code == 200
        data = res.json()
        assert "total_ram_gb" in data
        assert "cpu_cores" in data
        assert "backend" in data


@pytest.mark.asyncio
async def test_api_discover_models(setup_models_env):
    """GET /models/discover renvoie la liste enrichie des modèles et compatibilités."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/models/discover?use_case=coding")
        assert res.status_code == 200
        items = res.json()
        assert len(items) > 0
        assert all("compatibility" in m for m in items)


@pytest.mark.asyncio
async def test_api_check_compatibility(setup_models_env):
    """POST /models/check-compatibility évalue le modèle passé en payload."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/models/check-compatibility", json={"model": "qwen2.5:7b"})
        assert res.status_code == 200
        data = res.json()
        assert "compatible" in data
        assert "fit_level" in data
        assert "recommended_runtime" in data


@pytest.mark.asyncio
async def test_api_install_model(setup_models_env):
    """POST /models/install installe et rend le modèle disponible."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/models/install",
            json={"model": "llama3.2:3b", "provider": "ollama"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "prêt" in data["message"].lower() or "installé" in data["message"].lower()


@pytest.mark.asyncio
async def test_api_get_installed_models(setup_models_env):
    """GET /models/installed renvoie la liste des modèles disponibles."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/models/installed")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_api_inspect_model(setup_models_env):
    """GET /models/inspect/{model_id} inspecte les capacités et la méthode d'exécution."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/models/inspect/qwen2.5:7b")
        assert res.status_code == 200
        data = res.json()
        assert "can_run" in data
        assert "status" in data
        assert "status_label" in data
        assert "method" in data
        assert "formats_available" in data


@pytest.mark.asyncio
async def test_api_runtimes_health(setup_models_env):
    """GET /models/runtimes/health vérifie les statuts des runtimes."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/models/runtimes/health")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "runtimes" in data


@pytest.mark.asyncio
async def test_api_list_downloads(setup_models_env):
    """GET /models/downloads liste les tâches de téléchargement."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/models/downloads")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_api_get_storage_layout(setup_models_env):
    """GET /models/storage renvoie la disposition de stockage."""
    transport = ASGITransport(app=setup_models_env)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/models/storage")
        assert res.status_code == 200
        data = res.json()
        assert "models_dir" in data
        assert "downloads_dir" in data
        assert "artifacts_dir" in data
        assert "registry_dir" in data
        assert "installed_dir" in data
        assert "metadata_dir" in data
        assert "tmp_dir" in data
        assert data["models_dir"].endswith("/models")


