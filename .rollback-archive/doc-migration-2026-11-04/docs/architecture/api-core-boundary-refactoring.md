# ETHAN — Refactoring Frontière API/Core

**Date** : 2026-03-08  
**Auteur** : API Boundary Refactoring Agent  
**Statut** : Proposition — aucune modification de code effectuée  
**Portée** : `interfaces/api/routers/v1.py`, `core/`

---

## 1. Résumé Exécutif

`interfaces/api/routers/v1.py` (625 lignes) contient actuellement **toute la logique métier** avec un stockage in-memory (`MemoryStore` class) :

- Agents
- Goals
- Missions
- Skills
- Knowledge
- Memory / Facts
- Settings
- Providers
- Plugins
- Chat
- Flux / Events

**Problème** : Les données sont perdues au redémarrage du conteneur API. La logique métier est dans l'interface, pas dans le Core.

**Objectif** : Transformer l'API en **passerelle pure** qui délègue au Core, sans casser les endpoints existants.

---

## 2. État Actuel de `interfaces/api/routers/v1.py`

### 2.1 Structure actuelle

```python
# interfaces/api/routers/v1.py

class MemoryStore:
    """Stockage in-memory — PERDU AU REDÉMARRAGE."""
    def __init__(self):
        self.agents: dict = {}
        self.goals: dict = {}
        self.missions: dict = {}
        self.facts: dict = {}
        self.skills: dict = {}
        self.knowledge: dict = {}
        self.events: list = []
        self.chat_messages: list = []

_store = MemoryStore()  # Instance globale

# Endpoints avec logique métier inline :
# /v1/agents/*        → CRUD in-memory
# /v1/goals/*         → CRUD in-memory
# /v1/missions/*      → CRUD in-memory
# /v1/memory/*        → CRUD in-memory
# /v1/skills/*        → CRUD in-memory
# /v1/knowledge/*     → CRUD in-memory
# /v1/flux/*          → lecture in-memory
# /v1/settings        → dict in-memory (_default_settings)
# /v1/chat            → ProviderManager (déjà OK)
# /v1/providers       → liste hardcodée (_default_providers)
# /v1/plugins         → liste hardcodée (_default_plugins)
```

### 2.2 Problèmes identifiés

| # | Problème | Impact |
|---|---|---|
| 1 | `MemoryStore` in-memory | Données perdues au redémarrage |
| 2 | Logique métier inline dans les routes | Violation de l'architecture ETHAN |
| 3 | `_default_providers` hardcodés | Ne reflète pas la réalité du ProviderManager |
| 4 | `_default_plugins` hardcodés | Ne reflète pas le vrai système de plugins |
| 5 | `_default_settings` hardcodés | Ne reflète pas `core/config/` |
| 6 | Pas de validation métier | Les règles sont absentes ou inline |
| 7 | Pas de persistance | Aucun stockage PostgreSQL/Redis |

---

## 3. Architecture Cible

```
interfaces/api (FastAPI)
    │
    ├── routers/v1.py          ← PASSERELLE PURE (routes + sérialisation)
    ├── routers/providers.py   ← PASSERELLE PURE (déjà OK)
    ├── routers/message.py     ← PASSERELLE PURE (déjà OK)
    ├── routers/state.py       ← PASSERELLE PURE (déjà OK)
    ├── routers/internal.py    ← PASSERELLE PURE (déjà OK)
    └── auth.py                ← JWT (authentification)
        │
        ↓
core/ (Source de vérité)
    ├── agents/                ← CRÉER (AgentManager)
    ├── goals/                 ← EXISTE (GoalManager)
    ├── missions/              ← CRÉER (MissionManager)
    ├── skills/                ← EXISTE (SkillManager)
    ├── knowledge/             ← CRÉER (KnowledgeManager)
    ├── memory/                ← EXISTE (MemoryManager)
    ├── facts/                 ← EXISTE (FactStore, MemoryIngest, MemoryRetrieval)
    ├── config/                ← EXISTE (ConfigLoader, RuntimeConfig)
    ├── llm/                   ← EXISTE (ProviderManager)
    ├── bus/                   ← EXISTE (EventBus)
    └── state/                 ← EXISTE (Redis + PostgreSQL)
        │
        ↓
runtime/storage/events (NATS, Redis, PostgreSQL)
```

---

## 4. Plan de Migration par Domaine

### 4.1 Agents → `core/agents/`

**État actuel** : CRUD in-memory dans `interfaces/api/routers/v1.py` (lignes 79-118).

**État Core** : `core/agents/` n'existe pas. La classe `Agent` est dans `core/modules/base.py`. `AgentConfig` est dans `core/config/schema.py`.

**Action** :

1. Créer `core/agents/` :
   - `core/agents/__init__.py` — réexports
   - `core/agents/base.py` — façade réexportant `Agent` depuis `core/modules/base.py` et `AgentConfig` depuis `core/config/schema.py`
   - `core/agents/manager.py` — `AgentManager` avec persistance PostgreSQL/Redis
   - `core/agents/types.py` — types `Agent`, `AgentStatus`, `AgentConfig`

2. `AgentManager` :
   - `create(name, capabilities)` → persiste dans PostgreSQL
   - `get(agent_id)` → lit depuis PostgreSQL
   - `update(agent_id, data)` → met à jour dans PostgreSQL
   - `delete(agent_id)` → supprime de PostgreSQL
   - `list()` → liste depuis PostgreSQL
   - Publie des événements NATS (`agent.created`, `agent.updated`, `agent.deleted`)

3. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/agents/*` appellent `AgentManager` au lieu du `MemoryStore`
   - Validation HTTP conservée (format des requêtes/réponses)

**Fichiers** :
- Créer : `core/agents/__init__.py`, `core/agents/base.py`, `core/agents/manager.py`, `core/agents/types.py`
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.2 Goals → `core/goals/`

**État actuel** : CRUD in-memory dans `interfaces/api/routers/v1.py` (lignes 125-165).

**État Core** : `core/goals/manager.py` existe déjà avec persistance PostgreSQL + Redis + EventBus.

**Action** :

1. Étendre `core/goals/manager.py` si nécessaire :
   - Ajouter `list_goals()`, `get_goal()`, `update_goal()`, `delete_goal()` si absents
   - Vérifier que le CRUD complet est disponible

2. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/goals/*` appellent `GoalManager` au lieu du `MemoryStore`
   - Adapter le format des données (le Core utilise `intent` dict, l'API utilise `title`/`description`)

**Fichiers** :
- Modifier : `core/goals/manager.py` (si CRUD incomplet)
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.3 Missions → `core/missions/`

**État actuel** : CRUD in-memory dans `interfaces/api/routers/v1.py` (lignes 172-228).

**État Core** : `core/missions/` n'existe pas.

**Action** :

1. Créer `core/missions/` :
   - `core/missions/__init__.py` — réexports
   - `core/missions/manager.py` — `MissionManager` avec persistance PostgreSQL/Redis
   - `core/missions/types.py` — types `Mission`, `MissionStep`, `MissionStatus`, `MissionVerdict`

2. `MissionManager` :
   - `create(title, description, steps)` → persiste dans PostgreSQL
   - `get(mission_id)` → lit depuis PostgreSQL
   - `update(mission_id, data)` → met à jour dans PostgreSQL
   - `delete(mission_id)` → supprime de PostgreSQL
   - `list()` → liste depuis PostgreSQL
   - `verify_step(mission_id, step_id)` → vérifie un step
   - `approve_step(mission_id, step_id)` → approuve un step
   - Publie des événements NATS (`mission.created`, `mission.updated`, `mission.completed`)

3. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/missions/*` appellent `MissionManager` au lieu du `MemoryStore`

**Fichiers** :
- Créer : `core/missions/__init__.py`, `core/missions/manager.py`, `core/missions/types.py`
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.4 Skills → `core/skills/`

**État actuel** : CRUD in-memory dans `interfaces/api/routers/v1.py` (lignes 322-373).

**État Core** : `core/skills/` existe déjà (manager.py, registry.py, executor.py, selector.py, composer.py, lab.py, types.py).

**Action** :

1. Vérifier que `core/skills/manager.py` expose le CRUD complet :
   - `create()`, `get()`, `update()`, `delete()`, `list()`, `execute()`

2. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/skills/*` appellent `SkillManager` au lieu du `MemoryStore`
   - Adapter le format des données

**Fichiers** :
- Modifier : `core/skills/manager.py` (si CRUD incomplet)
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.5 Knowledge → `core/knowledge/`

**État actuel** : CRUD in-memory dans `interfaces/api/routers/v1.py` (lignes 380-412).

**État Core** : `core/knowledge/` n'existe pas. `core/facts/` couvre une partie (FactStore, MemoryIngest, MemoryRetrieval).

**Action** :

1. Créer `core/knowledge/` :
   - `core/knowledge/__init__.py` — réexports
   - `core/knowledge/manager.py` — `KnowledgeManager` avec persistance PostgreSQL/Redis
   - `core/knowledge/types.py` — types `KnowledgeNode`, `KnowledgeConnection`

2. `KnowledgeManager` :
   - `create(label, type, connections)` → persiste dans PostgreSQL
   - `get(knowledge_id)` → lit depuis PostgreSQL
   - `list()` → liste depuis PostgreSQL
   - `search(query)` → recherche dans PostgreSQL
   - Publie des événements NATS (`knowledge.created`, `knowledge.updated`)

3. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/knowledge/*` appellent `KnowledgeManager` au lieu du `MemoryStore`

**Fichiers** :
- Créer : `core/knowledge/__init__.py`, `core/knowledge/manager.py`, `core/knowledge/types.py`
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.6 Memory / Facts → `core/memory/` + `core/facts/`

**État actuel** : CRUD in-memory dans `interfaces/api/routers/v1.py` (lignes 234-315).

**État Core** : `core/memory/` et `core/facts/` existent déjà (MemoryManager, FactStore, MemoryIngest, MemoryRetrieval).

**Action** :

1. Vérifier que `core/memory/manager.py` et `core/facts/store.py` exposent le CRUD complet :
   - `list_events()`, `ingest()`, `search()`, `get()`
   - `list_facts()`, `create_fact()`, `get_fact()`, `search_facts()`

2. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/memory/*` appellent `MemoryManager` + `FactStore` au lieu du `MemoryStore`
   - Adapter le format des données

**Fichiers** :
- Modifier : `core/memory/manager.py` (si CRUD incomplet)
- Modifier : `core/facts/store.py` (si CRUD incomplet)
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.7 Settings → `core/config/`

**État actuel** : Dict in-memory `_default_settings` dans `interfaces/api/routers/v1.py` (lignes 439-455).

**État Core** : `core/config/` existe déjà (loader.py, schema.py, secrets.py).

**Action** :

1. Créer `core/config/settings.py` :
   - `SettingsManager` avec persistance PostgreSQL/Redis
   - `get()`, `update()` pour les sections : `llm`, `permissions`, `governance`, `budget`, `system`

2. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/settings` appellent `SettingsManager` au lieu du dict in-memory

**Fichiers** :
- Créer : `core/config/settings.py`
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.8 Providers → `core/llm/`

**État actuel** : Liste hardcodée `_default_providers` dans `interfaces/api/routers/v1.py` (lignes 558-585).

**État Core** : `core/llm/provider_manager.py` existe déjà avec `ProviderManager` complet.

**Action** :

1. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/providers` appellent `ProviderManager.list_providers()` au lieu de la liste hardcodée
   - Les routes `/v1/providers/{id}` appellent `ProviderManager.describe_provider()` au lieu de la liste hardcodée
   - Les routes `/v1/providers/{id}` (PUT) appellent `ProviderManager.register_provider()` / `set_enabled()` au lieu de la liste hardcodée

**Note** : Le router dédié `interfaces/api/routers/providers.py` existe déjà et utilise correctement `ProviderManager`. Les routes `/v1/providers` dans `v1.py` sont redondantes et doivent être supprimées ou déléguées.

**Fichiers** :
- Modifier : `interfaces/api/routers/v1.py` (supprimer les routes providers redondantes)

---

### 4.9 Plugins → `plugins/`

**État actuel** : Liste hardcodée `_default_plugins` dans `interfaces/api/routers/v1.py` (lignes 592-625).

**État Core** : `plugins/` existe déjà (manager.py, loader.py, validator.py, versioning.py, tool_registry.py).

**Action** :

1. Vérifier que `plugins/manager.py` expose le CRUD complet :
   - `list()`, `get()`, `install()`, `uninstall()`, `toggle()`

2. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/plugins` appellent `PluginManager` au lieu de la liste hardcodée

**Fichiers** :
- Modifier : `plugins/manager.py` (si CRUD incomplet)
- Modifier : `interfaces/api/routers/v1.py`

---

### 4.10 Chat → `core/llm/`

**État actuel** : Déjà correct — utilise `ProviderManager` (lignes 462-551).

**Action** : Aucune modification nécessaire, sauf :
- Remplacer l'accès direct à `_manager._registry` et `_manager._providers_config` par des méthodes publiques du `ProviderManager`
- Utiliser `ProviderManager.chat()` avec les requirements appropriés

**Fichiers** :
- Modifier : `interfaces/api/routers/v1.py` (utiliser les méthodes publiques)

---

### 4.11 Flux / Events → `core/bus/`

**État actuel** : Lecture in-memory des events dans `interfaces/api/routers/v1.py` (lignes 419-432).

**État Core** : `core/bus/` existe déjà (EventBus, store, router, monitor).

**Action** :

1. Vérifier que `core/bus/store.py` expose la lecture des événements :
   - `list_events()`, `get_event()`

2. `interfaces/api/routers/v1.py` :
   - Les routes `/v1/flux` appellent `EventBus` / `EventStore` au lieu du `MemoryStore`

**Fichiers** :
- Modifier : `core/bus/store.py` (si lecture incomplète)
- Modifier : `interfaces/api/routers/v1.py`

---

## 5. Ordre de Migration Recommandé

### Phase 1 — Réparations immédiates (P0)

| # | Action | Risque |
|---|---|---|
| 1.1 | Créer `core/agents/` (façade + AgentManager) | Faible |
| 1.2 | Créer `core/missions/` (MissionManager) | Moyen |
| 1.3 | Créer `core/knowledge/` (KnowledgeManager) | Moyen |
| 1.4 | Créer `core/config/settings.py` (SettingsManager) | Faible |

### Phase 2 — Migration des routes (P1)

| # | Action | Risque |
|---|---|---|
| 2.1 | Migrer `/v1/agents/*` vers `AgentManager` | Moyen |
| 2.2 | Migrer `/v1/goals/*` vers `GoalManager` | Moyen |
| 2.3 | Migrer `/v1/missions/*` vers `MissionManager` | Moyen |
| 2.4 | Migrer `/v1/skills/*` vers `SkillManager` | Moyen |
| 2.5 | Migrer `/v1/knowledge/*` vers `KnowledgeManager` | Moyen |
| 2.6 | Migrer `/v1/memory/*` vers `MemoryManager` + `FactStore` | Moyen |
| 2.7 | Migrer `/v1/settings` vers `SettingsManager` | Faible |
| 2.8 | Migrer `/v1/plugins` vers `PluginManager` | Faible |
| 2.9 | Supprimer les routes `/v1/providers` redondantes | Faible |
| 2.10 | Migrer `/v1/flux` vers `EventBus` | Faible |

### Phase 3 — Nettoyage (P2)

| # | Action | Risque |
|---|---|---|
| 3.1 | Supprimer la classe `MemoryStore` de `interfaces/api/routers/v1.py` | Faible |
| 3.2 | Supprimer `_default_providers` et `_default_plugins` | Faible |
| 3.3 | Supprimer `_default_settings` | Faible |
| 3.4 | Vérifier que `pytest tests/` passe | — |

---

## 6. Règles de Non-Régression

1. **Les endpoints existants doivent continuer à fonctionner** — mêmes routes, mêmes formats de requête/réponse.
2. **Migration progressive** — chaque domaine est migré indépendamment.
3. **Tests existants** — `pytest tests/` doit passer après chaque migration.
4. **Validation HTTP conservée dans l'API** — le Core ne gère pas le HTTP.
5. **Sérialisation conservée dans l'API** — le Core retourne des objets métier, l'API les sérialise.
6. **Authentification conservée dans l'API** — JWT + RBAC restent dans `interfaces/api/auth.py`.
7. **Aucune suppression de fonctionnalité** — chaque route migrée doit avoir un équivalent fonctionnel.

---

## 7. Résultat Attendu

Après migration, `interfaces/api/routers/v1.py` sera une **passerelle pure** :

```python
# interfaces/api/routers/v1.py (après migration)

from core.agents.manager import AgentManager
from core.goals.manager import GoalManager
from core.missions.manager import MissionManager
from core.skills.manager import SkillManager
from core.knowledge.manager import KnowledgeManager
from core.memory.manager import MemoryManager
from core.facts.store import FactStore
from core.config.settings import SettingsManager
from core.llm.provider_manager import ProviderManager

# Injection des managers au startup
_agents: AgentManager | None = None
_goals: GoalManager | None = None
_missions: MissionManager | None = None
_skills: SkillManager | None = None
_knowledge: KnowledgeManager | None = None
_memory: MemoryManager | None = None
_facts: FactStore | None = None
_settings: SettingsManager | None = None

@router.get("/agents")
async def list_agents():
    return await _agents.list()

@router.post("/agents")
async def create_agent(data: dict[str, Any]):
    return await _agents.create(**data)

# ... etc. — chaque route délègue au Core
```

**Aucune logique métier, aucun stockage, aucune règle dans l'API.**