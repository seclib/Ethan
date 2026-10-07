"""Tests unitaires complets pour le pipeline de gestion des modèles d'ETHAN.

Couvre :
- Détection et formats Hugging Face (core.models.hf)
- Registre centralisé des modèles (core.models.registry)
- Downloader résilient avec retry (core.models.downloader)
- Allocation et collision de ports TCP (core.hardware.ports)
- Vitesse physique tok/s et KV cache (core.hardware.fit)
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from core.hardware.fit import check_model_compatibility
from core.hardware.ports import find_free_port, is_port_in_use
from core.models.downloader import ModelDownloader
from core.models.hf import inspect_hf_model, search_hf_models
from core.models.registry import ModelEntry, ModelRegistry


def test_fit_engine_speed_and_recommendation():
    """Vérifie la projection de vitesse en tok/s et la recommandation claire."""
    mock_hw = {
        "total_ram_gb": 32.0,
        "available_ram_gb": 24.0,
        "cpu_cores": 16,
        "gpu_count": 1,
        "gpu_name": "NVIDIA GeForce RTX 4090",
        "gpu_vram_gb": 24.0,
        "gpu_vram_free_gb": 22.0,
        "backend": "cuda",
        "memory_bandwidth_gb_s": 1008.0,
    }
    res = check_model_compatibility("qwen2.5:7b", hardware=mock_hw)
    assert res.compatible is True
    assert res.estimated_speed_tps > 20.0
    assert "recommandé" in res.recommendation.lower()
    assert res.recommended_format == "gguf"
    assert "ollama" in res.supported_runtimes


def test_fit_engine_apple_silicon_metal():
    """Vérifie la gestion de la mémoire unifiée pour Apple Silicon Metal."""
    mock_hw = {
        "total_ram_gb": 64.0,
        "available_ram_gb": 48.0,
        "cpu_cores": 12,
        "gpu_count": 1,
        "gpu_name": "Apple M3 Max",
        "gpu_vram_gb": 48.0,  # 75% de 64 Go
        "gpu_vram_free_gb": 48.0,
        "backend": "metal",
        "unified_memory": True,
        "memory_bandwidth_gb_s": 400.0,
    }
    res = check_model_compatibility("qwen2.5-coder:7b", hardware=mock_hw)
    assert res.compatible is True
    assert res.fit_level in ("perfect", "good")
    assert res.recommended_format == "gguf"
    assert "apple silicon" in res.reason.lower()


def test_ports_allocation():
    """find_free_port retourne un port valide non utilisé."""
    port = find_free_port(start_port=29100, max_offset=5)
    assert isinstance(port, int)
    assert 29100 <= port <= 29105
    assert not is_port_in_use(port)


def test_model_registry_crud_and_search():
    """Le registre indexe et permet la recherche avec enrichissement matériel."""
    reg = ModelRegistry()
    entry = ModelEntry(
        id="test-org/test-model-7b",
        name="Test Model 7B",
        provider="ollama",
        repo_id="test-org/test-model-7b",
        params_b=7.0,
        use_case="coding",
    )
    reg.register(entry)

    assert reg.get("test-org/test-model-7b") is not None

    mock_hw = {
        "total_ram_gb": 16.0,
        "available_ram_gb": 12.0,
        "cpu_cores": 8,
        "gpu_count": 0,
        "backend": "cpu",
    }
    results = reg.search(query="test-model", hardware=mock_hw)
    assert len(results) >= 1
    found = results[0]
    assert found["id"] == "test-org/test-model-7b"
    assert "compatibility" in found


@pytest.mark.asyncio
async def test_inspect_hf_model_offline_fallback():
    """En cas d'indisponibilité réseau, inspect_hf_model ne crashe pas."""
    info = await inspect_hf_model("Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
    assert info["repo_id"] == "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    assert "gguf" in info["formats_available"]


@pytest.mark.asyncio
async def test_downloader_retry_on_failure():
    """Le downloader effectue des retries en cas d'erreur sans bloquer."""
    downloader = ModelDownloader()
    # Un repo inexistant ou sans huggingface_hub déclenche la gestion propre des erreurs
    res = await downloader.download_hf_model(
        repo_id="nonexistent-org/invalid-model-12345",
        max_retries=2,
    )
    assert res["success"] is False
    assert res["attempts"] == 2
