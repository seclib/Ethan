# ADR-1008 — Plugin Discovery & Loading

> **Statut** : Proposed
> **Date** : 2026-06-23

---

## Context

Les plugins sont actuellement chargés manuellement. Pour un système extensible, nous avons besoin de:

- **Auto-discovery** — Découverte automatique des plugins
- **Hot-loading** — Chargement dynamique sans redémarrage
- **Versioning** — Gestion des versions de plugins
- **Isolation** — Plugins isolés les uns des autres

Sans discovery, chaque plugin doit être:
- explicitement importé
- manuellement enregistré
- hardcodé dans la configuration

---

## Decision

Les plugins doivent être découverts et chargés automatiquement via un **Plugin Discovery System**:

> **Plugin Registry + Auto-loader**

---

## Plugin Schema

```python
class Plugin(ABC):
    """Interface abstraite pour tous les plugins."""
    
    @abstractmethod
    def get_name(self) -> str
    @abstractmethod
    def get_version(self) -> str
    @abstractmethod
    def get_capabilities(self) -> List[str]

class PluginRegistry:
    """Registre des plugins disponibles."""
    
    async def discover(self, plugin_dirs: List[Path])
    async def load(self, plugin_name: str)
    async def unload(self, plugin_name: str)
    def get_plugin(self, name: str) -> Plugin
    def list_plugins(self) -> List[str]

class PluginLoader:
    """Chargeur dynamique de plugins."""
    
    async def load_from_path(self, path: Path) -> Plugin
    async def load_from_entry_point(self, entry_point: str) -> Plugin
```

---

## Implementation

### Plugin Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class PluginMetadata:
    """Metadata d'un plugin."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    capabilities: List[str]

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
```

### Plugin Registry

```python
class PluginRegistry:
    """Registre central des plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
    
    async def discover(self, plugin_dirs: List[Path]):
        """Découvrir les plugins dans les répertoires."""
        for plugin_dir in plugin_dirs:
            # Chercher les fichiers plugin.py ou __init__.py
            for plugin_file in plugin_dir.rglob("plugin.py"):
                await self._load_plugin_from_file(plugin_file)
    
    async def _load_plugin_from_file(self, path: Path):
        """Charger un plugin depuis un fichier."""
        # Import dynamique
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Chercher la classe Plugin
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                plugin = attr()
                metadata = plugin.get_metadata()
                self._plugins[metadata.name] = plugin
                self._metadata[metadata.name] = metadata
                break
    
    def get_plugin(self, name: str) -> Plugin:
        """Récupérer un plugin par nom."""
        if name not in self._plugins:
            raise ValueError(f"Plugin '{name}' not found")
        return self._plugins[name]
    
    def list_plugins(self) -> List[str]:
        """Lister tous les plugins disponibles."""
        return list(self._plugins.keys())
```

### Plugin Loader

```python
class PluginLoader:
    """Chargeur de plugins avec isolation."""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._loaded_plugins: Dict[str, ModuleType] = {}
    
    async def load(self, plugin_name: str) -> Plugin:
        """Charger un plugin par nom."""
        plugin = self.registry.get_plugin(plugin_name)
        await plugin.initialize(PluginContext())
        return plugin
    
    async def unload(self, plugin_name: str) -> None:
        """Décharger un plugin."""
        if plugin_name in self._loaded_plugins:
            plugin = self.registry.get_plugin(plugin_name)
            await plugin.shutdown()
            del self._loaded_plugins[plugin_name]
```

---

## Consequences

* **Extensibility** — Nouveaux plugins sans modifier le core
* **Zero-config** — Découverte automatique
* **Hot-loading** — Chargement dynamique
* **Isolation** — Plugins indépendants
* **Versioning** — Gestion des versions

---

## Compliance

* Tous les plugins doivent implémenter l'interface Plugin
* Les plugins sont dans plugins/
* Le PluginRegistry est dans core/ (abstraction)
* Les implémentations de chargement sont dans plugins/

## References

* [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 5 (Plugin Architecture)
* [ADR-1005](/engineering/adr/ADR-1005-core-technology-independence.md) — Core Technology Independence
* [ADR-1006](/engineering/adr/ADR-1006-capability-composition-pattern.md) — Capability Composition