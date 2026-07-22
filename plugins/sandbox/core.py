"""Plugin Sandbox — isolation et limites de ressources.

Fournit deux niveaux d'isolation :
1. **In-process** : resource limits + builtins restreints (léger)
2. **Subprocess** : exécution dans un processus séparé avec restrictions (recommandé)
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ResourceLimits:
    """Limites de ressources pour un plugin."""
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    max_execution_time_s: int = 30
    max_file_descriptors: int = 100
    max_network_connections: int = 10


class PermissionSet:
    """Ensemble de permissions vérifiables."""

    def __init__(self):
        self._permissions: list[tuple[str, str]] = []

    def add(self, action: str, resource: str) -> None:
        """Ajoute une permission action:resource."""
        self._permissions.append((action, resource))

    def add_many(self, permissions: list[str]) -> None:
        """Ajoute des permissions depuis une liste 'action:resource'."""
        for perm in permissions:
            if ":" in perm:
                action, resource = perm.split(":", 1)
                self.add(action, resource)

    def allows(self, action: str, resource: str) -> bool:
        """Vérifie si l'action est autorisée sur la ressource."""
        import fnmatch
        for perm_action, perm_resource in self._permissions:
            if fnmatch.fnmatch(action, perm_action) and fnmatch.fnmatch(resource, perm_resource):
                return True
        return False

    def is_empty(self) -> bool:
        return len(self._permissions) == 0


class SecurityError(Exception):
    """Exception levée en cas de violation de sécurité."""
    pass


class PluginSandbox:
    """Sandbox d'exécution pour plugin.

    Deux modes :
    - `enforce()` : isolation in-process (builtins restreints + resource limits)
    - `run_in_subprocess()` : isolation par processus séparé (recommandé)
    """

    def __init__(self, permissions: PermissionSet | None = None):
        self.permissions = permissions or PermissionSet()
        self.resource_limits = ResourceLimits()

    def check_permission(self, action: str, resource: str) -> bool:
        """Vérifie une permission."""
        return self.permissions.allows(action, resource)

    @contextlib.asynccontextmanager
    async def enforce(self):
        """Context manager — isolation in-process.

        Protège contre :
        - `eval()`, `exec()`, `open()` (builtins désactivés)
        - Mémoire excessive (RLIMIT_AS)
        - Trop de file descriptors (RLIMIT_NOFILE)
        """
        import builtins
        import resource
        
        # Sauvegarde des builtins originaux
        original_eval = builtins.eval
        original_exec = builtins.exec
        original_open = builtins.open
        
        # Sauvegarde des limites de ressources originales
        try:
            soft_as, hard_as = resource.getrlimit(resource.RLIMIT_AS)
            soft_nofile, hard_nofile = resource.getrlimit(resource.RLIMIT_NOFILE)
            
            # Application des nouvelles limites
            mem_bytes = self.resource_limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, hard_as))
            resource.setrlimit(resource.RLIMIT_NOFILE, (self.resource_limits.max_file_descriptors, hard_nofile))
        except (ValueError, OSError):
            pass

        def _disabled(*args, **kwargs):
            raise SecurityError("Opération interdite par la Sandbox du plugin")

        # Désactivation des appels dangereux
        builtins.eval = _disabled
        builtins.exec = _disabled
        builtins.open = _disabled

        try:
            yield self
        finally:
            # Restauration des builtins
            builtins.eval = original_eval
            builtins.exec = original_exec
            builtins.open = original_open
            
            # Restauration des limites
            try:
                resource.setrlimit(resource.RLIMIT_AS, (soft_as, hard_as))
                resource.setrlimit(resource.RLIMIT_NOFILE, (soft_nofile, hard_nofile))
            except (ValueError, OSError):
                pass

    def run_in_subprocess(
        self,
        code: str,
        timeout: Optional[int] = None,
        env: Optional[dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        """Exécute du code Python dans un subprocess isolé.

        Garanties :
        - Processus séparé (pas d'accès à la mémoire du parent)
        - Timeout configurable (arrêt par SIGKILL)
        - Environnement restreint (uniquement les variables passées)
        - Pas d'accès au stdin parent
        - Stderr capturé séparément

        Args:
            code: Code Python à exécuter
            timeout: Timeout en secondes (défaut: max_execution_time_s)
            env: Variables d'environnement pour le subprocess

        Returns:
            subprocess.CompletedProcess avec stdout, stderr, returncode

        Raises:
            SecurityError: Si le timeout est dépassé
            SecurityError: Si le returncode est négatif (signal)
        """
        timeout = timeout or self.resource_limits.max_execution_time_s

        # Créer un fichier temporaire pour le code
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            prefix="ethan_plugin_",
            delete=False,
        ) as f:
            f.write(code)
            script_path = f.name

        try:
            # Environnement restreint
            restricted_env = {
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
            }
            if env:
                restricted_env.update(env)

            result = subprocess.run(
                [sys.executable, "-I", script_path],  # -I : isolated mode
                capture_output=True,
                text=True,
                timeout=timeout,
                env=restricted_env,
                stdin=subprocess.DEVNULL,
                preexec_fn=self._restrict_subprocess,
            )

            if result.returncode < 0:
                # Tué par un signal
                signal_name = signal.Signals(-result.returncode).name
                raise SecurityError(
                    f"Plugin terminé par le signal {signal_name} "
                    f"(timeout={timeout}s ou dépassement mémoire)"
                )

            return result

        except subprocess.TimeoutExpired:
            raise SecurityError(
                f"Plugin dépassé le timeout de {timeout}s — processus tué"
            )
        finally:
            # Nettoyage du fichier temporaire
            try:
                os.unlink(script_path)
            except OSError:
                pass

    @staticmethod
    def _restrict_subprocess():
        """Fonction preexec_fn pour restreindre le subprocess.

        Appliquée AVANT l'exécution du code dans le processus enfant.
        """
        import resource
        import os

        # Limite mémoire
        try:
            mem_bytes = 512 * 1024 * 1024  # 512 MB
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except (ValueError, OSError):
            pass

        # Limite file descriptors
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (100, 100))
        except (ValueError, OSError):
            pass

        # Limite nombre de processus enfants
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
        except (ValueError, OSError):
            pass

        # Ignorer SIGINT (géré par le parent)
        signal.signal(signal.SIGINT, signal.SIG_IGN)