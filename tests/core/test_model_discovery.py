"""Tests unitaires pour la découverte de modèles (Hugging Face / Ollama / Cloud)."""

from __future__ import annotations

import pytest
from core.models.discovery import CURATED_MODEL_CATALOG, discover_catalog_models


def test_curated_model_catalog_content():
    """Le catalogue contient des modèles standards bien formés."""
    assert len(CURATED_MODEL_CATALOG) >= 5
    for item in CURATED_MODEL_CATALOG:
        assert "id" in item
        assert "name" in item
        assert "provider" in item
        assert "use_case" in item


def test_discover_catalog_models_enrichment():
    """Chaque modèle retourné est enrichi avec son statut de compatibilité matérielle."""
    mock_hw = {
        "total_ram_gb": 32.0,
        "available_ram_gb": 20.0,
        "cpu_cores": 16,
        "gpu_count": 1,
        "gpu_name": "RTX 4090",
        "gpu_vram_gb": 24.0,
        "gpu_vram_free_gb": 22.0,
        "backend": "cuda",
        "platform": "linux",
    }
    models = discover_catalog_models(hardware=mock_hw)
    assert len(models) == len(CURATED_MODEL_CATALOG)
    for m in models:
        assert "compatibility" in m
        compat = m["compatibility"]
        assert "compatible" in compat
        assert "fit_level" in compat
        assert "recommended_runtime" in compat


def test_discover_catalog_models_search_and_filter():
    """Le filtrage par mot-clé et use_case fonctionne correctement."""
    coding_models = discover_catalog_models(use_case="coding")
    assert all(m["use_case"] == "coding" for m in coding_models)

    qwen_models = discover_catalog_models(query="qwen")
    assert all("qwen" in m["name"].lower() or "qwen" in m["id"].lower() for m in qwen_models)
