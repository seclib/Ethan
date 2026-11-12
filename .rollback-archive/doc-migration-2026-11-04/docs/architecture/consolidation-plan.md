# ETHAN — Plan de Consolidation Architecture

**Date** : 2026-03-08  
**Auteur** : Architecture Audit Agent  
**Statut** : Proposition — aucune modification de code effectuée  
**Portée** : `core/`, `interfaces/api/`, `interfaces/webui/`, `interfaces/cli/`, `plugins/`

---

## 1. Résumé Exécutif

ETHAN souffre actuellement de **doublons internes au Core** et d'une **violation du principe de séparation** : la logique métier est partiellement implémentée dans l'interface API (`interfaces/api/routers/v1.py`) avec un stockage in-memory non persistant.

Le constat principal :

1. **`core/llm/` et `core/providers/`** implémentent deux systèmes de providers LLM parallèles.
2. **`core/llm/__init__.py`** duplique des types déjà définis dans `core/llm/types.py`.
3. **`interfaces/api/routers/v1.py`** contient toute la logique métier (agents, goals, missions, skills, knowledge, memory, settings, providers, plugins) en mémoire — perdue au redémarrage.
4. **`core/agents/`** est référencé par `core/executive/` et `core/cognition/` mais **n'existe pas** (import cassé).
5. **Planner et Goals** existent en triple exemplaire dans le Core.
6. **RAG, Documents, Missions, Knowledge** n'ont pas de module Core dédié.

---

## 2. Systèmes Dupliqués

### 2.1 Providers LLM — Doublon critique

| Emplacement | Rôle | Dépendances | Qualité |
|---|---|---|---|
| `core/llm/providers/` (8 providers) | Système moderne : `LLMProviderRegistry`, `LLMSelector`, `LLMClient`, `LLMRouter`, `ProviderManager`, `ProviderStore` | `core/llm/types.py`, `core/llm/registry.py`, `core/config/secrets.py` | ✅ Complet, persistant, testé |
| `core/providers/` (3 providers) | Système legacy : `ReasoningProvider`, `ProviderRegistry` simple | **Importe depuis `core/llm`** | ⚠️ Redondant, moins complet |
| `core/llm/__init__.py` | Définit ses propres `ChatMessage`, `ChatResponse`, `ModelInfo`, `LLMProvider`, `ProviderRegistry` | — | ⚠️ Doublon interne avec `core/llm/types.py` |

**Meilleure implémentation à conserver** : `core/llm/`  
**Action** : Fusionner `core/providers/` → `core/llm/providers/` avec shim de compatibilité. Supprimer les types dupliqués de `core/llm/__init__.py` (garder les réexports).

### 2.2 Planner — Triple doublon

| Emplacement | Rôle | Dépendances |
|---|---|---|
| `core/planner/` (planner.py, goal_manager.py, dag.py, checkpoint.py, optimizer.py, decomposer.py) | Planner complet avec DAG, checkpoints, optimizer | `core/registry/` |
| `core/modules/planner/main.py` | Module NATS qui décompose les tâches en étapes (`PLANNER_RULES`) | `core/ethan_types/`, NATS |
| `core/executive/` (executive.py, goal_manager.py) | Executive qui crée des goals et délègue au Planner | `core/agents/` (cassé), `core/ethan_types/` |

**Meilleure implémentation à conserver** : `core/planner/`  
**Action** : Unifier les 3 implémentations vers `core/planner/`. Le module NATS (`core/modules/planner/`) doit devenir un wrapper qui appelle `core/planner/`.

### 2.3 Goals — Triple doublon

| Emplacement | Rôle | Dépendances |
|---|---|---|
| `core/goals/manager.py` | GoalManager avec persistance PostgreSQL + Redis + EventBus | `core/bus/`, `core/state/`, `core/ethan_types/` |
| `core/planner/goal_manager.py` | GoalManager avec priorités et détection de conflits | `core/planner/types.py` |
| `core/executive/goal_manager.py` | ExecutiveGoalManager avec cycle de vie complet | `core/executive/types.py`, `core/ethan_types/` |

**Meilleure implémentation à conserver** : `core/goals/manager.py` (persistance réelle via PostgreSQL/Redis)  
**Action** : Unifier les 3 implémentations vers `core/goals/`. Les fonctionnalités de priorisation et de conflits de `core/planner/goal_manager.py` doivent être fusionnées dans `core/goals/`.

### 2.4 Agents — Import cassé

| Emplacement | Rôle |
|---|---|
| `core/modules/base.py` | Définit `Module` et `Agent` (classes de base) |
| `core/config/schema.py` | Définit `AgentConfig` |
| `core/executive/executive.py` | Importe `from core.agents.base import Agent, AgentConfig` — **cassé** |
| `core/cognition/module.py` | Importe `from core.agents.base import Agent, AgentConfig` — **cassé** |

**Action** : Créer `core/agents/` comme façade réexportant `Agent` depuis `core/modules/base.py` et `AgentConfig` depuis `core/config/schema.py`.

### 2.5 Configuration — Doublon partiel

| Emplacement | Rôle |
|---|---|
| `core/config/` (loader.py, schema.py, secrets.py) | Configuration runtime complète (bus, storage, agents) |
| `interfaces/cli/core/config.py` | Configuration CLI locale (`~/.config/ethan/`) |
| `interfaces/api/routers/v1.py` | Settings in-memory (`_default_settings`) |

**Meilleure implémentation à conserver** : `core/config/` pour le runtime. La CLI garde sa config locale (spécifique à l'interface).  
**Action** : Migrer les settings de `interfaces/api/routers/v1.py` vers `core/config/`.

### 2.6 Stockage — Doublon partiel

| Emplacement | Rôle |
|---|---|
| `core/state/` (redis_state.py, postgres_state.py, composite_backend.py) | État unifié Redis + PostgreSQL |
| `core/memory/` (redis_store.py, pg_store.py, chromadb_backend.py, qdrant_backend.py) | Stockage mémoire vectoriel |
| `core/llm/store.py` | ProviderStore (PostgreSQL + Redis) |
| `interfaces/api/routers/v1.py` | `MemoryStore` in-memory (agents, goals, missions, skills, knowledge, events) |

**Meilleure implémentation à conserver** : `core/state/` + `core/memory/` + `core/llm/store.py`  
**Action** : Supprimer le `MemoryStore` in-memory de l'API et le remplacer par des appels au Core.

---

## 3. Source de Vérité par Domaine

| Domaine | Propriétaire actuel | Propriétaire cible | Action |
|---|---|---|---|
| **LLM** | `core/llm/` + `core/providers/` + `core/llm/__init__.py` | `core/llm/` | Fusionner `core/providers/` → `core/llm/providers/` ; supprimer les types dupliqués de `core/llm/__init__.py` |
| **Providers** | `core/llm/provider_manager.py` + `core/providers/` | `core/llm/provider_manager.py` | Supprimer `core/providers/` (legacy) avec shim |
| **Memory** | `core/memory/` + `core/facts/` + `core/modules/memory/` | `core/memory/` + `core/facts/` | Unifier les modules NATS vers `core/memory/` |
| **RAG** | **Aucun** (`core/rag/` n'existe pas) | `core/rag/` | Créer le module RAG (ingestion, embeddings, retrieval, context) |
| **Documents** | **Aucun** (page WebUI placeholder) | `core/rag/` | Créer le module documents dans `core/rag/` |
| **Planner** | `core/planner/` + `core/modules/planner/` + `core/executive/` | `core/planner/` | Unifier les 3 implémentations |
| **Goals** | `core/goals/` + `core/planner/goal_manager.py` + `core/executive/goal_manager.py` | `core/goals/` | Unifier les 3 implémentations |
| **Agents** | **Aucun** (`core/agents/` n'existe pas, import cassé) | `core/agents/` | Créer le module agents (façade sur `core/modules/base.py`) |
| **Skills** | `core/skills/` | `core/skills/` | ✅ OK — pas de doublon |
| **Knowledge** | **Partiel** (`core/facts/` couvre une partie) | `core/knowledge/` | Créer le module knowledge |
| **Missions** | **Aucun** (in-memory dans `interfaces/api/routers/v1.py`) | `core/missions/` | Créer le module missions |
| **Settings** | **Partiel** (in-memory dans `interfaces/api/routers/v1.py`) | `core/config/` | Migrer les settings vers `core/config/` |
| **Authentication** | `core/auth/` (RBAC) + `interfaces/api/auth.py` (JWT) | `core/auth/` | ✅ OK — RBAC au Core, JWT à l'API |
| **Plugins** | `plugins/` | `plugins/` | ✅ OK — pas de doublon |
| **Flux/Events** | `core/bus/` + `core/events/` | `core/bus/` | ✅ OK — pas de doublon |

---

## 4. Cartographie des Dépendances

### 4.1 État actuel

```
WebUI (React/Next.js)
    ↓ (proxy /api/*)
interfaces/api/ (FastAPI)
    ├── routers/v1.py  ← LOGIQUE MÉTIER IN-MEMORY (violation)
    ├── routers/providers.py  ← OK (appelle ProviderManager)
    ├── routers/message.py  ← OK (publie sur NATS)
    ├── routers/state.py  ← OK (expose l'état)
    ├── routers/internal.py  ← OK (audit, budget, facts, approval)
    └── auth.py  ← OK (JWT)
        ↓
core/
    ├── llm/ (ProviderManager, LLMClient, etc.)
    ├── bus/ (EventBus, NATS)
    ├── state/ (Redis + PostgreSQL)
    ├── goals/ (GoalManager)
    ├── planner/ (Planner, DAG)
    ├── memory/ (MemoryManager)
    ├── facts/ (FactStore, MemoryIngest, MemoryRetrieval)
    ├── skills/ (SkillManager)
    ├── modules/ (Module, Agent, ExecutiveModule, PlannerModule, MemoryModule)
    └── kernel.py (CognitiveKernel — orchestrateur)
        ↓
Runtime (NATS, Redis, PostgreSQL)
```

### 4.2 Inversions de dépendances identifiées

| # | Inversion | Impact |
|---|---|---|
| 1 | `interfaces/api/routers/v1.py` contient la logique métier (agents, goals, missions, skills, knowledge, memory, settings, providers, plugins) en in-memory | **Critique** — la logique métier est dans l'interface, pas dans le Core |
| 2 | `core/executive/executive.py` et `core/cognition/module.py` importent `core.agents.base` qui n'existe pas | **Critique** — import cassé |
| 3 | `core/providers/` importe depuis `core/llm/` mais définit ses propres types | **Moyen** — doublon interne |
| 4 | `core/llm/__init__.py` définit des types qui existent déjà dans `core/llm/types.py` | **Moyen** — doublon interne |
| 5 | `interfaces/cli/core/config.py` duplique la logique de configuration | **Faible** — spécifique CLI, acceptable |

### 4.3 État cible

```
WebUI (React/Next.js) — UI pure
    ↓ (proxy /api/*)
interfaces/api/ (FastAPI) — Gateway pure
    ├── routers/v1.py  ← CLIENT PUR (appelle le Core)
    ├── routers/providers.py  ← CLIENT PUR (appelle ProviderManager)
    ├── routers/message.py  ← CLIENT PUR (publie sur NATS)
    ├── routers/state.py  ← CLIENT PUR (expose l'état)
    ├── routers/internal.py  ← CLIENT PUR (audit, budget, facts, approval)
    └── auth.py  ← JWT (authentification)
        ↓
core/ — Source de vérité
    ├── llm/ (ProviderManager, LLMClient, etc.)
    ├── agents/ (Agent, AgentConfig — façade)
    ├── missions/ (MissionManager)
    ├── knowledge/ (KnowledgeManager)
    ├── rag/ (ingestion, embeddings, retrieval, context)
    ├── bus/ (EventBus, NATS)
    ├── state/ (Redis + PostgreSQL)
    ├── goals/ (GoalManager — unifié)
    ├── planner/ (Planner, DAG — unifié)
    ├── memory/ (MemoryManager)
    ├── facts/ (FactStore, MemoryIngest, MemoryRetrieval)
    ├── skills/ (SkillManager)
    ├── config/ (Settings, RuntimeConfig)
    └── kernel.py (CognitiveKernel — orchestrateur)
        ↓
Runtime (NATS, Redis, PostgreSQL)
```

---

## 5. Classification des Responsabilités

### A. Doit rester dans WebUI (UI pure)

- Composants graphiques (`components/`)
- Pages (`app/(dashboard)/`)
- Navigation, thèmes, animations
- Hooks React (`features/*/hooks/`) — ce sont des clients API
- Services WebUI (`features/*/services/`) — ce sont des clients API
- Store UI (`core/store/ui.store.ts`)

### B. Doit appartenir au Core

- **Logique métier** actuellement dans `interfaces/api/routers/v1.py` :
  - Agents → `core/agents/`
  - Goals → `core/goals/`
  - Missions → `core/missions/`
  - Skills → `core/skills/`
  - Knowledge → `core/knowledge/`
  - Memory → `core/memory/` + `core/facts/`
  - Settings → `core/config/`
  - Providers → `core/llm/`
  - Plugins → `plugins/`
- **Doublons internes** :
  - `core/providers/` → fusionner dans `core/llm/providers/`
  - `core/llm/__init__.py` → supprimer les types dupliqués
  - `core/modules/planner/` → wrapper sur `core/planner/`
  - `core/executive/` → wrapper sur `core/goals/` + `core/planner/`
  - `core/planner/goal_manager.py` → fusionner dans `core/goals/`
  - `core/executive/goal_manager.py` → fusionner dans `core/goals/`

### C. Doit être partagé via API/Event

- Tous les endpoints REST dans `interfaces/api/` (déjà le cas)
- Les événements NATS via `core/bus/` (déjà le cas)
- Les WebSockets via `interfaces/webui/src/core/providers/websocket-provider.tsx`

---

## 6. Plan de Migration Contrôlée

### Phase 0 — Réparations immédiates (P0)

**Objectif** : Réparer les imports cassés et les doublons critiques.

| # | Action | Fichiers | Risque |
|---|---|---|---|
| 0.1 | Créer `core/agents/` (façade réexportant `Agent` depuis `core/modules/base.py` et `AgentConfig` depuis `core/config/schema.py`) | `core/agents/__init__.py`, `core/agents/base.py` | Faible |
| 0.2 | Supprimer les types dupliqués de `core/llm/__init__.py` (garder les réexports) | `core/llm/__init__.py` | Faible |
| 0.3 | Fusionner `core/providers/` → `core/llm/providers/` avec shim de compatibilité | `core/providers/__init__.py`, `core/providers/providers/*.py` | Moyen |

**Critère de sortie** : `pytest tests/` passe, `python -c "from core.executive.executive import ExecutiveModule"` fonctionne.

### Phase 1 — Migration de la logique métier (P1)

**Objectif** : Sortir la logique métier de `interfaces/api/routers/v1.py` vers le Core.

| # | Action | Fichiers | Risque |
|---|---|---|---|
| 1.1 | Créer `core/missions/` — migrer les missions depuis `interfaces/api/routers/v1.py` | `core/missions/__init__.py`, `core/missions/manager.py`, `core/missions/types.py` | Moyen |
| 1.2 | Créer `core/knowledge/` — migrer le knowledge depuis `interfaces/api/routers/v1.py` | `core/knowledge/__init__.py`, `core/knowledge/manager.py`, `core/knowledge/types.py` | Moyen |
| 1.3 | Migrer les settings vers `core/config/` | `core/config/settings.py` | Moyen |
| 1.4 | Transformer `interfaces/api/routers/v1.py` en client pur qui appelle le Core | `interfaces/api/routers/v1.py` | Moyen |

**Critère de sortie** : Tous les endpoints `/v1/*` fonctionnent avec persistance PostgreSQL/Redis au lieu de l'in-memory.

### Phase 2 — Unification des doublons Core (P2)

**Objectif** : Unifier les implémentations parallèles dans le Core.

| # | Action | Fichiers | Risque |
|---|---|---|---|
| 2.1 | Unifier `core/planner/` + `core/modules/planner/` + `core/executive/` → `core/planner/` | `core/planner/`, `core/modules/planner/`, `core/executive/` | Moyen |
| 2.2 | Unifier `core/goals/` + `core/planner/goal_manager.py` + `core/executive/goal_manager.py` → `core/goals/` | `core/goals/`, `core/planner/goal_manager.py`, `core/executive/goal_manager.py` | Moyen |
| 2.3 | Unifier `core/modules/memory/` → `core/memory/` | `core/modules/memory/`, `core/memory/` | Faible |

**Critère de sortie** : Une seule implémentation par domaine, les autres deviennent des wrappers ou sont supprimées.

### Phase 3 — Création des modules manquants (P3)

**Objectif** : Créer les modules Core manquants.

| # | Action | Fichiers | Risque |
|---|---|---|---|
| 3.1 | Créer `core/rag/` (ingestion, embeddings, retrieval, context) | `core/rag/__init__.py`, `core/rag/ingestion.py`, `core/rag/embeddings.py`, `core/rag/retrieval.py`, `core/rag/context.py` | Moyen |
| 3.2 | Créer `core/documents/` (gestion documentaire) | `core/documents/__init__.py`, `core/documents/manager.py`, `core/documents/types.py` | Moyen |
| 3.3 | Connecter la page WebUI Documents au Core RAG | `interfaces/webui/src/app/(dashboard)/documents/page.tsx` | Faible |

**Critère de sortie** : La page Documents de la WebUI affiche de vrais documents ingérés via le Core.

---

## 7. Règles de Non-Régression

1. **Aucune suppression** de fonctionnalité existante sans remplacement équivalent.
2. **Shims de compatibilité** : tout module déplacé garde un `__init__.py` qui réexporte depuis le nouvel emplacement.
3. **Tests existants** : `pytest tests/` doit passer après chaque phase.
4. **Migration progressive** : chaque phase est indépendante et réversible.
5. **Comparaison avant réécriture** : toute fonctionnalité existante est considérée comme une base validée.
6. **Documentation** : chaque phase doit mettre à jour `docs/architecture/`.

---

## 8. Priorités

| Priorité | Action | Justification |
|---|---|---|
| **P0** | Réparer `core/agents/` (import cassé) | Bloquant — `core/executive/` et `core/cognition/` ne peuvent pas importer |
| **P0** | Fusionner `core/providers/` → `core/llm/providers/` | Doublon critique — deux systèmes de providers parallèles |
| **P0** | Supprimer les types dupliqués de `core/llm/__init__.py` | Doublon interne — risque de confusion |
| **P1** | Migrer la logique métier de `interfaces/api/routers/v1.py` vers le Core | Violation architecturale — logique métier dans l'interface |
| **P1** | Créer `core/missions/` et `core/knowledge/` | Modules manquants — logique actuellement in-memory |
| **P2** | Unifier Planner et Goals | Triple doublon dans le Core |
| **P3** | Créer `core/rag/` et `core/documents/` | Capacités manquantes — RAG est une capacité ETHAN fondamentale |

---

## 9. Conclusion

ETHAN a une architecture globalement saine : le Kernel est un orchestrateur pur, le bus d'événements est centralisé, l'état est externalisé (Redis + PostgreSQL), et la WebUI est un client API.

Les problèmes identifiés sont :

1. **Doublons internes au Core** (providers LLM, planner, goals) — à unifier
2. **Logique métier dans l'interface API** (`interfaces/api/routers/v1.py`) — à migrer vers le Core
3. **Imports cassés** (`core/agents/`) — à réparer
4. **Modules manquants** (RAG, Documents, Missions, Knowledge) — à créer

Le plan de migration proposé est **progressif, réversible et sans suppression de fonctionnalités**. Chaque phase est indépendante et peut être validée par les tests existants.