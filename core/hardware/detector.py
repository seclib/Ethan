"""Sonde de détection hardware centralisée ETHAN.

S'appuie sur `core.diagnostics.host` (psutil + pynvml), le sysfs Linux et sysctl
pour fournir une vue structurée et mise en cache des ressources système
(CPU, RAM, GPU, VRAM, mémoire unifiée, bande passante mémoire).
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys
import time
from typing import Any

from core.diagnostics.host import check_host_resources

# Cache matériel (TTL 24h par défaut pour éviter d'invoquer NVML/sysfs en boucle)
_CACHE_TTL_SECONDS = 86400.0
_hardware_cache: dict[str, Any] | None = None
_cache_timestamp: float = 0.0

# Base de données des bandes passantes mémoire pour les GPU courants (en Go/s)
# Utilisé pour modéliser le débit physique en tokens/seconde (memory-bus bound).
GPU_BANDWIDTH_GB_S: dict[str, float] = {
    # NVIDIA GeForce RTX 40 & 50 series
    "5090": 1792.0,
    "5080": 960.0,
    "4090": 1008.0,
    "4080": 717.0,
    "4070 ti": 672.0,
    "4070": 504.0,
    "4060 ti": 288.0,
    "4060": 272.0,
    # NVIDIA GeForce RTX 30 & 20 series
    "3090": 936.0,
    "3080 ti": 912.0,
    "3080": 760.0,
    "3070": 448.0,
    "3060": 360.0,
    "2080 ti": 616.0,
    # NVIDIA Datacenter
    "h200": 4800.0,
    "h100": 3350.0,
    "a100": 2039.0,
    "a6000": 768.0,
    "l40": 864.0,
    "l4": 300.0,
    "t4": 320.0,
    "v100": 900.0,
    # AMD Radeon & Instinct
    "mi300": 5300.0,
    "mi250": 3277.0,
    "7900 xtx": 960.0,
    "7900 xt": 800.0,
    "7800 xt": 624.0,
    # Apple Silicon (Unified Memory)
    "m3 max": 400.0,
    "m4 max": 546.0,
    "m1 ultra": 800.0,
    "m2 ultra": 800.0,
    "m3 ultra": 800.0,
    "m1 max": 400.0,
    "m2 max": 400.0,
    "m1 pro": 200.0,
    "m2 pro": 200.0,
    "m3 pro": 150.0,
    "m4 pro": 273.0,
    "m1": 68.0,
    "m2": 100.0,
    "m3": 100.0,
    "m4": 120.0,
}


def _lookup_bandwidth(gpu_name: str | None, backend: str) -> float:
    """Retourne la bande passante estimée en Go/s pour un GPU donné."""
    if not gpu_name:
        # Bande passante CPU dual-channel standard DDR4/DDR5
        return 55.0

    name_lower = gpu_name.lower()
    for key, bw in GPU_BANDWIDTH_GB_S.items():
        if key in name_lower:
            return bw

    # Valeurs par défaut si le modèle précis n'est pas répertorié
    if backend == "cuda":
        return 500.0
    if backend == "rocm":
        return 450.0
    if backend == "metal":
        return 200.0
    return 55.0


def _detect_apple_silicon() -> dict[str, Any] | None:
    """Détecte la mémoire unifiée et la puce Apple Silicon sur macOS Darwin."""
    if sys.platform != "darwin":
        return None

    try:
        brand = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
        mem_bytes = int(
            subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
        )
        total_ram_gb = round(mem_bytes / (1024**3), 1)

        # Budget Metal : 67% si <=16GB, 75% si <=64GB, 80% si >64GB
        if total_ram_gb <= 16.0:
            budget_ratio = 0.67
        elif total_ram_gb <= 64.0:
            budget_ratio = 0.75
        else:
            budget_ratio = 0.80

        usable_metal_vram = round(total_ram_gb * budget_ratio, 1)

        return {
            "is_apple_silicon": True,
            "chip_name": brand,
            "total_ram_gb": total_ram_gb,
            "usable_metal_vram_gb": usable_metal_vram,
            "backend": "metal",
        }
    except Exception:
        return None


def _detect_amd_sysfs() -> dict[str, Any] | None:
    """Détecte les GPU AMD Radeon / Instinct via Linux sysfs (/sys/class/drm)."""
    if sys.platform != "linux":
        return None

    cards = glob.glob("/sys/class/drm/card[0-9]*/device")
    for card in cards:
        try:
            vendor_path = os.path.join(card, "vendor")
            if not os.path.exists(vendor_path):
                continue
            with open(vendor_path, encoding="utf-8") as f:
                vendor = f.read().strip()

            # 0x1002 = AMD PCI Vendor ID
            if vendor.lower() == "0x1002":
                vram_path = os.path.join(card, "mem_info_vram_total")
                vram_gb = 0.0
                if os.path.exists(vram_path):
                    with open(vram_path, encoding="utf-8") as vf:
                        vram_bytes = int(vf.read().strip())
                        vram_gb = round(vram_bytes / (1024**3), 1)

                return {
                    "gpu_name": "AMD Radeon / Instinct GPU",
                    "vram_gb": vram_gb,
                    "backend": "rocm",
                }
        except Exception:
            continue
    return None


def get_system_hardware(fresh: bool = False) -> dict[str, Any]:
    """Retourne la carte des ressources matérielles du système hôte.

    Args:
        fresh: Force une re-sonde en ignorant le cache en mémoire (TTL 24h).

    Returns:
        Dict structuré :
        {
            "total_ram_gb": float,
            "available_ram_gb": float,
            "cpu_cores": int,
            "gpu_count": int,
            "gpu_name": str | None,
            "gpu_vram_gb": float,
            "gpu_vram_free_gb": float,
            "backend": "cuda" | "metal" | "rocm" | "cpu",
            "platform": "linux" | "darwin" | "windows",
            "unified_memory": bool,
            "memory_bandwidth_gb_s": float
        }
    """
    global _hardware_cache, _cache_timestamp

    now = time.time()
    if not fresh and _hardware_cache is not None and (now - _cache_timestamp < _CACHE_TTL_SECONDS):
        return dict(_hardware_cache)

    checks = check_host_resources()
    result: dict[str, Any] = {
        "total_ram_gb": 8.0,
        "available_ram_gb": 4.0,
        "cpu_cores": 4,
        "gpu_count": 0,
        "gpu_name": None,
        "gpu_vram_gb": 0.0,
        "gpu_vram_free_gb": 0.0,
        "backend": "cpu",
        "platform": sys.platform,
        "unified_memory": False,
        "memory_bandwidth_gb_s": 55.0,
    }

    # 1. Sonder CPU et mémoire générale via host diagnostics
    for check in checks:
        if check.component == "cpu" and check.metadata:
            result["cpu_cores"] = check.metadata.get("cores", 4)
        elif check.component == "memory" and check.metadata:
            result["total_ram_gb"] = check.metadata.get("total_gb", 8.0)
            used_gb = check.metadata.get("used_gb", 4.0)
            result["available_ram_gb"] = max(0.5, round(result["total_ram_gb"] - used_gb, 1))

    # 2. Vérifier NVIDIA GPU via NVML
    for check in checks:
        if check.component == "gpu" and check.metadata:
            gpus = check.metadata.get("gpus", [])
            if gpus:
                result["gpu_count"] = len(gpus)
                first_gpu = gpus[0]
                result["gpu_name"] = first_gpu.get("name", "NVIDIA GPU")
                result["gpu_vram_gb"] = sum(g.get("vram_total_gb", 0.0) for g in gpus)
                vram_used = sum(g.get("vram_used_gb", 0.0) for g in gpus)
                result["gpu_vram_free_gb"] = max(0.0, round(result["gpu_vram_gb"] - vram_used, 1))
                result["backend"] = "cuda"

    # 3. Sonder Apple Silicon si macOS Darwin
    if sys.platform == "darwin":
        apple = _detect_apple_silicon()
        if apple:
            result["gpu_name"] = apple["chip_name"]
            result["gpu_count"] = 1
            result["backend"] = "metal"
            result["unified_memory"] = True
            result["gpu_vram_gb"] = apple["usable_metal_vram_gb"]
            result["gpu_vram_free_gb"] = apple["usable_metal_vram_gb"]

    # 4. Sonder AMD ROCm sous Linux si aucun GPU NVIDIA détecté
    if result["gpu_count"] == 0 and sys.platform == "linux":
        amd = _detect_amd_sysfs()
        if amd:
            result["gpu_count"] = 1
            result["gpu_name"] = amd["gpu_name"]
            result["gpu_vram_gb"] = amd["vram_gb"]
            result["gpu_vram_free_gb"] = amd["vram_gb"]
            result["backend"] = "rocm"

    # 5. Résoudre la bande passante mémoire estimée
    result["memory_bandwidth_gb_s"] = _lookup_bandwidth(result["gpu_name"], result["backend"])

    # Sauvegarder dans le cache
    _hardware_cache = dict(result)
    _cache_timestamp = now
    return result
