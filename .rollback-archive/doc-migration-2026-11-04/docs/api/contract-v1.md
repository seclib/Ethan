# Contrat API ETHAN v1 — État actuel (refonte Phase 0)

**Date :** 29/10/2026  
**Branche :** `refactor/ethan-rebuild-p0`  
**Fichier source :** `interfaces/api/routers/v1.py` (monolithe, ~85 Ko)

## Principe

L'API Gateway est une passerelle HTTP mince vers ETHAN Core. Elle ne contient **aucune logique métier** : elle délègue aux managers et stores du Core (`core/skills/`, `core/plugins/`, `core/knowledge/`, `core/llm/`).

## Routes par domaine

### Skills — `/v1/skills`

| Méthode | Route | Description | Délégation Core |
|---------|-------|-------------|-----------------|
| GET | `/skills` | Liste avec filtres (active, kind, tag) | `SkillStore.list_skills()` |
| POST | `/skills` | Créer une skill | `SkillStore.create_skill()` |
| GET | `/skills/search` | Recherche textuelle | `SkillStore.search_skills()` |
| GET | `/skills/export` | Export complet | `SkillStore.export_skills()` |
| POST | `/skills/import` | Import (portabilité) | `SkillStore.import_skills()` |
| GET | `/skills/{id}` | Détail d'une skill | `SkillStore.get_skill()` |
| PUT | `/skills/{id}` | Mise à jour | `SkillStore.update_skill()` |
| DELETE | `/skills/{id}` | Suppression | `SkillStore.delete_skill()` |
| POST | `/skills/{id}/toggle` | Activer/désactiver | `SkillStore.toggle_skill()` |
| GET | `/skills/{id}/valves` | Valves de config | `SkillStore.get_skill_valves()` |
| PUT | `/skills/{id}/valves` | Mise à jour valves | `SkillStore.update_skill_valves()` |
| POST | `/skills/{id}/run` | Exécution | `SkillStore.run_skill()` |
| POST | `/skills/lab/test` | Test sandbox Docker | `SkillLab.test()` |
| GET | `/skills/lab/results` | Résultats lab | `SkillLab.results()` |

### Plugins — `/v1/plugins`

| Méthode | Route | Description | Délégation Core |
|---------|-------|-------------|-----------------|
| GET | `/plugins` | Catalogue + état fusionné | `PluginRegistry.list_plugins()` |
| GET | `/plugins/categories` | Catégories dynamiques | `PluginRegistry.categories()` |
| GET | `/plugins/{id}` | Détail d'un plugin | `PluginRegistry.get()` |
| GET | `/plugins/{id}/permissions` | Permissions déclarées | `PluginRegistry.permissions()` |
| GET | `/plugins/{id}/capabilities` | Capacités résolues | `PluginRegistry.capabilities()` |
| POST | `/plugins/install` | Installer (catalogue ou custom) | `PluginRegistry.install()` |
| POST | `/plugins/{id}/install` | Installer par id | `PluginRegistry.install()` |
| POST | `/plugins/{id}/enable` | Activer | `PluginRegistry.enable()` |
| POST | `/plugins/{id}/disable` | Désactiver | `PluginRegistry.disable()` |
| PUT | `/plugins/{id}/toggle` | Basculer état | `PluginRegistry.toggle()` |
| PUT | `/plugins/{id}/update` | Synchroniser manifest | `PluginRegistry.update()` |
| DELETE | `/plugins/{id}` | Désinstaller | `PluginRegistry.uninstall()` |
| POST | `/plugins/{id}/connect` | Connecter (config, pas de secret) | `PluginRegistry.connect()` |
| DELETE | `/plugins/{id}/connection` | Déconnecter | `PluginRegistry.disconnect()` |

### Knowledge — `/v1/knowledge`

| Méthode | Route | Description | Délégation Core |
|---------|-------|-------------|-----------------|
| GET | `/knowledge` | Liste des nodes | `KnowledgeManager.list()` |
| GET | `/knowledge/search` | Recherche | `KnowledgeManager.search()` |
| GET | `/knowledge/collections` | Collections utilisateur | `KnowledgeCollectionManager.list_collections()` |
| POST | `/knowledge/collections` | Créer collection | `KnowledgeCollectionManager.create_collection()` |
| GET | `/knowledge/collections/tree` | Arborescence | `KnowledgeCollectionManager.list_tree()` |

### Folders

Aucune route dédiée `/folders`. Utilisé via `_validated_folder_ids()` et `get_folder_manager()` intégré aux routes agents.

### Providers — `/v1/providers` (DOUBLON à supprimer)

| Méthode | Route | Statut |
|---------|-------|--------|
| GET/POST | `/v1/providers` | ⚠️ Doublon de `/providers` (ProviderManager réel) |

**Décision :** Conserver uniquement `GET/POST/PUT/DELETE /providers` (implémentation réelle via `core/llm/provider_manager.py`). Supprimer `/v1/providers`.

## Points d'injection (dépendance Core)

| Variable globale | Setter | Rôle |
|------------------|--------|------|
| `_skill_store` | `set_skill_store()` | `core.skills.store.SkillStore` |
| `_knowledge_collections` | `set_knowledge_collections()` | `core.knowledge.collections.KnowledgeCollectionManager` |
| `_plugin_registry` | `set_plugin_registry()` | `core.plugins.registry.PluginRegistry` |
| `_skill_lab` | `get_skill_lab()` (paresseux) | `core.skills.lab.SkillLab` |
| `_domains.knowledge` | Injecté via `WebUICoreStore` | `core.knowledge.manager.KnowledgeManager` |
| `_tool_manager` | Injecté via `WebUICoreStore` | `core.tools.manager.ToolManager` |

## Fichiers liés à ne pas modifier pendant la Phase 0

- `core/skills/store.py` — source de vérité, inchangé
- `core/plugins/registry.py` — source de vérité, inchangé
- `core/knowledge/manager.py` — source de vérité, inchangé
- `interfaces/api/routers/providers.py` — route `/providers` réelle, inchangé

## Fichiers à créer pendant la Phase 1

- `interfaces/api/routers/skills.py` — extraction des routes skills
- `interfaces/api/routers/plugins.py` — extraction des routes plugins
- `interfaces/api/routers/knowledge.py` — extraction des routes knowledge
- Complétion de `interfaces/api/routers/skills_import.py` (actuellement 6 octets)