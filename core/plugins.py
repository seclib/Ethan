"""Plugin System — ADR-1008

Système de découverte et de chargement automatique des plugins.
Permet l'extension du système sans modifier le core.
"""

from __future__ import annotations

import importlib.util
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Type, Any

logger = logging.getLogger(__name__)

@dataclass
class PluginMetadata:
    """Metadata d'un plugin."""
    name: str
    version: str
    description: str
    author: str
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class PluginContext:
    """Contexte fourni au plugin lors de l'initialisation."""
    def __init__(self, config: Dict[str, Any], event_bus: Any = None):
        self.config = config
        self.event_bus = event_bus


class Plugin(ABC):
    """Interface abstraite pour tous les plugins."""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Retourner les metadata du plugin."""
        pass

    @abstractmethod
    async def initialize(self, context: PluginContext) -> None:
        """Initialiser le plugin."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Nettoyer le plugin."""
        pass


class PluginRegistry:
    """Registre central des plugins."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}

    async def discover(self, plugin_dirs: List[Path]):
        """Découvrir les plugins dans les répertoires spécifiés."""
        for plugin_dir in plugin_dirs:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory {plugin_dir} does not exist")
                continue

            # Cherche tous les fichiers .py dans les sous-répertoires
            for plugin_file in plugin_dir.rglob("*.py"):
                try:
                    await self._load_plugin_from_file(plugin_file)
                except Exception as e:
                    logger.error(f"Failed to load plugin from {plugin_file}: {e}")

    async def _load_plugin_from_file(self, path: Path):
        """Import dynamique d'un plugin depuis un fichier."""
        module_name = path.stem if path.name != "__init__.py" else path.parent.name
        
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Cherche la première classe qui hérite de Plugin et n'est pas la classe Plugin elle-même
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                try:
                    plugin_instance = attr()
                    metadata = plugin_instance.get_metadata()
                    self._plugins[metadata.name] = plugin_instance
                    self._metadata[metadata.name] = metadata
                    logger.info(f"Discovered plugin: {metadata.name} (v{metadata.version})")
                    return
                except Exception as e:
                    logger.error(f"Failed to instantiate plugin class {attr_name} in {path}: {e}")

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Récupérer un plugin par son nom."""
        return self._plugins.get(name)

    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Récupérer les metadata d'un plugin."""
        return self._metadata.get(name)

    def list_plugins(self) -> List[str]:
        """Lister tous les plugins découverts."""
        return list(self._plugins.keys())

    def __len__(self) -> int:
        return len(self._plugins)