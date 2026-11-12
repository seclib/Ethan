"""Moteur d'adéquation matérielle ("What Fits?") d'ETHAN.

Calcule l'empreinte mémoire requise par un modèle (poids + KV cache paramétrable),
projette le débit en tokens/seconde (memory-bus bound) et évalue la compatibilité
matérielle selon les formats (GGUF, Safetensors) et runtimes (Ollama, llama.cpp, vLLM).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .detector import get_system_hardware

# Table de Bytes-Per-Parameter (BPP) par type de quantification
QUANT_BPP: dict[str, float] = {
    "F32": 4.0,
    "F16": 2.0,
    "BF16": 2.0,
    "FP8": 1.0,
    "INT8": 1.0,
    "Q8_0": 1.05,
    "Q6_K": 0.80,
    "Q5_K_M": 0.68,
    "Q4_K_M": 0.58,
    "Q4_0": 0.58,
    "Q3_K_M": 0.48,
    "Q2_K": 0.37,
    "AWQ": 0.58,
    "GPTQ": 0.58,
    "INT4": 0.58,
}

# Facteur multiplicateur pour le KV Cache selon la quantification du cache
KV_CACHE_FACTORS: dict[str, float] = {
    "f16": 2.0,
    "bf16": 2.0,
    "q8_0": 1.0,
    "q4_0": 0.5,
}

DEFAULT_BPP = 0.58


@dataclass
class CompatibilityResult:
    """Résultat complet de l'analyse de compatibilité d'un modèle."""

    compatible: bool
    fit_level: str  # "perfect" | "good" | "marginal" | "too_tight"
    vram_required_gb: float
    ram_required_gb: float
    recommended_runtime: str  # "ollama" | "llamacpp" | "vllm" | "sglang" | "cloud"
    recommended_format: str  # "gguf" | "safetensors" | "cloud"
    estimated_speed_tps: float
    reason: str
    recommendation: str
    status: str = "compatible"  # "compatible" | "compatible_with_constraints" | "incompatible" | "insufficient_info"
    status_label: str = "Compatible"  # "Compatible" | "Compatible avec contraintes" | "Incompatible" | "Information insuffisante"
    execution_method: str = ""
    supported_runtimes: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "status": self.status,
            "status_label": self.status_label,
            "execution_method": self.execution_method,
            "fit_level": self.fit_level,
            "vram_required_gb": self.vram_required_gb,
            "ram_required_gb": self.ram_required_gb,
            "recommended_runtime": self.recommended_runtime,
            "recommended_format": self.recommended_format,
            "estimated_speed_tps": self.estimated_speed_tps,
            "reason": self.reason,
            "recommendation": self.recommendation,
            "supported_runtimes": self.supported_runtimes,
            "details": self.details,
        }


def parse_params_b(model_name: str) -> float:
    """Extrait le nombre de paramètres en milliards (B) depuis le nom d'un modèle."""
    name = model_name.lower()

    # Modèles géants connus (DeepSeek V3 / R1 = 671B)
    if "deepseek-v3" in name or (
        "deepseek-r1" in name
        and not any(k in name for k in ("distill", "1.5b", "7b", "8b", "14b", "32b", "70b"))
    ):
        return 671.0

    # Détection des millions (ex: 135m -> 0.135)
    match_m = re.search(r"[-_/:](\d+(?:\.\d+)?)\s*m\b", name)
    if match_m:
        return round(float(match_m.group(1)) / 1000.0, 3)

    # Détection des milliards avec suffixe explicite 'b' (ex: 7b -> 7.0, 1.5b -> 1.5, 70b -> 70.0)
    match_b = re.search(r"[-_/:]?(\d+(?:\.\d+)?)\s*b\b", name)
    if match_b:
        return float(match_b.group(1))

    # Chercher un nombre avec suffixe de taille (ex: -7B-, _70B_)
    match_suffix = re.search(r"\b(\d+(?:\.\d+)?)[bB]\b", model_name)
    if match_suffix:
        return float(match_suffix.group(1))

    return 7.0


def check_model_compatibility(
    model_name: str,
    params_b: float | None = None,
    quantization: str | None = None,
    context_length: int = 4096,
    is_vision: bool = False,
    kv_cache_type: str = "q8_0",
    hardware: dict[str, Any] | None = None,
) -> CompatibilityResult:
    """Calcule l'adéquation matérielle et les options d'exécution pour un modèle.

    Args:
        model_name: Nom ou identifiant du modèle (ex: "qwen2.5:7b", "meta-llama/Llama-3.1-8B")
        params_b: Nombre de paramètres en milliards (déduit du nom si None)
        quantization: Format de quantification (ex: "Q4_K_M", "FP8", "F16")
        context_length: Contexte ciblé en tokens (default: 4096)
        is_vision: Indique si le modèle est multimodal/vision (ajoute 1.1 Go pour le projecteur CLIP)
        kv_cache_type: Type de KV Cache ("f16", "q8_0", "q4_0")
        hardware: Spécifications matérielles fournies (détectées automatiquement si None)

    Returns:
        CompatibilityResult avec recommandations, vitesse projetée et runtimes supportés.
    """
    sys_hw = hardware or get_system_hardware()
    p_billions = params_b if params_b is not None else parse_params_b(model_name)
    name_lower = model_name.lower()

    # 1. Cas des modèles Cloud
    is_cloud = any(
        name_lower.startswith(p)
        for p in ("gpt-", "o1-", "o3-", "o4-", "claude-", "gemini-", "openrouter/")
    )
    if is_cloud:
        return CompatibilityResult(
            compatible=True,
            fit_level="perfect",
            status="compatible",
            status_label="Compatible",
            execution_method="API Cloud (distante)",
            vram_required_gb=0.0,
            ram_required_gb=0.0,
            recommended_runtime="cloud",
            recommended_format="cloud",
            estimated_speed_tps=60.0,
            reason="Modèle hébergé dans le Cloud (API distante).",
            recommendation="Prêt à l'emploi — aucune ressource GPU/RAM requise sur votre machine.",
            supported_runtimes=["cloud"],
            details={"is_cloud": True},
        )

    # 1.b Cas des modèles sans information de taille
    if p_billions is None or p_billions <= 0:
        return CompatibilityResult(
            compatible=False,
            fit_level="too_tight",
            status="insufficient_info",
            status_label="Information insuffisante",
            execution_method="Non déterminable",
            vram_required_gb=0.0,
            ram_required_gb=0.0,
            recommended_runtime="unknown",
            recommended_format="unknown",
            estimated_speed_tps=0.0,
            reason="Taille et paramètres du modèle inconnus ou non spécifiés.",
            recommendation="Précisez le nombre de paramètres ou inspectez le dépôt source avant déploiement.",
            supported_runtimes=[],
            details={"params_billions": 0.0},
        )

    # 2. Détermination du format et des BPP
    bpp = DEFAULT_BPP
    if quantization and quantization.upper() in QUANT_BPP:
        bpp = QUANT_BPP[quantization.upper()]
    elif "q8" in name_lower or "fp8" in name_lower:
        bpp = 1.05
    elif "f16" in name_lower or "bf16" in name_lower:
        bpp = 2.0
    elif "q4" in name_lower or "awq" in name_lower or "int4" in name_lower:
        bpp = 0.58

    # Calcul taille des poids et KV cache
    weights_gb = p_billions * bpp
    kv_factor = KV_CACHE_FACTORS.get(kv_cache_type.lower(), 1.0)
    kv_cache_gb = 8e-6 * (p_billions * 1e9) * context_length * kv_factor / (1024**3)

    # Marge de sécurité (0.4 Go texte, 1.1 Go si vision/multimodal)
    headroom_gb = 1.1 if is_vision else 0.4
    total_required_gb = round(weights_gb + kv_cache_gb + headroom_gb, 1)

    # Métriques système
    total_ram = sys_hw.get("total_ram_gb", 8.0)
    avail_ram = sys_hw.get("available_ram_gb", 4.0)
    gpu_vram = sys_hw.get("gpu_vram_gb", 0.0)
    gpu_vram_free = sys_hw.get("gpu_vram_free_gb", 0.0)
    backend = sys_hw.get("backend", "cpu")
    bandwidth = sys_hw.get("memory_bandwidth_gb_s", 55.0)

    # Estimation du débit en tokens/seconde (Memory bus bound)
    active_weights = max(0.5, weights_gb)
    raw_tps = (bandwidth / active_weights) * 0.55
    estimated_speed_tps = round(min(180.0, max(2.0, raw_tps)), 1)

    # 3. Règles d'adéquation matérielle et sélection de runtime
    fit_level = "too_tight"
    status = "incompatible"
    status_label = "Incompatible"
    execution_method = ""
    compatible = False
    recommended_runtime = "ollama"
    recommended_format = "gguf"
    supported_runtimes = []
    reason = ""
    recommendation = ""

    if backend == "metal":  # Apple Silicon (Unified Memory)
        usable_ram = total_ram * 0.75
        if total_required_gb <= usable_ram:
            compatible = True
            fit_level = "perfect" if total_required_gb <= usable_ram * 0.7 else "good"
            status = "compatible"
            status_label = "Compatible"
            execution_method = "Apple Silicon Metal (Mémoire unifiée)"
            recommended_runtime = "ollama"
            recommended_format = "gguf"
            supported_runtimes = ["ollama", "llamacpp"]
            reason = f"Exécution fluide sur Apple Silicon ({total_required_gb:.1f} Go / {usable_ram:.1f} Go attribuables)."
            recommendation = f"Recommandé pour votre puce Apple Silicon — vitesse estimée ~{estimated_speed_tps} tok/s."
        else:
            compatible = False
            fit_level = "too_tight"
            status = "incompatible"
            status_label = "Incompatible"
            execution_method = "Non exécutable (Mémoire unifiée insuffisante)"
            reason = f"Mémoire insuffisante sur Apple Silicon ({total_required_gb:.1f} Go requis pour {usable_ram:.1f} Go max)."
            recommendation = (
                "Modèle trop volumineux pour votre machine. Choisissez une variante plus légère."
            )

    elif gpu_vram > 0 and backend == "cuda":  # NVIDIA CUDA
        supported_runtimes = ["ollama", "llamacpp", "vllm"]
        if total_required_gb <= gpu_vram_free:
            compatible = True
            fit_level = "perfect"
            status = "compatible"
            status_label = "Compatible"
            execution_method = f"GPU NVIDIA ({gpu_vram:.0f} Go VRAM)"
            recommended_runtime = "vllm" if p_billions >= 14 else "ollama"
            recommended_format = "safetensors" if recommended_runtime == "vllm" else "gguf"
            reason = f"Exécution 100% VRAM GPU ({total_required_gb:.1f} Go / {gpu_vram_free:.1f} Go VRAM libre)."
            recommendation = f"Recommandé pour votre GPU NVIDIA — vitesse maximale en VRAM ~{estimated_speed_tps} tok/s."
        elif total_required_gb <= gpu_vram:
            compatible = True
            fit_level = "good"
            status = "compatible"
            status_label = "Compatible"
            execution_method = f"GPU NVIDIA ({gpu_vram:.0f} Go VRAM, charge élevée)"
            recommended_runtime = "ollama"
            recommended_format = "gguf"
            reason = f"Exécution sur GPU VRAM ({total_required_gb:.1f} Go / {gpu_vram:.1f} Go VRAM totale)."
            recommendation = (
                f"Compatible en mémoire GPU (charge élevée) — vitesse ~{estimated_speed_tps} tok/s."
            )
        elif total_required_gb <= (gpu_vram + avail_ram):
            compatible = True
            fit_level = "marginal"
            status = "compatible_with_constraints"
            status_label = "Compatible avec contraintes"
            execution_method = "Hybride GPU + CPU offload"
            recommended_runtime = "ollama"
            recommended_format = "gguf"
            estimated_speed_tps = round(estimated_speed_tps * 0.35, 1)
            reason = f"Exécution hybride GPU + CPU offload ({total_required_gb:.1f} Go requis, dépasse la VRAM de {gpu_vram:.1f} Go)."
            recommendation = f"Compatible avec partage GPU/CPU (vitesse réduite ~{estimated_speed_tps} tok/s)."
        else:
            compatible = False
            fit_level = "too_tight"
            status = "incompatible"
            status_label = "Incompatible"
            execution_method = "Non exécutable (VRAM et RAM insuffisantes)"
            reason = f"Mémoire système insuffisante ({total_required_gb:.1f} Go requis / {gpu_vram + total_ram:.1f} Go total)."
            recommendation = (
                "Modèle trop volumineux pour votre matériel. Privilégiez une version plus petite."
            )

    else:  # CPU uniquement (Linux x86 / AMD APU / etc.)
        supported_runtimes = ["ollama", "llamacpp"]
        recommended_format = "gguf"
        if total_required_gb <= avail_ram:
            compatible = True
            fit_level = "marginal"
            status = "compatible_with_constraints"
            status_label = "Compatible avec contraintes"
            execution_method = "Processeur hôte / CPU RAM"
            recommended_runtime = "ollama"
            estimated_speed_tps = round(min(15.0, (55.0 / active_weights) * 0.4), 1)
            reason = f"Exécution sur processeur/RAM ({total_required_gb:.1f} Go requis / {avail_ram:.1f} Go RAM libre)."
            recommendation = f"Compatible processeur (vitesse modérée ~{estimated_speed_tps} tok/s)."
        else:
            compatible = False
            fit_level = "too_tight"
            status = "incompatible"
            status_label = "Incompatible"
            execution_method = "Non exécutable (RAM hôte insuffisante)"
            reason = f"RAM libre insuffisante pour le processeur ({total_required_gb:.1f} Go requis / {avail_ram:.1f} Go disponibles)."
            recommendation = "Mémoire RAM insuffisante pour exécuter ce modèle sur votre processeur."

    return CompatibilityResult(
        compatible=compatible,
        fit_level=fit_level,
        status=status,
        status_label=status_label,
        execution_method=execution_method,
        vram_required_gb=total_required_gb if gpu_vram > 0 or backend == "metal" else 0.0,
        ram_required_gb=total_required_gb,
        recommended_runtime=recommended_runtime,
        recommended_format=recommended_format,
        estimated_speed_tps=estimated_speed_tps,
        reason=reason,
        recommendation=recommendation,
        supported_runtimes=supported_runtimes,
        details={
            "params_billions": p_billions,
            "quantization": quantization or "Q4_K_M (est.)",
            "weights_gb": round(weights_gb, 1),
            "kv_cache_gb": round(kv_cache_gb, 2),
            "system_ram_gb": total_ram,
            "system_vram_gb": gpu_vram,
            "bandwidth_gb_s": bandwidth,
            "backend": backend,
        },
    )
