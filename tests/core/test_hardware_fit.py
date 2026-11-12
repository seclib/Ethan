"""Tests unitaires pour la détection hardware et l'adéquation mémoire ("What Fits?")."""

from __future__ import annotations

import pytest
from core.hardware.detector import get_system_hardware
from core.hardware.fit import (
    QUANT_BPP,
    check_model_compatibility,
    parse_params_b,
)


def test_get_system_hardware_structure():
    """Vérifie que la sonde hardware renvoie toujours les clés obligatoires."""
    hw = get_system_hardware()
    assert isinstance(hw, dict)
    assert "total_ram_gb" in hw
    assert "available_ram_gb" in hw
    assert "cpu_cores" in hw
    assert "gpu_count" in hw
    assert "backend" in hw
    assert hw["total_ram_gb"] > 0
    assert hw["cpu_cores"] >= 1


def test_parse_params_b():
    """Vérifie la déduction du nombre de paramètres depuis différents formats."""
    assert parse_params_b("qwen2.5-7b") == 7.0
    assert parse_params_b("llama-3.1-70b-instruct") == 70.0
    assert parse_params_b("phi-4-14b") == 14.0
    assert parse_params_b("deepseek-r1-distill-qwen-1.5b") == 1.5
    assert parse_params_b("smollm2-135m") == 0.135


def test_check_model_compatibility_cloud():
    """Les modèles Cloud sont toujours compatibles et ne requièrent aucune RAM locale."""
    res = check_model_compatibility("gpt-4o-mini")
    assert res.compatible is True
    assert res.fit_level == "perfect"
    assert res.recommended_runtime == "cloud"
    assert res.vram_required_gb == 0.0

    res_claude = check_model_compatibility("claude-3-5-sonnet-20241022")
    assert res_claude.compatible is True
    assert res_claude.recommended_runtime == "cloud"


def test_check_model_compatibility_fits_gpu():
    """Un modèle de 7B (Q4 ~5 Go) tient parfaitement sur un GPU de 24 Go."""
    mock_hw = {
        "total_ram_gb": 32.0,
        "available_ram_gb": 24.0,
        "cpu_cores": 16,
        "gpu_count": 1,
        "gpu_name": "RTX 4090",
        "gpu_vram_gb": 24.0,
        "gpu_vram_free_gb": 22.0,
        "backend": "cuda",
        "platform": "linux",
    }
    res = check_model_compatibility("qwen2.5:7b", hardware=mock_hw)
    assert res.compatible is True
    assert res.fit_level == "perfect"
    assert res.vram_required_gb > 0
    assert res.vram_required_gb < 10.0


def test_check_model_compatibility_too_tight():
    """Un modèle de 70B (Q4 ~42 Go) dépasse une machine de 8 Go RAM sans GPU."""
    mock_hw = {
        "total_ram_gb": 8.0,
        "available_ram_gb": 4.0,
        "cpu_cores": 4,
        "gpu_count": 0,
        "gpu_name": None,
        "gpu_vram_gb": 0.0,
        "gpu_vram_free_gb": 0.0,
        "backend": "cpu",
        "platform": "linux",
    }
    res = check_model_compatibility("llama-3.1-70b", hardware=mock_hw)
    assert res.compatible is False
    assert res.fit_level == "too_tight"
    assert "insuffisante" in res.reason.lower()


def test_check_model_compatibility_marginal_cpu():
    """Un modèle de 3B tient en RAM disponible sur CPU."""
    mock_hw = {
        "total_ram_gb": 16.0,
        "available_ram_gb": 10.0,
        "cpu_cores": 8,
        "gpu_count": 0,
        "gpu_name": None,
        "gpu_vram_gb": 0.0,
        "gpu_vram_free_gb": 0.0,
        "backend": "cpu",
        "platform": "linux",
    }
    res = check_model_compatibility("llama3.2:3b", hardware=mock_hw)
    assert res.compatible is True
    assert res.fit_level == "marginal"
    assert res.recommended_runtime == "ollama"
