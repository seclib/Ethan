# 📊 Analyse de la Dette Technique ETHAN

**Date** : 22/07/2026  
**Analyste** : Architecte Logiciel  
**Statut** : Analyse complète — Nettoyage Phase 1 et Phase 2 effectués

## Changements Effectués

### Phase 1 — Nettoyage immédiat (faible risque) ✅

| Action | Fichiers/Dossiers |
|--------|-------------------|
| Suppression fichiers Go morts | `core/executor/executor.go`, `retry.go`, `core/gateway/gateway.go`, `core/state/manager.go` |
| Suppression répertoires Go morts | `core/ingest/`, `core/intent/`, `core/resolver/`, `core/router/`, `core/service/`, `core/response/` |
| Suppression code mort Python | `core/executor/` (entier), `core/state/state.py` |
| Suppression WebUI obsolète | `webui/` (racine) |
| Suppression répertoires vides | `core/workflow/`, `plugins/registry/`, `plugins/store/`, `interfaces/mcp/`, `infrastructure/configs/` |

### Phase 2 — Résolution de duplications ✅

| Action | Détails |
|--------|---------|
| Migration `core/events/__init__.py` | Import de `core.bus.memory_bus` au lieu de `core.bus.memory` |
| Suppression anciens bus | `core/bus/nats.py`, `core/bus/memory.py` |
| Mise à jour tests | `tests/test_core/test_bus.py`, `tests/test_core/test_agents.py` → `core.bus.memory_bus` |
| Suppression `core/cognition/planner/` | Incomplet, remplacé par `core/planner/` |
| Unification `plugins/sandbox` | `sandbox.py` → `sandbox/core.py`, `__init__.py` mis à jour pour exporter `PluginSandbox`, `PluginRuntime` |
| Unification `colors.py` | `interfaces/cli/ui/colors.py` supprimé, `config_cmd.py` mis à jour vers `core/colors.py` |

### Phase 2 — Reporté

| Action | Raison |
|--------|--------|
| Unification `core/skills/` + `core/tools/` | `core/skills/` importe `ToolManager` depuis `core.tools.manager` — unification nécessite un refactoring plus approfondi |
| Correction `nats_bus.py` Event type | `nats_bus.py` définit sa propre classe `Event` — nécessite de vérifier la compatibilité avec `kernel.py` |
| Consolidation commandes plugin | `plugin.py` vs `plugin_cmd.py` vs `plugins.py` — chargement dynamique, nécessite analyse du registry |

---

## Synthèse Exécutive

Le projet ETHAN présente **une dette technique importante** résultant de **deux transitions architecturales** :

1. **Go → Python** : Le kernel a été réécrit de Go vers Python, laissant des fichiers `.go` morts dans des répertoires Python
2. **Ancienne → Nouvelle architecture** : Plusieurs modules ont été remplacés par des versions "clean architecture" mais les anciens fichiers sont restés

**Architecture cible :** `core/` | `runtime/` | `plugins/` | `interfaces/` | `infrastructure/`

---

## 1. Fichiers Go Morts (ancienne architecture kernel)

**10 fichiers Go** orphelins dans des répertoires Python. Aucun n'est importé par le code Python actif.

| Fichier | Pourquoi supprimer | Impact | Remplacement |
|---------|-------------------|--------|--------------|
| `core/executor/executor.go` | Vestige kernel Go | Aucun | `core/orchestrator/executor.py` |
| `core/executor/retry.go` | Même raison | Aucun | `core/orchestrator/executor.py` |
| `core/gateway/gateway.go` | Ancienne passerelle HTTP Go | Aucun | `interfaces/api/main.py` |
| `core/ingest/ingest.go` | Ancien ingérateur Go, répertoire ne contient QUE ce fichier | Aucun | `core/facts/ingest.py` |
| `core/intent/intent.go` | Ancienne gestion d'intentions Go, répertoire ne contient QUE ce fichier | Aucun | `core/context/intent.py` |
| `core/resolver/resolver.go` | Ancien résolveur Go, répertoire ne contient QUE ce fichier | Aucun | `core/cognition/` |
| `core/router/router.go` | Ancien routeur Go, répertoire ne contient QUE ce fichier | Aucun | `core/bus/router.py` |
| `core/service/service.go` | Ancien service Go, répertoire ne contient QUE ce fichier | Aucun | `infrastructure/systemd/` |
| `core/response/builder.go` | Ancien builder de réponse Go, répertoire ne contient QUE ce fichier | Aucun | À créer en Python si besoin |
| `core/state/manager.go` | Ancien gestionnaire d'état Go | Aucun | `core/state/interface.py` + implémentations |

**Action :** Supprimer tous ces fichiers `.go` et les répertoires qui ne contiennent que des fichiers Go (`core/ingest/`, `core/intent/`, `core/resolver/`, `core/router/`, `core/service/`, `core/response/`).

---

## 2. Duplication Bus (core/bus/)

**4 fichiers** pour 2 implémentations (NATS + InMemory).

| Fichier | Type | Utilisé par | Statut |
|---------|------|-------------|--------|
| `core/bus/nats.py` | OLD — `NATSBus`, `connect(servers)` | `core/events/__init__.py`, tests | À migrer |
| `core/bus/nats_bus.py` | NEW — `EventBus`, `connect()` | `core/bootstrap.py`, bootstrap modules | Actif |
| `core/bus/memory.py` | OLD — `InMemoryBus`, `connect(servers)` | `core/events/__init__.py`, tests | À migrer |
| `core/bus/memory_bus.py` | NEW — `InMemoryBus`, `MemoryEventBus` alias | `core/main.py`, tests | Actif |

**Problème :** `nats_bus.py` définit sa propre classe `Event` au lieu d'utiliser `core.ethan_types.event.Event`, créant une incompatibilité avec `kernel.py`.

**Action :**
1. Migrer `core/events/__init__.py` pour importer de `core.bus.memory_bus`
2. Mettre à jour les tests (`tests/test_core/test_bus.py`, `tests/test_core/test_agents.py`)
3. Supprimer `core/bus/nats.py` et `core/bus/memory.py`
4. Corriger `nats_bus.py` pour utiliser `core.ethan_types.event.Event`

---

## 3. Duplication State (core/state/)

| Fichier | Type | Statut |
|---------|------|--------|
| `core/state/state.py` | OLD — `StateManager` monolithique, URLs en dur | **Mort** (non importé) |
| `core/state/manager.go` | Go | **Mort** |
| `core/state/interface.py` | NEW — `StateBackend` ABC | Actif |
| `core/state/redis_state.py` | NEW — Redis live state | Actif |
| `core/state/postgres_state.py` | NEW — PostgreSQL persistent state | Actif |
| `core/state/composite_backend.py` | NEW — Composite (Redis + PG) | Actif |
| `core/state/memory_backend.py` | NEW — Memory backend | Actif |

**Action :** Supprimer `core/state/state.py` et `core/state/manager.go`.

---

## 4. Duplication WebUI

| Chemin | Description | Statut |
|--------|-------------|--------|
| `webui/` (racine) | Ancienne version avec `legacy/` (app.py, api_client.py, config.py) | **Obsolète** |
| `interfaces/webui/` | Nouvelle version (Next.js, auth, dashboard) | **Actif** |

docker-compose.yml utilise `deploy/Dockerfile.ui` → `interfaces/webui/`.

**Action :** Supprimer `webui/` à la racine.

---

## 5. Duplication CLI (interfaces/cli/)

### 5.1 colors.py dupliqué
- `interfaces/cli/core/colors.py` — Système de couleurs complet
- `interfaces/cli/ui/colors.py` — Helpers de style basiques

### 5.2 Trois fichiers de commande plugin
- `interfaces/cli/commands/plugin.py` — `ethan plugin <install|remove|list>`
- `interfaces/cli/commands/plugin_cmd.py` — `ethan plugin <validate|list|info>`
- `interfaces/cli/commands/plugins.py` — `ethan plugins` (liste)

**Action :** Unifier `colors.py` et consolider les 3 fichiers plugin en un seul.

---

## 6. Duplication Infrastructure

### 6.1 deploy/ vs infrastructure/docker/
| Chemin | Contenu | Statut |
|--------|---------|--------|
| `deploy/` | Dockerfiles, nats/, postgres/ | **Actif** (docker-compose.yml) |
| `infrastructure/docker/` | cli/, core/, plugins/, runtime/ | **Inutilisé** |

### 6.2 infrastructure/config/ vs infrastructure/configs/
- `infrastructure/config/` — `core.yaml`, `plugins.yaml`, `runtime.yaml` — Actif
- `infrastructure/configs/` — **Vide** — **Mort**

### 6.3 docker-compose multiples
- `docker-compose.yml` — Principal (actif)
- `docker-compose.dev.yml` — Patch dev (vide pour `build:`)
- `docker-compose.prod.yml` — Patch prod (vide pour `build:`)
- `docker-compose.cluster.yml` — Patch cluster NATS 3 nœuds
- `docker-compose.observability.yml` — Observabilité
- `core/deployment/docker/docker-compose*.yml` — Anciens fichiers

**Action :** Supprimer `infrastructure/configs/` (vide). Consolider `infrastructure/docker/`.

---

## 7. core/events/ — Module de rétrocompatibilité

`core/events/__init__.py` est un **shim** qui :
- Importe depuis `core.bus.memory` (l'ANCIEN bus) au lieu de `core.bus.memory_bus` (le NOUVEAU)
- Définit sa propre classe `EventHandler` (ABC) et `EventBus` (wrapper)
- Crée une instance globale `bus = EventBus()`

**Action :** Mettre à jour pour importer de `core.bus.memory_bus`, puis supprimer le shim.

---

## 8. core/bootstrap.py vs core/bootstrap/

| Chemin | Description |
|--------|-------------|
| `core/bootstrap.py` | Point d'entrée (201 lignes, `main()` async) |
| `core/bootstrap/` | Package : `bootstrapper.py`, `integrity.py`, `repair.py`, `config_evolution.py` |

**Problème :** Cohabitation d'un fichier et d'un package du même nom. Fonctionnellement correct mais confus.

**Action :** Renommer `core/bootstrap.py` → `core/runtime.py` ou déplacer dans `core/bootstrap/__main__.py`.

---

## 9. core/orchestrator/ — Ancienne architecture cognitive

| Fichier | Description |
|---------|-------------|
| `cognitive_loop.py` | Boucle cognitive |
| `executor.py` | Exécuteur de tâches |
| `orchestrator.py` | Orchestrateur |
| `registry.py` | Registre de capacités |
| `observer.py` | Observateur |
| `planner.py` | Planificateur |
| `pipeline.py` | Pipeline |

**Utilisé uniquement par :** `tests/core/test_cognitive_loop.py`, `tests/core/test_pipeline.py`

**Action :** Consolider avec `core/kernel.py` + `core/modules/`.

---

## 10. core/executor/ — Code mort

| Fichier | Statut |
|---------|--------|
| `core/executor/__init__.py` | Importe de `executor.py` |
| `core/executor/executor.py` | **Non importé** |
| `core/executor/executor.go` | Go mort |
| `core/executor/retry.go` | Go mort |

**Action :** Supprimer le répertoire `core/executor/` entier.

---

## 11. Répertoires "presque vides" (Go mort seulement)

| Répertoire | Contenu | Action |
|------------|---------|--------|
| `core/ingest/` | `ingest.go` seulement | Supprimer |
| `core/intent/` | `intent.go` seulement | Supprimer |
| `core/resolver/` | `resolver.go` seulement | Supprimer |
| `core/router/` | `router.go` seulement | Supprimer |
| `core/service/` | `service.go` seulement | Supprimer |
| `core/response/` | `builder.go` seulement | Supprimer |

---

## 12. Redondance skills vs tools

| Fonctionnalité | `core/skills/` | `core/tools/` |
|----------------|----------------|---------------|
| Executor | `executor.py` (`SkillExecutor`) | `executor.py` (`ToolExecutor`) |
| Manager | `manager.py` | `manager.py` |
| Registry | `registry.py` | `registry.py` |
| Selector | `selector.py` | `selector.py` |
| Types | `types.py` | `types.py` |
| Composer | `composer.py` | — |
| Lab | `lab.py` | — |
| Monitor | — | `monitor.py` |
| Pearl Oracle | — | `pearl-reference-oracle/` |

**Action :** Unifier en `core/skills/`. Un skill est un tool spécialisé.

---

## 13. Redondance planner vs cognition/planner

| Chemin | Contenu |
|--------|---------|
| `core/planner/` | `planner.py`, `decomposer.py`, `dag.py`, `optimizer.py`, `checkpoint.py`, `goal_manager.py`, `types.py` |
| `core/cognition/planner/` | `decomposer.py`, `__init__.py` (incomplet) |

**Action :** Supprimer `core/cognition/planner/` et garder `core/planner/`.

---

## 14. Redondance registry vs modules

| Chemin | Contenu |
|--------|---------|
| `core/registry/` | `module.py` (`ModuleRegistry`), `capability.py`, `events.py`, `registry.py` |
| `core/modules/` | `base.py` (`Module`, `Agent`), `interface.py`, `capability.py`, `dependency.py`, `permissions.py` |

**Action :** Garder la séparation (registre → entités) mais clarifier les responsabilités.

---

## 15. core/providers/ — Redondance potentielle

| Chemin | Contenu |
|--------|---------|
| `core/providers/` | `__init__.py`, `providers/` (`anthropic.py`, `openai.py`, `ollama.py`) |
| `core/llm/providers/` | Existe aussi |

**Action :** Vérifier si `core/providers/` est utilisé ou si c'est un doublon de `core/llm/providers/`.

---

## 16. core/deployment/ — Anciens scripts

| Contenu | Description |
|---------|-------------|
| `docker/` | `docker-compose*.yml`, `Dockerfile*`, `nginx.conf` (anciens) |
| `scripts/` | Scripts de déploiement |
| `xfce/` | Configuration XFCE (desktop) |

**Action :** Vérifier si utilisé. Si non, supprimer ou déplacer vers `infrastructure/`.

---

## 17. core/workflow/ — Vide

**Action :** Supprimer (répertoire vide).

---

## 18. plugins/ — Duplications

| Chemin | Contenu | Statut |
|--------|---------|--------|
| `plugins/sandbox.py` | Module Python | Actif |
| `plugins/sandbox/` | Package (`__init__.py`, `runtime.py`) | Actif |
| `plugins/registry/` | **Vide** | **Mort** |
| `plugins/store/` | **Vide** | **Mort** |
| `plugins/sdk/` | `base.py` | Actif |
| `plugins/builtin/` | `browser/`, `security/`, `twitter/` | Actif |

**Action :** Unifier `sandbox.py` et `sandbox/`. Supprimer `registry/` et `store/` (vides).

---

## 19. interfaces/ — Répertoires vides

| Chemin | Contenu | Statut |
|--------|---------|--------|
| `interfaces/mcp/` | **Vide** | **Mort** |

**Action :** Supprimer `interfaces/mcp/`.

---

## 20. core/context/ — Presque vide

| Chemin | Contenu |
|--------|---------|
| `core/context/` | `intent.py` seulement |

**Action :** Garder (fonctionnel) mais vérifier si utilisé.

---

## 21. core/security/ — Incomplet

| Contenu | Description |
|---------|-------------|
| `gateway.py` | Gateway de sécurité |
| `types.py` | Types de sécurité |
| `validation/` | Validation |

**Action :** Vérifier si utilisé. Compléter ou marquer comme deprecated.

---

## 22. core/cost/ — Isolé

| Contenu | Description |
|---------|-------------|
| `budget.py` | Gestion de budget |
| `tracker.py` | Suivi des coûts |
| `types.py` | Types |
| `__init__.py` | Exportations |

**Action :** Vérifier si utilisé par le kernel. Marquer comme deprecated si non.

---

## 23. Modules Actifs (pas de suppression)

Ces modules sont actifs et utilisés par le kernel ou d'autres modules :

| Module | Utilisé par |
|--------|-------------|
| `core/facts/` | Ingestion et récupération de faits |
| `core/goals/` | `core/kernel.py` (GoalManager) |
| `core/llm/` | Gestion LLM (client, manager, registry, router, selector) |
| `core/memory/` | Gestion mémoire (Redis, PG, ChromaDB, Qdrant) |
| `core/metacognition/` | `core/bootstrap.py` |
| `core/scheduler/` | `core/kernel.py` (Scheduler) |
| `core/telemetry/` | `core/bootstrap.py` (setup_logging) |
| `core/modules/` | `core/kernel.py`, `core/registry/` |
| `core/registry/` | `core/kernel.py` (ModuleRegistry) |
| `core/cognition/` | Architecture cognitive (reasoner, intention, planner) |
| `core/autonomy/` | `core/bootstrap.py` (AutonomyLoopController) |
| `core/learning/` | `core/bootstrap.py` (LearningEngine) |
| `core/safety/` | Circuit breaker |
| `core/config/` | Configuration (loader, schema, secrets) |
| `core/ethan_types/` | Types partagés (event, goal, module, etc.) |
| `core/bus/` | Bus d'événements (interface, backends) |
| `core/state/` | State backend (interface, redis, postgres, composite) |
| `core/approval/` | Système d'approbation |
| `core/audit/` | Audit trail |
| `core/auth/` | Authentification |
| `core/capabilities/` | Capacités LLM/mémoire |
| `core/executive/` | Exécutif (goal_manager) |
| `core/ingest/` | (Go mort, voir section 1) |
| `core/llm/providers/` | Fournisseurs LLM |
| `core/metrics/` | Healthcheck, logging, telemetry | |

---

## 24. Structure du projet — Hors cible

La structure actuelle ne correspond pas à l'architecture cible `core/ | runtime/ | plugins/ | interfaces/ | infrastructure/`.

| Répertoire | Devrait être | Raison |
|------------|-------------|--------|
| `deploy/` | `infrastructure/docker/` | Dockerfiles de déploiement |
| `scripts/` | `core/scripts/` ou `infrastructure/scripts/` | Scripts shell |
| `install/` | `infrastructure/scripts/` | Scripts d'installation |
| `sdk/` | `core/sdk/` ou `plugins/sdk/` | SDK |
| `examples/` | `docs/examples/` | Exemples |
| `engineering/` | `docs/engineering/` | Docs techniques |
| `ethan` | `scripts/ethan` | Script de lancement |
| `pyproject.toml` | Racine | Garder |
| `Makefile` | Racine | Garder |
| `docker-compose*.yml` | Racine | Garder |
| `tests/` | Racine | Garder |
| `docs/` | Racine | Garder |

**Action :** Planifier un déplacement progressif. Priorité : `deploy/` → `infrastructure/docker/`.

---

## Plan de Nettoyage Priorisé

### Phase 1 — Nettoyage immédiat (faible risque)
1. Supprimer tous les fichiers `.go` morts (section 1, 10, 11)
2. Supprimer `core/state/state.py` (section 3)
3. Supprimer `webui/` à la racine (section 4)
4. Supprimer `infrastructure/configs/` (section 6)
5. Supprimer `core/workflow/` (section 17)
6. Supprimer `plugins/registry/` et `plugins/store/` (section 18)
7. Supprimer `interfaces/mcp/` (section 19)

### Phase 2 — Résolution de duplications (risque modéré)
1. Unifier `core/bus/nats.py` + `nats_bus.py` → garder `nats_bus.py`, corriger l'Event type
2. Unifier `core/bus/memory.py` + `memory_bus.py` → garder `memory_bus.py`
3. Migrer `core/events/__init__.py` vers `core.bus.memory_bus`
4. Unifier `core/skills/` + `core/tools/` → garder `core/skills/`
5. Unifier `interfaces/cli/core/colors.py` + `interfaces/cli/ui/colors.py`
6. Consolider `interfaces/cli/commands/plugin.py` + `plugin_cmd.py` + `plugins.py`
7. Supprimer `core/cognition/planner/` (section 13)
8. Unifier `plugins/sandbox.py` + `plugins/sandbox/` (section 18)

### Phase 3 — Restructuration (risque élevé)
1. Renommer `core/bootstrap.py` → `core/runtime.py` (section 8)
2. Déplacer `deploy/` → `infrastructure/docker/` (section 24)
3. Déplacer `scripts/` → `infrastructure/scripts/` (section 24)
4. Déplacer `install/` → `infrastructure/scripts/` (section 24)
5. Déplacer `sdk/` → `core/sdk/` (section 24)
6. Déplacer `examples/` → `docs/examples/` (section 24)
7. Déplacer `engineering/` → `docs/engineering/` (section 24)
8. Consolider `core/orchestrator/` avec `core/kernel.py` (section 9)

### Phase 4 — Vérifications
1. Vérifier `core/providers/` vs `core/llm/providers/` (section 15)
2. Vérifier `core/deployment/` (section 16)
3. Vérifier `core/security/` (section 21)
4. Vérifier `core/cost/` (section 22)
5. Vérifier `core/context/intent.py` (section 20)
