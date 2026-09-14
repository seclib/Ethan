"""Diagnostic système hôte — CPU, RAM, disque, GPU/VRAM (psutil + NVML).

Fait partie de la capacité ETHAN « diagnostic système » (Core-owned) :
consommée par `ethan doctor`, `ethan status` et l'API `/health/diagnostics`
(elle-même rendue par la WebUI). Une seule implémentation, jamais doublée.
"""

from __future__ import annotations

import os
import shutil
from typing import Any

from .system import CheckResult, Status

try:  # psutil est une dépendance runtime déclarée (pyproject, extra server).
    import psutil
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]

try:  # nvidia-ml-py est déclarée mais un hôte sans GPU ne l'utilise pas.
    import pynvml
except ImportError:  # pragma: no cover
    pynvml = None  # type: ignore[assignment]

_MIN_DISK_GB = 10.0
_WARN_DISK_PCT = 90.0
_WARN_MEM_PCT = 90.0


def _gb(num_bytes: float) -> str:
    return f"{num_bytes / (1024 ** 3):.1f} Go"


def check_host_resources() -> list[CheckResult]:
    """Checks synchrones sur les ressources de la machine hôte."""
    checks: list[CheckResult] = []
    checks.extend(_check_cpu())
    checks.extend(_check_memory())
    checks.extend(_check_disk())
    checks.extend(_check_gpu())
    return checks


def _check_cpu() -> list[CheckResult]:
    if psutil is None:
        return [
            CheckResult(
                "cpu", Status.UNAVAILABLE,
                "psutil non installé — métriques CPU indisponibles",
            )
        ]
    try:
        cores = psutil.cpu_count(logical=True) or 0
        freq = psutil.cpu_freq()
        load1, load5, load15 = os.getloadavg()
        metadata = {
            "cores": cores,
            "load_avg": [round(load1, 2), round(load5, 2), round(load15, 2)],
        }
        if freq is not None:
            metadata["freq_mhz"] = round(freq.current or 0)
        return [
            CheckResult(
                "cpu", Status.OK, f"{cores} cœurs logiques",
                metadata=metadata,
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [CheckResult("cpu", Status.ERROR, f"Métriques CPU échouées : {exc}")]


def _check_memory() -> list[CheckResult]:
    if psutil is None:
        return [
            CheckResult(
                "memory", Status.UNAVAILABLE,
                "psutil non installé — métriques RAM indisponibles",
            )
        ]
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        pct = mem.percent
        metadata = {
            "total_gb": round(mem.total / (1024 ** 3), 1),
            "used_gb": round((mem.total - mem.available) / (1024 ** 3), 1),
            "percent": round(pct, 1),
            "swap_percent": round(swap.percent, 1),
        }
        if pct >= _WARN_MEM_PCT:
            return [
                CheckResult(
                    "memory", Status.WARNING,
                    f"RAM à {pct:.0f}% ({_gb(mem.available)} disponibles)",
                    metadata=metadata,
                )
            ]
        return [
            CheckResult(
                "memory", Status.OK,
                f"{_gb(mem.used)} / {_gb(mem.total)} utilisés ({pct:.0f}%)",
                metadata=metadata,
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [CheckResult("memory", Status.ERROR, f"Métriques RAM échouées : {exc}")]



def _check_disk() -> list[CheckResult]:
    """Espace disque sur le workspace ETHAN et /var/lib/docker si présent."""
    checks: list[CheckResult] = []
    targets: list[tuple[str, str]] = [
        ("disk", os.environ.get("ETHAN_WORKSPACE_DIR", os.getcwd())),
    ]
    if os.path.isdir("/var/lib/docker"):
        targets.append(("docker_disk", "/var/lib/docker"))

    for name, path in targets:
        try:
            usage = shutil.disk_usage(path)
            free_gb = usage.free / (1024 ** 3)
            pct = usage.used / usage.total * 100 if usage.total else 0
            metadata = {
                "path": path,
                "total_gb": round(usage.total / (1024 ** 3), 1),
                "used_percent": round(pct, 1),
                "free_gb": round(free_gb, 1),
            }
            if free_gb < _MIN_DISK_GB:
                checks.append(CheckResult(
                    name, Status.ERROR,
                    f"Espace critique : {free_gb:.1f} Go libres sur {path} "
                    f"(minimum {_MIN_DISK_GB:.0f} Go)",
                    metadata=metadata,
                ))
            elif pct >= _WARN_DISK_PCT:
                checks.append(CheckResult(
                    name, Status.WARNING,
                    f"Disque à {pct:.0f}% ({free_gb:.1f} Go libres)",
                    metadata=metadata,
                ))
            else:
                checks.append(CheckResult(
                    name, Status.OK,
                    f"{free_gb:.1f} Go libres sur {path} ({pct:.0f}% utilisés)",
                    metadata=metadata,
                ))
        except Exception as exc:  # noqa: BLE001
            checks.append(CheckResult(
                name, Status.ERROR, f"Métriques disque échouées : {exc}",
                detail=path,
            ))
    return checks


def _check_gpu() -> list[CheckResult]:
    """GPU/VRAM via NVML. UNAVAILABLE explicite si pas de GPU NVIDIA —
    jamais de valeur inventée."""
    if pynvml is None:
        return [
            CheckResult(
                "gpu", Status.UNAVAILABLE,
                "nvidia-ml-py non installé — métriques GPU indisponibles "
                "(normal sans GPU NVIDIA)",
            )
        ]
    try:
        pynvml.nvmlInit()
        try:
            count = pynvml.nvmlDeviceGetCount()
            if count == 0:
                return [
                    CheckResult(
                        "gpu", Status.UNAVAILABLE,
                        "Aucun GPU NVIDIA détecté sur cette machine",
                    )
                ]
            gpus = []
            worst = Status.OK
            for i in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                name = name.decode() if isinstance(name, bytes) else str(name)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )
                used_pct = mem.used / mem.total * 100 if mem.total else 0
                if used_pct >= 95 or temp >= 85:
                    worst = Status.WARNING
                gpus.append({
                    "index": i,
                    "name": name,
                    "vram_total_gb": round(mem.total / (1024 ** 3), 1),
                    "vram_used_gb": round(mem.used / (1024 ** 3), 1),
                    "vram_percent": round(used_pct, 1),
                    "util_percent": round(util.gpu, 1),
                    "temp_c": temp,
                })
            return [
                CheckResult(
                    "gpu", worst,
                    f"{count} GPU NVIDIA : "
                    + "; ".join(
                        f"{g['name']} (VRAM {g['vram_used_gb']}/"
                        f"{g['vram_total_gb']} Go, {g['util_percent']}%)"
                        for g in gpus
                    ),
                    metadata={"gpus": gpus},
                )
            ]
        finally:
            pynvml.nvmlShutdown()
    except pynvml.NVMLError as exc:
        return [
            CheckResult(
                "gpu", Status.UNAVAILABLE,
                f"NVML indisponible (pas de driver NVIDIA ?) : {exc}",
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [CheckResult("gpu", Status.ERROR, f"Sonde GPU échouée : {exc}")]


__all__ = ["check_host_resources"]
