"""SystemMetrics — métriques système réelles pour le Monitoring.

Sources :
    - CPU / RAM / disque : psutil (déjà dépendance du projet) ;
    - GPU / VRAM : NVML via nvidia-ml-py (dépendance du projet) — si aucun
      GPU NVIDIA, la section est déclarée ``available: false`` avec la
      raison, jamais chiffrée à la main ;
    - Docker : ``docker stats --no-stream`` (timeout court) — indisponible
      si le daemon ou la socket n'est pas accessible.

Aucune donnée fictive : chaque bloc expose ``available`` et ``reason``.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from typing import Any

logger = logging.getLogger(__name__)


class SystemMetrics:
    """Collecte des métriques système réelles (CPU, RAM, disque, GPU, Docker)."""

    def __init__(self, *, workspace_dir: str | None = None) -> None:
        self._workspace_dir = workspace_dir or os.getcwd()
        self._started_at = time.time()

    # ── API publique ───────────────────────────────────────────────────

    def collect(self, *, include_docker: bool = True) -> dict[str, Any]:
        """Rapport complet. Chaque section indique sa disponibilité."""
        return {
            "timestamp": time.time(),
            "uptime_seconds": round(time.time() - self._started_at, 1),
            "cpu": self._cpu(),
            "memory": self._memory(),
            "disk": self._disk(),
            "gpu": self._gpu(),
            "process": self._process(),
            "docker": self._docker()
            if include_docker
            else {
                "available": False,
                "reason": "non demandé",
            },
        }

    # ── Sections ───────────────────────────────────────────────────────

    @staticmethod
    def _cpu() -> dict[str, Any]:
        try:
            import psutil
        except ImportError:
            return {"available": False, "reason": "psutil non installé"}
        try:
            percent = psutil.cpu_percent(interval=0.2)
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            load1, load5, load15 = os.getloadavg()
            return {
                "available": True,
                "percent": percent,
                "cores": psutil.cpu_count(logical=True),
                "physical_cores": psutil.cpu_count(logical=False),
                "per_core": per_core,
                "load": {"1m": round(load1, 2), "5m": round(load5, 2), "15m": round(load15, 2)},
            }
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "reason": f"psutil a échoué : {exc}"}

    @staticmethod
    def _memory() -> dict[str, Any]:
        try:
            import psutil
        except ImportError:
            return {"available": False, "reason": "psutil non installé"}
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                "available": True,
                "total_bytes": vm.total,
                "used_bytes": vm.used,
                "percent": vm.percent,
                "swap_percent": swap.percent,
            }
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "reason": f"psutil a échoué : {exc}"}

    def _disk(self) -> dict[str, Any]:
        try:
            import psutil
        except ImportError:
            return {"available": False, "reason": "psutil non installé"}
        try:
            usage = psutil.disk_usage(self._workspace_dir)
            result: dict[str, Any] = {
                "available": True,
                "path": self._workspace_dir,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": usage.percent,
            }
            docker_root = "/var/lib/docker"
            if os.path.isdir(docker_root):
                du = psutil.disk_usage(docker_root)
                result["docker_root"] = {
                    "path": docker_root,
                    "total_bytes": du.total,
                    "free_bytes": du.free,
                    "percent": du.percent,
                }
            return result
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "reason": f"psutil a échoué : {exc}"}

    @staticmethod
    def _gpu() -> dict[str, Any]:
        try:
            import pynvml  # fourni par nvidia-ml-py
        except ImportError:
            return {
                "available": False,
                "reason": "nvidia-ml-py non installé (aucune métrique GPU)",
            }
        try:
            pynvml.nvmlInit()
        except Exception as exc:  # noqa: BLE001
            return {
                "available": False,
                "reason": f"Aucun GPU NVIDIA accessible : {exc}",
            }
        try:
            gpus = []
            count = pynvml.nvmlDeviceGetCount()
            for i in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except Exception:  # noqa: BLE001
                    temp = None
                gpus.append(
                    {
                        "index": i,
                        "name": name.decode() if isinstance(name, bytes) else str(name),
                        "vram_total_bytes": mem.total,
                        "vram_used_bytes": mem.used,
                        "vram_percent": round(mem.used / mem.total * 100, 1) if mem.total else None,
                        "gpu_percent": util.gpu,
                        "temperature_c": temp,
                    }
                )
            return {"available": True, "count": count, "gpus": gpus}
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "reason": f"NVML a échoué : {exc}"}
        finally:
            try:
                pynvml.nvmlShutdown()
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _process() -> dict[str, Any]:
        try:
            import psutil

            proc = psutil.Process()
            with proc.oneshot():
                cpu = proc.cpu_percent(interval=None)
                mem = proc.memory_info()
            return {
                "available": True,
                "pid": proc.pid,
                "cpu_percent": cpu,
                "rss_bytes": mem.rss,
                "threads": proc.num_threads(),
                "create_time": proc.create_time(),
            }
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "reason": f"process indisponible : {exc}"}

    def _docker(self) -> dict[str, Any]:
        if shutil.which("docker") is None:
            return {
                "available": False,
                "reason": "commande 'docker' introuvable (socket Docker non montée ?)",
            }
        try:
            proc = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except subprocess.TimeoutExpired:
            return {"available": False, "reason": "timeout de docker stats (10s)"}
        except subprocess.CalledProcessError as exc:
            return {
                "available": False,
                "reason": f"docker stats a échoué : {(exc.stderr or '').strip()[:200]}",
            }
        containers = []
        for line in proc.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                containers.append(
                    {
                        "name": parts[0],
                        "cpu_percent": parts[1].strip().removesuffix("%"),
                        "mem_usage": parts[2].strip(),
                    }
                )
        return {"available": True, "containers": containers}


__all__ = ["SystemMetrics"]
