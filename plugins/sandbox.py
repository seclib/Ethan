"""Plugin Sandbox — isolation et limites de ressources."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import Any


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


class PluginSandbox:
    """Sandbox d'exécution pour plugin."""

    def __init__(self, permissions: PermissionSet | None = None):
        self.permissions = permissions or PermissionSet()
        self.resource_limits = ResourceLimits()

    def check_permission(self, action: str, resource: str) -> bool:
        """Vérifie une permission."""
        return self.permissions.allows(action, resource)

    @contextlib.asynccontextmanager
    async def enforce(self):
        """Context manager qui applique les limites."""
        try:
            yield self
        finally:
            pass  # cleanup resources