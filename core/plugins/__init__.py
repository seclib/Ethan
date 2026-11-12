"""ETHAN Core — Plugin Registry.

Système Plugins Core-owned : catalogue de manifestes + état persistant
(domaine `webui_plugins` du CoreRecordStore).  Référence les systèmes
existants (Tools, Skills, MCP) au lieu de les dupliquer.
"""

from typing import Any

from .catalog import BUILTIN_PLUGINS, catalogue_categories, find_manifest
from .odin import (
    STATE_ACTIVE,
    STATE_DEGRADED,
    STATE_ERROR,
    STATE_NOT_INSTALLED,
    STATE_STARTING,
    STATE_STOPPED,
    STATE_STOPPING,
    STATE_UNKNOWN,
    OdinService,
    get_odin_service,
    set_odin_service,
)
from .registry import (
    PluginRegistry,
    get_plugin_registry,
    resolve_conversation_tools,
    set_plugin_registry,
)
from .types import (
    STATUS_ACTIVE,
    STATUS_AVAILABLE,
    STATUS_INACTIVE,
    PluginAuthentication,
    PluginConfigurationField,
    PluginManifest,
)
from .validator import PluginValidator, ValidationResult

# ── ADR-1008 — Plugin SDK (API du test `tests/core/test_plugins.py`). ─────────
#
# Types API du système Plugins (get_metadata, initialize, shutdown et les
# métadonnées d'un plugin). Ils correspondent à la spécification ADR-1008,
# indépendamment de l'implémentation partielle `plugins.sdk.base:PluginBase`.


class PluginContext:
    """Contexte d'initialisation d'un plugin."""

    def __init__(self, **values: Any) -> None:
        for key, value in values.items():
            setattr(self, key, value)


class Plugin:
    """Interface abstraite d'un plugin ETHAN."""

    async def initialize(self, context: PluginContext) -> None:
        """Initialisation du plugin avec le contexte d'exécution."""
        ...

    async def shutdown(self) -> None:
        """Arrêt du plugin."""
        ...


class PluginMetadata:
    """Métadonnées d'un plugin.

    Signature utilisée par les tests de découverte de plugins :
        PluginMetadata(name, version, description, author, capabilities)
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str = "ETHAN",
        capabilities: list[str] | None = None,
        **values: Any,
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.capabilities = capabilities or []
        for key, value in values.items():
            setattr(self, key, value)


__all__ = [
    "BUILTIN_PLUGINS",
    "OdinService",
    "PluginAuthentication",
    "PluginConfigurationField",
    "PluginManifest",
    "PluginRegistry",
    "PluginValidator",
    "STATE_ACTIVE",
    "STATE_DEGRADED",
    "STATE_ERROR",
    "STATE_NOT_INSTALLED",
    "STATE_STARTING",
    "STATE_STOPPED",
    "STATE_STOPPING",
    "STATE_UNKNOWN",
    "STATUS_ACTIVE",
    "STATUS_AVAILABLE",
    "STATUS_INACTIVE",
    "ValidationResult",
    "catalogue_categories",
    "find_manifest",
    "get_odin_service",
    "get_plugin_registry",
    "resolve_conversation_tools",
    "set_odin_service",
    "set_plugin_registry",
]
