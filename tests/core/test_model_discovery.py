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


@pytest.mark.asyncio
async def test_discover_models_async_use_case_filters_hf_results(monkeypatch):
    """Le filtre use_case s'applique aussi aux résultats HF live.

    Les entrées HF sont catégorisées « general » (usage réel inconnu du
    Core) : un filtre explicite doit donc les écarter plutôt que de leur
    inventer une catégorie.
    """
    from unittest.mock import AsyncMock

    from core.models import discovery

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
    monkeypatch.setattr(
        discovery,
        "search_hf_models",
        AsyncMock(
            return_value=[
                {
                    "id": "hf-org/tiny-model",
                    "name": "Tiny Model",
                    "repo_id": "hf-org/tiny-model",
                    "pipeline_tag": "text-generation",
                    "formats_available": ["gguf"],
                }
            ]
        ),
    )

    # use_case="general" → le modèle HF (catégorisé « general ») est conservé.
    general = await discovery.discover_models_async(
        query="zzz-unmatched-by-catalog", use_case="general", hardware=mock_hw
    )
    assert any(m["source"] == "huggingface" for m in general)

    # use_case="coding" → le modèle HF live est écarté (usage inconnu).
    coding = await discovery.discover_models_async(
        query="zzz-unmatched-by-catalog", use_case="coding", hardware=mock_hw
    )
    assert all(m["source"] != "huggingface" for m in coding)


@pytest.mark.asyncio
async def test_discover_models_hf_source_without_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """source="huggingface" interroge HF même sans terme de recherche.

    Régression D2 : la condition ``query.strip()`` excluait systématiquement
    Hugging Face sur source explicite — l'utilisateur choisissait Hugging Face
    et obtenait 0 résultat. ``source="all"`` sans terme reste réservé au
    catalogue curaté pour ne pas être noyé par le top HF.
    """
    from core.models import discovery

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
    calls: list[str | None] = []

    async def _fake_search(query: str, limit: int = 5) -> list[dict]:
        calls.append(query)
        return [
            {
                "id": "hf-org/top-model",
                "name": "Top Model",
                "repo_id": "hf-org/top-model",
                "pipeline_tag": "text-generation",
                "formats_available": ["gguf"],
            }
        ]

    monkeypatch.setattr(discovery, "search_hf_models", _fake_search)

    hf_results = await discovery.discover_models_async(
        query="", source="huggingface", hardware=mock_hw
    )
    assert calls == [""]
    assert any(m["source"] == "huggingface" for m in hf_results)

    calls.clear()
    all_results = await discovery.discover_models_async(
        query="", source="all", hardware=mock_hw
    )
    assert calls == []
    assert all(m["source"] != "huggingface" for m in all_results)
