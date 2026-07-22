"""Plugin Sandbox — isolation et limites de ressources.

Fournit deux niveaux d'isolation :
1. **In-process** : resource limits + builtins restreints (léger)
2. **Subprocess** : exécution dans un processus séparé avec restrictions (recommandé)
"""

from __future__ import annotations

from plugins.sandbox.core import (
    PermissionSet,
    PluginSandbox,
    ResourceLimits,
    SecurityError,
)
from plugins.sandbox.runtime import PluginRuntime

__version__ = "1.0.0"
__all__ = [
    "PluginSandbox",
    "ResourceLimits",
    "PermissionSet",
    "SecurityError",
    "PluginRuntime",
]
