"""Health Check — Vérification de la santé du système.

Vérifie l'état de santé des modules et du système.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Statut de santé d'un composant."""
    name: str
    healthy: bool
    message: str = ""
    last_check: float = 0.0
    metadata: dict[str, Any] | None = None


class HealthChecker:
    """Vérifie la santé du système."""

    def __init__(self):
        self._checks: dict[str, HealthStatus] = {}
        self._last_check_time = 0.0

    def register(self, name: str, check_fn) -> None:
        """Enregistre un check de santé.

        Args:
            name: Nom du composant
            check_fn: Fonction async qui retourne (healthy: bool, message: str)
        """
        self._checks[name] = HealthStatus(name=name, healthy=False)
        self._check_fns = getattr(self, '_check_fns', {})
        self._check_fns[name] = check_fn

    async def check_all(self) -> dict[str, HealthStatus]:
        """Exécute tous les checks.

        Returns:
            Dict {name: HealthStatus}
        """
        results = {}
        for name, check_fn in self._check_fns.items():
            try:
                healthy, message = await check_fn()
                results[name] = HealthStatus(
                    name=name,
                    healthy=healthy,
                    message=message,
                    last_check=time.time(),
                )
            except Exception as e:
                results[name] = HealthStatus(
                    name=name,
                    healthy=False,
                    message=f"Check failed: {e}",
                    last_check=time.time(),
                )

        self._last_check_time = time.time()
        return results

    async def check_system(self) -> HealthStatus:
        """Check système global.

        Returns:
            HealthStatus global
        """
        # Vérifier les ressources système
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            healthy = True
            issues = []

            if cpu_percent > 90:
                healthy = False
                issues.append(f"High CPU: {cpu_percent}%")

            if memory.percent > 90:
                healthy = False
                issues.append(f"High memory: {memory.percent}%")

            if disk.percent > 90:
                healthy = False
                issues.append(f"Low disk space: {disk.percent}%")

            message = "; ".join(issues) if issues else "System healthy"

            return HealthStatus(
                name="system",
                healthy=healthy,
                message=message,
                last_check=time.time(),
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                },
            )

        except ImportError:
            return HealthStatus(
                name="system",
                healthy=True,
                message="psutil not installed, skipping system check",
                last_check=time.time(),
            )
        except Exception as e:
            return HealthStatus(
                name="system",
                healthy=False,
                message=f"System check failed: {e}",
                last_check=time.time(),
            )

    def get_summary(self) -> dict[str, Any]:
        """Résumé de santé."""
        if not self._checks:
            return {"status": "no_checks_registered"}

        total = len(self._checks)
        healthy = sum(1 for c in self._checks.values() if c.healthy)

        return {
            "status": "healthy" if healthy == total else "degraded",
            "total_checks": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "last_check": self._last_check_time,
        }