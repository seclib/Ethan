"""Plugin Loader — Découverte et chargement dynamique des plugins Python.

Les plugins sont découverts dans :
1. core/plugins/bundled/ (plugins intégrés)
2. ~/.ethan/plugins/python/ (plugins utilisateur)
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any

from core.plugins.interface import EthanPlugin, PluginManifest

logger = logging.getLogger(__name__)

# Chemins de découverte des plugins
BUNDLED_PLUGINS_DIR = Path(__file__).parent / "bundled"
USER_PLUGINS_DIR = Path.home() / ".ethan" / "plugins" / "python"


class PluginLoader:
    """Chargeur dynamique de plugins Python.

    Supporte :
    - Plugins dans des dossiers (avec __init__.py)
    - Plugins dans des fichiers .py simples
    - Dépendances optionnelles
    """

    def __init__(self, extra_paths: list[Path] | None = None):
        self._paths = [
            BUNDLED_PLUGINS_DIR,
            USER_PLUGINS_DIR,
        ]
        if extra_paths:
            self._paths.extend(extra_paths)

        self._loaded: dict[str, EthanPlugin] = {}
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Crée les dossiers de plugins s'ils n'existent pas."""
        for path in self._paths:
            path.mkdir(parents=True, exist_ok=True)

    def discover(self) -> list[PluginManifest]:
        """Découvre tous les plugins disponibles (sans les charger).

        Returns:
            Liste des manifests des plugins trouvés
        """
        manifests: list[PluginManifest] = []

        for plugins_dir in self._paths:
            if not plugins_dir.exists():
                continue

            # Chercher les dossiers avec __init__.py
            for entry in plugins_dir.iterdir():
                if entry.is_dir() and (entry / "__init__.py").exists():
                    manifest = self._extract_manifest(entry)
                    if manifest:
                        manifests.append(manifest)

                # Chercher les fichiers .py
                elif entry.suffix == ".py" and entry.stem != "__init__":
                    manifest = self._extract_manifest(entry)
                    if manifest:
                        manifests.append(manifest)

        return manifests

    async def load(self, name: str, **kwargs: Any) -> EthanPlugin | None:
        """Charge un plugin par son nom.

        Args:
            name: Nom du plugin (nom du dossier ou du fichier sans .py)
            **kwargs: Configuration passée au plugin

        Returns:
            Instance du plugin, ou None si introuvable
        """
        if name in self._loaded:
            return self._loaded[name]

        # Chercher dans tous les chemins
        for plugins_dir in self._paths:
            if not plugins_dir.exists():
                continue

            # Dossier
            plugin_dir = plugins_dir / name
            if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                return await self._load_from_dir(plugin_dir, name, **kwargs)

            # Fichier
            plugin_file = plugins_dir / f"{name}.py"
            if plugin_file.exists():
                return await self._load_from_file(plugin_file, name, **kwargs)

        logger.warning(f"Plugin '{name}' not found in {self._paths}")
        return None

    async def load_all(self, **kwargs: Any) -> list[EthanPlugin]:
        """Charge tous les plugins découverts.

        Returns:
            Liste des instances de plugins chargés
        """
        plugins = []
        for manifest in self.discover():
            try:
                plugin = await self.load(manifest.name, **kwargs)
                if plugin:
                    plugins.append(plugin)
            except Exception as e:
                logger.error(f"Failed to load plugin '{manifest.name}': {e}")
        return plugins

    def get_loaded(self, name: str) -> EthanPlugin | None:
        """Récupère un plugin déjà chargé."""
        return self._loaded.get(name)

    def list_loaded(self) -> list[EthanPlugin]:
        """Liste tous les plugins chargés."""
        return list(self._loaded.values())

    # ─── Méthodes internes ───────────────────────────────────────────

    def _extract_manifest(self, entry: Path) -> PluginManifest | None:
        """Extrait le manifest d'un plugin sans le charger."""
        try:
            # Ajouter le dossier parent au path
            parent = entry.parent if entry.is_dir() else entry.parent
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))

            module_name = entry.stem if entry.is_file() else entry.name
            module = importlib.import_module(module_name)

            # Chercher la variable MANIFEST
            if hasattr(module, "MANIFEST") and isinstance(module.MANIFEST, dict):
                return PluginManifest(**module.MANIFEST)

            # Chercher une sous-classe de EthanPlugin
            for _, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and issubclass(obj, EthanPlugin)
                        and obj is not EthanPlugin):
                    return obj.manifest

            return None

        except Exception as e:
            logger.debug(f"Could not extract manifest from {entry}: {e}")
            return None

        finally:
            # Nettoyer le sys.path
            parent = entry.parent if entry.is_dir() else entry.parent
            if str(parent) in sys.path:
                sys.path.remove(str(parent))

    async def _load_from_dir(
        self,
        plugin_dir: Path,
        name: str,
        **kwargs: Any,
    ) -> EthanPlugin | None:
        """Charge un plugin depuis un dossier."""
        try:
            if str(plugin_dir.parent) not in sys.path:
                sys.path.insert(0, str(plugin_dir.parent))

            module = importlib.import_module(name)
            return await self._instantiate(module, name, **kwargs)

        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
            return None

        finally:
            if str(plugin_dir.parent) in sys.path:
                sys.path.remove(str(plugin_dir.parent))

    async def _load_from_file(
        self,
        plugin_file: Path,
        name: str,
        **kwargs: Any,
    ) -> EthanPlugin | None:
        """Charge un plugin depuis un fichier .py."""
        try:
            if str(plugin_file.parent) not in sys.path:
                sys.path.insert(0, str(plugin_file.parent))

            spec = importlib.util.spec_from_file_location(name, plugin_file)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return await self._instantiate(module, name, **kwargs)

        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_file}: {e}")
            return None

        finally:
            if str(plugin_file.parent) in sys.path:
                sys.path.remove(str(plugin_file.parent))

    async def _instantiate(
        self,
        module: Any,
        name: str,
        **kwargs: Any,
    ) -> EthanPlugin | None:
        """Instancie un plugin depuis un module."""
        # Chercher une sous-classe de EthanPlugin
        for _, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and issubclass(obj, EthanPlugin)
                    and obj is not EthanPlugin):
                instance = obj()
                self._loaded[name] = instance
                logger.info(f"Loaded plugin: {name} v{instance.version}")
                return instance

        logger.warning(f"No EthanPlugin subclass found in {name}")
        return None