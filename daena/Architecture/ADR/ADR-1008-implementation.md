# ADR-1008 — Plugin Discovery & Loading — Implementation Report

## Date
2026-06-23

## Statut
✅ **Implémenté**

---

## Résumé

Le système permet désormais la découverte automatique et le chargement dynamique des plugins, permettant l'extension du système sans modification du code source du core.

**Fonctionnalités:**
- **Auto-discovery** — Scan automatique des répertoires de plugins.
- **Dynamic Loading** — Importation et instanciation dynamique via `importlib`.
- **Plugin Registry** — Gestion centralisée des plugins et de leurs metadata.
- **Interface Standard** — Contrat strict via la classe `Plugin` (ABC).

---

## Modifications

### 1. Core Model (`core/plugins.py`)

**Ajouté:**
- `PluginMetadata` — Dataclass pour les informations du plugin (nom, version, capacités, etc.).
- `PluginContext` — Contexte d'initialisation.
- `Plugin` (ABC) — Interface abstraite (`get_metadata`, `initialize`, `shutdown`).
- `PluginRegistry` — Système de scan (`discover`) et de gestion des instances.

### 2. Tests (`tests/core/test_plugins.py`)

**Ajouté:**
- 7 tests unitaires validant :
  - L'initialisation du registre.
  - La découverte de fichiers `.py` isolés.
  - La découverte de plugins dans des packages (`__init__.py`).
  - La gestion de multiples plugins.
  - L'ignorance des fichiers Python invalides.
  - La récupération sécurisée des plugins.

**Résultat:** ✅ 7/7 tests passent

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PluginRegistry                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  discover([dir])   → scan .py files                         │
│  _load_plugin()    → importlib.util.spec_from_file_location │
│  instantiate()     → Plugin subclass instance               │
│  register()       → _plugins[name] = instance               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ charge
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Plugin (ABC)                           │
│  (get_metadata, initialize, shutdown)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Exemples d'usage

### Création d'un plugin
Pour ajouter un plugin, créez un fichier `plugin.py` dans un dossier du répertoire `plugins/` :

```python
from core.plugins import Plugin, PluginMetadata

class MyCustomPlugin(Plugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            description="Mon super plugin",
            author="Ethan",
            capabilities=["custom.cap"]
        )

    async def initialize(self, context):
        print("Plugin initialisé !")

    async def shutdown(self):
        print("Plugin fermé !")
```

### Chargement et utilisation
```python
from core.plugins import PluginRegistry
from pathlib import Path

registry = PluginRegistry()
await registry.discover([Path("plugins")])

plugin = registry.get_plugin("my-plugin")
if plugin:
    await plugin.initialize(context)
```

---

## Conformité ADR-1008

| Règle ADR | Status | Preuve |
|-----------|--------|--------|
| Auto-discovery | ✅ | `PluginRegistry.discover()` |
| Dynamic Loading | ✅ | `importlib.util` |
| Plugin Schema | ✅ | Classe `Plugin` (ABC) |
| Metadata | ✅ | `PluginMetadata` |
| Isolation | ✅ | Chargement via specs dynamiques |
| Testabilité | ✅ | 7 tests unitaires |

---

## Impact

- ✅ **Extensibility** — Ajout de nouvelles fonctionnalités sans modifier le core.
- ✅ **Zero-config** — Découverte automatique des fichiers `.py`.
- ✅ **Maintainability** — Contrat d'interface strict.
- ✅ **Backward compatible** — N'impacte pas les autres modules.

---

## Références

- [ADR-1008](/engineering/adr/ADR-1008-plugin-discovery-loading.md)
- [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 5 (Plugin Architecture)
- [ADR-1005](/engineering/adr/ADR-1005-core-technology-independence.md)