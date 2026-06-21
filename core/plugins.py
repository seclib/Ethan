# Jarvis OS — Plugin Loader
# Système de chargement et gestion des plugins

import importlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PluginManifest:
    """Manifeste d'un plugin."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "Apache-2.0"
    capabilities: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    entrypoint: str = "main.py"
    path: Path | None = None


@dataclass
class Plugin:
    """Plugin chargé."""
    manifest: PluginManifest
    module: Any = None
    instance: Any = None
    enabled: bool = True
    path: Path | None = None


class PluginManager:
    """Gestionnaire de plugins.

    Découvre, charge et gère les plugins depuis le répertoire plugins/.
    Chaque plugin doit avoir :
    - plugin.yaml : Manifeste
    - main.py     : Point d'entrée
    """

    def __init__(self, plugins_dir: str | Path = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._plugins: dict[str, Plugin] = {}
        self._capabilities: dict[str, str] = {}  # capability -> plugin name

    def discover(self) -> list[PluginManifest]:
        """Discover all plugins in the plugins directory."""
        manifests = []
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return manifests

        for entry in sorted(self.plugins_dir.iterdir()):
            if not entry.is_dir():
                continue
            manifest_path = entry / "plugin.yaml"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path) as f:
                    data = yaml.safe_load(f)
                manifest = PluginManifest(**data, path=entry)
                manifests.append(manifest)
                logger.info(f"Discovered plugin: {manifest.name} v{manifest.version}")
            except Exception as e:
                logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")

        return manifests

    def load(self, name: str) -> Plugin | None:
        """Load a specific plugin by name."""
        manifest_path = self.plugins_dir / name / "plugin.yaml"
        if not manifest_path.exists():
            logger.error(f"Plugin '{name}' not found")
            return None

        try:
            with open(manifest_path) as f:
                data = yaml.safe_load(f)
            manifest = PluginManifest(**data)

            # Import the plugin module
            module_name = f"plugins.{name}.main"
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                module = None

            plugin = Plugin(
                manifest=manifest,
                module=module,
                path=self.plugins_dir / name,
            )

            # Register capabilities
            for cap in manifest.capabilities:
                self._capabilities[cap] = name

            self._plugins[name] = plugin
            logger.info(f"Loaded plugin: {manifest.name} v{manifest.version}")
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin '{name}': {e}")
            return None

    def load_all(self) -> list[Plugin]:
        """Discover and load all plugins."""
        plugins = []
        for manifest in self.discover():
            plugin = self.load(manifest.name)
            if plugin:
                plugins.append(plugin)
        return plugins

    def get(self, name: str) -> Plugin | None:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def get_by_capability(self, capability: str) -> Plugin | None:
        """Get the plugin that provides a specific capability."""
        plugin_name = self._capabilities.get(capability)
        if plugin_name:
            return self.get(plugin_name)
        return None

    def list_plugins(self) -> list[str]:
        """List all loaded plugins."""
        return list(self._plugins.keys())

    def list_capabilities(self) -> list[str]:
        """List all available capabilities."""
        return list(self._capabilities.keys())

    def enable(self, name: str) -> bool:
        """Enable a plugin."""
        if name in self._plugins:
            self._plugins[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a plugin."""
        if name in self._plugins:
            self._plugins[name].enabled = False
            return True
        return False

    def is_loaded(self, name: str) -> bool:
        """Check if a plugin is loaded."""
        return name in self._plugins

    def unload(self, name: str) -> bool:
        """Unload a plugin."""
        if name in self._plugins:
            plugin = self._plugins.pop(name)
            for cap in plugin.manifest.capabilities:
                self._capabilities.pop(cap, None)
            return True
        return False


# Global plugin manager instance
manager = PluginManager()