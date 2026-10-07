"""Tests unitaires pour l'orchestrateur d'installation et de décision de runtime."""

from __future__ import annotations

import pytest
from core.llm.model_installer import (
    determine_execution_strategy,
    install_or_use_model,
)
from core.llm.model_store import ModelStore
from core.llm.provider_manager import ProviderManager
from core.state.record_store import CoreRecordStore


def test_determine_execution_strategy_cloud():
    """Détecte les modèles Cloud et associe le bon runtime."""
    s_openai = determine_execution_strategy("gpt-4o-mini")
    assert s_openai["runtime"] == "cloud"
    assert s_openai["provider_type"] == "openai"
    assert s_openai["compatible"] is True

    s_claude = determine_execution_strategy("claude-3-5-sonnet-20241022")
    assert s_claude["runtime"] == "cloud"
    assert s_claude["provider_type"] == "anthropic"

    s_gemini = determine_execution_strategy("gemini-2.5-flash")
    assert s_gemini["runtime"] == "cloud"
    assert s_gemini["provider_type"] == "gemini"


def test_determine_execution_strategy_huggingface_gguf():
    """Les modèles Hugging Face GGUF sont mappés pour Ollama via hf.co/ si compatibles."""
    mock_hw = {
        "total_ram_gb": 32.0,
        "available_ram_gb": 20.0,
        "cpu_cores": 16,
        "gpu_count": 1,
        "gpu_vram_gb": 24.0,
        "gpu_vram_free_gb": 22.0,
        "backend": "cuda",
    }
    strat = determine_execution_strategy("Qwen/Qwen2.5-Coder-7B-Instruct-GGUF", hardware=mock_hw)
    assert strat["compatible"] is True
    assert strat["runtime"] == "ollama"
    assert strat["target_model_name"] == "hf.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"


def test_determine_execution_strategy_incompatible():
    """Un modèle trop grand pour le matériel est rejeté proprement sans forcer de runtime."""
    mock_hw = {
        "total_ram_gb": 8.0,
        "available_ram_gb": 3.0,
        "cpu_cores": 4,
        "gpu_count": 0,
        "gpu_vram_gb": 0.0,
        "gpu_vram_free_gb": 0.0,
        "backend": "cpu",
    }
    strat = determine_execution_strategy("deepseek-ai/DeepSeek-V3", hardware=mock_hw)
    assert strat["compatible"] is False
    assert strat["action"] == "reject"
    assert "incompatible" in strat["reason"].lower()


@pytest.mark.asyncio
async def test_install_or_use_model_cloud_success():
    """L'installation d'un modèle Cloud configure et active le provider dans ProviderManager."""
    store = CoreRecordStore()
    manager = ProviderManager(store=None)
    await manager.initialize()

    result = await install_or_use_model("gpt-4o-mini", manager=manager)
    assert result["success"] is True
    assert result["runtime"] == "cloud"
    assert result["provider"] == "openai"


@pytest.mark.asyncio
async def test_install_or_use_model_local_registers_in_model_store():
    """Un modèle local compatible est enregistré dans le ModelStore."""
    record_store = CoreRecordStore()
    model_store = ModelStore(store=record_store)

    result = await install_or_use_model(
        "qwen2.5-coder:7b",
        provider_hint="ollama",
        store=model_store,
    )
    assert result["success"] is True
    assert result["runtime"] == "ollama"

    # Vérifier que la fiche a été créée
    models = await model_store.list_models()
    assert any(m["model"] == "qwen2.5-coder:7b" for m in models)
