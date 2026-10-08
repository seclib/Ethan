"""Tests unitaires et d'intégration pour le Model Hub d'ETHAN Core."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from core.hardware.fit import check_model_compatibility
from core.llm.model_store import ModelStore
from core.llm.provider_manager import ProviderManager
from core.models.hub import ModelHub, get_model_hub
from core.state.record_store import CoreRecordStore


def test_singleton_get_model_hub():
    """get_model_hub retourne une instance unique et initialisée."""
    hub1 = get_model_hub()
    hub2 = get_model_hub()
    assert hub1 is hub2
    assert isinstance(hub1, ModelHub)


@pytest.mark.asyncio
async def test_model_hub_discover_curated():
    """discover retourne les modèles du catalogue avec statut de compatibilité."""
    hub = ModelHub()
    mock_hw = {
        "total_ram_gb": 32.0,
        "available_ram_gb": 24.0,
        "cpu_cores": 16,
        "gpu_count": 1,
        "gpu_name": "RTX 4090",
        "gpu_vram_gb": 24.0,
        "gpu_vram_free_gb": 22.0,
        "backend": "cuda",
    }
    models = await hub.discover(use_case="coding", hardware=mock_hw)
    assert len(models) >= 1
    for m in models:
        assert "compatibility" in m
        assert m["compatibility"]["status"] in (
            "compatible",
            "compatible_with_constraints",
            "incompatible",
            "insufficient_info",
        )
        assert "execution_method" in m["compatibility"]


@pytest.mark.asyncio
async def test_model_hub_inspect_answers_capability_and_method():
    """inspect répond à « Ce modèle peut-il fonctionner, et par quelle méthode ? »"""
    hub = ModelHub()
    mock_hw = {
        "total_ram_gb": 32.0,
        "available_ram_gb": 24.0,
        "cpu_cores": 16,
        "gpu_count": 1,
        "gpu_name": "RTX 4090",
        "gpu_vram_gb": 24.0,
        "gpu_vram_free_gb": 22.0,
        "backend": "cuda",
    }

    # 1. Modèle 7B sur RTX 4090 -> compatible GPU
    res_7b = await hub.inspect("Qwen/Qwen2.5-Coder-7B-Instruct-GGUF", hardware=mock_hw)
    assert res_7b["can_run"] is True
    assert res_7b["status"] == "compatible"
    assert res_7b["status_label"] == "Compatible"
    assert "GPU" in res_7b["method"]
    assert "gguf" in res_7b["formats_available"]
    assert res_7b["conversion_supported"] is False

    # 2. Modèle sur CPU uniquement -> compatible avec contraintes
    mock_cpu_hw = {
        "total_ram_gb": 16.0,
        "available_ram_gb": 10.0,
        "cpu_cores": 8,
        "gpu_count": 0,
        "gpu_vram_gb": 0.0,
        "gpu_vram_free_gb": 0.0,
        "backend": "cpu",
    }
    res_cpu = await hub.inspect("llama3.2:3b", hardware=mock_cpu_hw)
    assert res_cpu["can_run"] is True
    assert res_cpu["status"] == "compatible_with_constraints"
    assert res_cpu["status_label"] == "Compatible avec contraintes"
    assert "Processeur" in res_cpu["method"] or "CPU" in res_cpu["method"]

    # 3. Modèle 70B sur petite machine -> incompatible
    mock_tiny_hw = {
        "total_ram_gb": 8.0,
        "available_ram_gb": 3.0,
        "cpu_cores": 4,
        "gpu_count": 0,
        "gpu_vram_gb": 0.0,
        "backend": "cpu",
    }
    res_70b = await hub.inspect("llama-3.1-70b", hardware=mock_tiny_hw)
    assert res_70b["can_run"] is False
    assert res_70b["status"] == "incompatible"
    assert res_70b["status_label"] == "Incompatible"
    assert "insuffisante" in res_70b["reason"].lower()

    # 4. Modèle Cloud -> compatible sans ressources locales
    res_cloud = await hub.inspect("gpt-4o-mini", hardware=mock_tiny_hw)
    assert res_cloud["can_run"] is True
    assert res_cloud["status"] == "compatible"
    assert "Cloud" in res_cloud["method"]


@pytest.mark.asyncio
async def test_model_hub_inspect_insufficient_info():
    """Un modèle sans paramètre ni taille identifiée renvoie 'information insuffisante'."""
    compat = check_model_compatibility("inconnu-sans-params", params_b=0.0)
    assert compat.status == "insufficient_info"
    assert compat.status_label == "Information insuffisante"
    assert compat.compatible is False


@pytest.mark.asyncio
async def test_model_hub_install_registers_in_store():
    """L'installation via ModelHub enregistre la fiche modèle prête à l'emploi."""
    hub = ModelHub()
    record_store = CoreRecordStore()
    model_store = ModelStore(store=record_store)

    mock_hw = {
        "total_ram_gb": 32.0,
        "available_ram_gb": 20.0,
        "cpu_cores": 16,
        "gpu_count": 1,
        "gpu_vram_gb": 24.0,
        "gpu_vram_free_gb": 22.0,
        "backend": "cuda",
    }

    mock_response = MagicMock(status_code=200)
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await hub.install(
            model_id="qwen2.5:7b",
            provider_hint="ollama",
            store=model_store,
            hardware=mock_hw,
        )
    assert result["success"] is True
    assert result["runtime"] == "ollama"

    # Vérifier l'inscription
    installed = await hub.list_installed(store=model_store)
    assert any(m["id"] == "qwen2.5:7b" or m["name"] == "qwen2.5:7b" for m in installed)


@pytest.mark.asyncio
async def test_model_hub_runtime_health():
    """check_runtime_health teste les runtimes sans bloquer."""
    hub = ModelHub()
    manager = ProviderManager(store=None)
    await manager.initialize()

    health = await hub.check_runtime_health(manager=manager)
    assert "status" in health
    assert "runtimes" in health
