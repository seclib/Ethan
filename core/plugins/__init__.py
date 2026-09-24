"""ETHAN Core — Plugin Registry.

Système Plugins Core-owned : catalogue de manifestes + état persistant
(domaine `webui_plugins` du CoreRecordStore).  Référence les systèmes
existants (Tools, Skills, MCP) au lieu de les dupliquer.
"""

from .catalog import BUILTIN_PLUGINS, catalogue_categories, find_manifest
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

__all__ = [
    "BUILTIN_PLUGINS",
    "PluginAuthentication",
    "PluginConfigurationField",
    "PluginManifest",
    "PluginRegistry",
    "PluginValidator",
    "ValidationResult",
    "STATUS_ACTIVE",
    "STATUS_AVAILABLE",
    "STATUS_INACTIVE",
    "catalogue_categories",
    "find_manifest",
    "get_plugin_registry",
    "resolve_conversation_tools",
    "set_plugin_registry",
]
