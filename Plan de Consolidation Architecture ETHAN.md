## Plan de Consolidation Architecture ETHAN

J'ai analysé en profondeur l'architecture actuelle. Voici le diagnostic complet et la stratégie de consolidation.

---

### 1. Systèmes dupliqués identifiés

#### 1.1 Providers LLM — **DOUBLON CRITIQUE**

| Emplacement | Rôle | Dépendances |
|---|---|---|
| `core/llm/providers/` (8 providers) | Système moderne : `LLMProviderRegistry`, `LLMSelector`, `LLMClient`, `LLMRouter`, `ProviderManager`, `ProviderStore` | `core/llm/types.py`, `core/llm/registry.py`, `core/config/secrets.py` |
| `core/providers/` (3 providers) | Système legacy : `ReasoningProvider`, `ProviderRegistry` simple | **Importe depuis `core/llm`** (le `__init__.py` définit ses propres types) |
| `core/llm/__init__.py` | Définit ses propres `ChatMessage`, `ChatResponse`, `ModelInfo`, `LLMProvider`, `ProviderRegistry` | **Doublon interne** avec `core/llm/types.py` et `core/llm/registry.py` |

**Meilleure implémentation à conserver** : `core/llm/` (complet, persistant, avec factory et store)

#### 1.2 Planner — **TRIPLE DOUBLON**

| Emplacement | Rôle |
|---|---|
| `core/planner/` (planner.py, goal_manager.py, dag.py, etc.) | Planner complet avec DAG, checkpoints, optimizer |
| `core/modules/planner/main.py` | Module NATS qui décompose les tâches en étapes (PLANNER_RULES) |
| `core/executive/` (executive.py, goal_manager.py) | Executive qui crée des goals et délègue au Planner |

**Meilleure implémentation à conserver** : `core/planner/` (le plus complet)

#### 1.3 Goals — **TRIPLE DOUBLON**

| Emplacement | Rôle |
|---|---|
| `core/goals/manager.py` | GoalManager avec persistance PostgreSQL + Redis + EventBus |
| `core/planner/goal_manager.py` | GoalManager avec priorités et conflits |
| `core/executive/goal_manager.py` | ExecutiveGoalManager avec cycle de vie |

**Meilleure implémentation à conserver** : `core/goals/manager.py` (persistance réelle)

#### 1.4 Agents — **IMPORT CASSÉ**

- `core/executive/executive.py` et `core/cognition/module.py` importent `from core.agents.base import Agent, AgentConfig`
- **`core/agents/` n'existe pas** — import cassé
- La classe `Agent` existe dans `core/modules/base.py`
- `AgentConfig` existe dans `core/config/schema.py`

**Action** : Créer `core/agents/` comme façade réexportant depuis `core/modules/base.py` et `core/config/schema.py`

#### 1.5 Configuration — **DOUBLON**

| Emplacement | Rôle |
|---|---|
| `core/config/` (loader.py, schema.py, secrets.py) | Configuration runtime complète |
| `interfaces/cli/core/config.py` | Configuration CLI locale (`~/.config/ethan/`) |
| `interfaces/api/routers/v1.py` | Settings in-memory (`_default_settings`) |

**Meilleure implémentation à conserver** : `core/config/` pour le runtime, CLI garde sa config locale (spécifique interface)

#### 1.6 Stockage — **DOUBLON**

| Emplacement | Rôle |
|---|---|
| `core/state/` (redis_state.py, postgres_state.py, composite_backend.py) | État unifié Redis + PostgreSQL |
| `core/memory/` (redis_store.py, pg_store.py, chromadb_backend.py, qdrant_backend.py) | Stockage mémoire |
| `core/llm/store.py` | ProviderStore (PostgreSQL + Redis) |
| `interfaces/api/routers/v1.py` | `MemoryStore` in-memory (agents, goals, missions, skills, knowledge, events) |

**Meilleure implémentation à conserver** : `core/state/` + `core/memory/` + `core/llm/store.py` — supprimer le `MemoryStore` in-memory de l'API

---

### 2. Source de vérité par domaine

| Domaine | Propriétaire actuel | Propriétaire cible | Action |
|---|---|---|---|
| **LLM** | `core/llm/` + `core/providers/` + `core/llm/__init__.py` | `core/llm/` | Fusionner `core/providers/` → `core/llm/providers/` ; supprimer les types dupliqués de `core/llm/__init__.py` |
| **Providers** | `core/llm/provider_manager.py` + `core/providers/` | `core/llm/provider_manager.py` | Supprimer `core/providers/` (legacy) |
| **Memory** | `core/memory/` + `core/facts/` + `core/modules/memory/` | `core/memory/` + `core/facts/` | Unifier les modules NATS vers `core/memory/` |
| **RAG** | **Aucun** (`core/rag/` n'existe pas) | `core/rag/` | Créer le module RAG (ingestion, embeddings, retrieval, context) |
| **Documents** | **Aucun** (page WebUI placeholder) | `core/rag/` | Créer le module documents dans `core/rag/` |
| **Planner** | `core/planner/` + `core/modules/planner/` + `core/executive/` | `core/planner/` | Unifier les 3 implémentations |
| **Goals** | `core/goals/` + `core/planner/goal_manager.py` + `core/executive/goal_manager.py` | `core/goals/` | Unifier les 3 implémentations |
| **Agents** | **Aucun** (`core/agents/` n'existe pas, import cassé) | `core/agents/` | Créer le module agents (façade sur `core/modules/base.py`) |
| **Skills** | `core/skills/` | `core/skills/` | OK — pas de doublon |
| **Knowledge** | **Partiel** (`core/facts/` couvre une partie) | `core/knowledge/` | Créer le module knowledge |
| **Missions** | **Aucun** (in-memory dans `interfaces/api/routers/v1.py`) | `core/missions/` | Créer le module missions |
| **Settings** | **Partiel** (in-memory dans `interfaces/api/routers/v1.py`) | `core/config/` | Migrer les settings vers `core/config/` |
| **Authentication** | `core/auth/` (RBAC) + `interfaces/api/auth.py` (JWT) | `core/auth/` | OK — RBAC au Core, JWT à l'API |
| **Plugins** | `plugins/` | `plugins/` | OK — pas de doublon |
| **Flux/Events** | `core/bus/` + `core/events/` | `core/bus/` | OK — pas de doublon |

---

### 3. Cartographie des dépendances

```
État actuel (avec inversions) :

WebUI ──→ API (proxy) ──→ interfaces/api/routers/v1.py (logique métier in-memory)
                              ↓
                         core/llm/ (ProviderManager)
                              ↓
                         core/ (kernel, bus, state)

CLI ──→ core/ (kernel_client) + config locale
```

**Inversions identifiées** :

1. **`interfaces/api/routers/v1.py`** contient la logique métier (agents, goals, missions, skills, knowledge, memory, settings, providers, plugins) en in-memory — **violation directe** de l'architecture
2. **`core/executive/executive.py`** et **`core/cognition/module.py`** importent `core.agents.base` qui n'existe pas — **import cassé**
3. **`core/providers/`** importe depuis `core/llm/` mais définit ses propres types — **doublon interne**
4. **`core/llm/__init__.py`** définit des types qui existent déjà dans `core/llm/types.py` — **doublon interne**

---

### 4. Plan de migration contrôlée

#### Phase 0 — Réparations immédiates (P0)
1. Créer `core/agents/` (façade réexportant `Agent` depuis `core/modules/base.py` et `AgentConfig` depuis `core/config/schema.py`)
2. Supprimer les types dupliqués de `core/llm/__init__.py` (garder les réexports)
3. Fusionner `core/providers/` → `core/llm/providers/` (garder un shim de compatibilité)

#### Phase 1 — Migration de la logique métier (P1)
1. Créer `core/missions/` — migrer les missions depuis `interfaces/api/routers/v1.py`
2. Créer `core/knowledge/` — migrer le knowledge depuis `interfaces/api/routers/v1.py`
3. Migrer les settings vers `core/config/`
4. Transformer `interfaces/api/routers/v1.py` en **client pur** qui appelle le Core

#### Phase 2 — Unification des doublons Core (P2)
1. Unifier `core/planner/` + `core/modules/planner/` + `core/executive/` → `core/planner/`
2. Unifier `core/goals/` + `core/planner/goal_manager.py` + `core/executive/goal_manager.py` → `core/goals/`
3. Unifier `core/modules/memory/` → `core/memory/`

#### Phase 3 — Création des modules manquants (P3)
1. Créer `core/rag/` (ingestion, embeddings, retrieval, context)
2. Créer `core/documents/` (gestion documentaire)
3. Connecter la page WebUI Documents au Core RAG

---

### 5. Règles de non-régression

- **Aucune suppression** de fonctionnalité existante
- **Shims de compatibilité** : `core/providers/` garde un `__init__.py` qui réexporte depuis `core/llm/`
- **Tests existants** : vérifier que `pytest tests/` passe après chaque phase
- **Migration progressive** : chaque phase est indépendante et réversible

---

### Prochaines étapes

Pour créer le rapport `docs/architecture/consolidation-plan.md`, je dois passer en **ACT MODE** pour :
1. Cré