# Audit d'Architecture ETHAN — Rapport Complet

> **Type** : Audit d'architecture  
> **Auteur** : Principal Software Architect  
> **Date** : 2026-07-19  
> **Version** : 1.0  
> **Statut** : Confidentiel

---

## Table des matières

1. [Vue d'ensemble du projet](#1-vue-densemble-du-projet)
2. [Organisation des dossiers](#2-organisation-des-dossiers)
3. [Cartographie des dépendances](#3-cartographie-des-dépendances)
4. [Architecture actuelle](#4-architecture-actuelle)
5. [Points forts](#5-points-forts)
6. [Faiblesses](#6-faiblesses)
7. [Dette technique](#7-dette-technique)
8. [Risques](#8-risques)
9. [Recommandations](#9-recommandations)

---

## 1. Vue d'ensemble du projet

### 1.1 Nature du projet

ETHAN est un **Cognitive Operating System Runtime** distribué, event-driven, avec les caractéristiques suivantes :

- **Type** : Daemon permanent + interfaces
- **Architecture** : Microservices orchestrés par Docker Compose
- **Communication** : NATS JetStream (event bus)
- **Persistence** : PostgreSQL (long-term) + Redis (short-term)
- **Modularité** : Modules indépendants, capacité-based
- **Isolation** : Core kernel isolé des interfaces

### 1.2 Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Core Kernel | Go + Python | Go 1.24+, Python 3.10-3.13 |
| Event Bus | NATS JetStream | 2.10+ |
| Cache/Runtime | Redis | 7+ |
| Persistence | PostgreSQL | 16+ |
| API Gateway | FastAPI + Uvicorn | 0.110+, 0.30+ |
| WebUI | Next.js | Latest |
| CLI | Python (Click) | 8+ |
| Build | Hatchling + maturin | Latest |
| Linting | Ruff | 0.4+ |
| Testing | Pytest 8+ | Async support |

---

## 2. Organisation des dossiers

### 2.1 Structure globale

```
Ethan/
├── core/                    # ✅ Kernel central (Go + Python)
│   ├── agents/              # Agents cognitifs
│   ├── api/                 # Contrats gRPC + Python API
│   ├── bootstrap/           # Démarrage système
│   ├── bus/                 # EventBus (ABC + NATS + Memory)
│   ├── capabilities/        # Définition des capabilities
│   ├── cognition/           # Module cognition
│   ├── config/              # Configuration injectée
│   ├── context/             # Gestion de contexte
│   ├── cost/                # Budget et coûts LLM
│   ├── events/              # Types d'événements
│   ├── executive/           # Module executive
│   ├── executor/            # Exécuteur de tâches
│   ├── goals/               # Gestion des buts
│   ├── ingest/              # Ingestion d'événements
│   ├── intent/              # Analyse d'intention
│   ├── learning/            # Module learning
│   ├── llm/                 # LLM Router + Providers
│   ├── metacognition/       # Module métacognition
│   ├── modules/             # Interface Module (ABC)
│   ├── orchestrator/        # Orchestrator Python
│   ├── planner/             # Module planner
│   ├── providers/           # Providers (LLM, Tools, etc.)
│   ├── registry/            # Registres (modules, capabilities)
│   ├── resolver/            # Résolveur de capabilities
│   ├── response/            # Formattage réponses
│   ├── router/              # Routeur d'événements
│   ├── scheduler/           # Planificateur
│   ├── security/            # Security gateway
│   ├── state/               # StateBackend (ABC + Redis + PG)
│   ├── telemetry/           # Télémétrie
│   ├── tools/               # Gestion d'outils
│   └── types/                # Types purs (Event, Goal, Plan)
│
├── interfaces/              # ✅ Interfaces (thin clients)
│   ├── api/                 # API Gateway (FastAPI)
│   ├── channels/            # Channels (Telegram, Discord, etc.)
│   ├── cli/                 # CLI Python
│   ├── desktop/             # Desktop (Electron/Tauri)
│   ├── mcp/                 # Model Context Protocol
│   ├── shell/               # Shell completion
│   └── webui/               # WebUI (Next.js)
│
├── plugins/                 # ✅ Plugins système
│   ├── browser/             # Plugin navigateur
│   ├── builtin/             # Plugins intégrés
│   ├── memory/              # Plugin mémoire
│   ├── registry/            # Registry plugins
│   ├── sandbox/             # Sandbox sécurité
│   ├── sdk/                 # SDK plugins
│   ├── store/               # Store plugins
│   └── terminal/            # Plugin terminal
│
├── sdk/                     # ✅ SDK public
│   ├── autonomy.py
│   ├── event.py
│   ├── goals.py
│   ├── learning.py
│   ├── metacognition.py
│   ├── module.py
│   ├── python/              # SDK Python
│   └── typescript/          # SDK TypeScript
│
├── runtime/                 # ⚠️ Runtime Go (séparé)
│   ├── cmd/
│   ├── compose/
│   ├── config/
│   ├── internal/
│   └── tests/
│
├── rust/                    # ⚠️ Crates Rust (séparé)
│   ├── crates/
│   ├── Cargo.toml
│   └── rust-toolchain.toml
│
├── deploy/                  # ✅ Dockerfiles + configs
│   ├── Dockerfile.api
│   ├── Dockerfile.kernel
│   ├── Dockerfile.module
│   ├── Dockerfile.ui
│   ├── Dockerfile.python-base
│   └── postgres/
│
├── infrastructure/          # ✅ Infrastructure
│   ├── config/
│   ├── docker/
│   ├── grafana/
│   ├── kubernetes/
│   ├── launchd/
│   ├── postgres/
│   ├── prometheus/
│   ├── scripts/
│   ├── shell/
│   ├── systemd/
│   └── traefik/
│
├── scripts/                 # ✅ Scripts launcher
│   ├── cmd-*.sh
│   ├── ethan-lib.sh
│   └── install/
│
├── docs/                    # ✅ Documentation
│   ├── architecture/
│   ├── development/
│   ├── getting-started/
│   └── user-guide/
│
├── engineering/             # ✅ RFC, ADR, templates
│   ├── adr/
│   ├── architecture/
│   ├── reports/
│   ├── rfc/
│   └── standards/
│
├── examples/                # ⚠️ Exemples (mixés)
│   ├── browser_assistant/
│   ├── code_companion/
│   ├── daily_digest/
│   ├── deep_research/
│   ├── doc_qa/
│   ├── messaging_hub/
│   ├── multi_model_router/
│   ├── openjarvis/          # ⚠️ Ancien projet ?
│   ├── scheduled_ops/
│   ├── security_scanner/
│   └── twitter_bot/
│
├── tests/                   # ⚠️ Tests globaux
│
├── proto/                   # ✅ Protobuf definitions
│   └── ethan/
│
├── jarvis-OS/               # ⚠️ Dossier suspect
│
├── .agents/                 # ⚠️ Dossier caché
│
├── ethan                    # ✅ Launcher principal
├── pyproject.toml           # ✅ Packaging Python
├── docker-compose.yml       # ✅ Docker Compose principal
├── docker-compose.dev.yml   # ✅ Docker Compose dev
├── docker-compose.prod.yml  # ✅ Docker Compose prod
├── Makefile                 # ✅ Build automation
└── README.md                # ✅ Documentation principale
```

---

## 3. Cartographie des dépendances

### 3.1 Dépendances par couche (théoriques)

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACES (Thin Clients)                 │
│  api/  cli/  webui/  desktop/  shell/  channels/  mcp/      │
│                                                             │
│  Dépendances : core (API Python) + SDK                      │
│  Ne dépend PAS : plugins, interfaces/, legacy               │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ NATS / HTTP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CORE (Kernel Isolé)                       │
│                                                             │
│  core/ : kernel, bus, registry, state, modules, types      │
│                                                             │
│  Dépendances : SDK + providers + plugins (via registry)    │
│  Ne dépend PAS : interfaces/, legacy, cli/                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Event Bus (NATS)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      PLUGINS (Indépendants)                  │
│                                                             │
│  plugins/ : browser, builtin, memory, registry, sandbox,   │
│             sdk, store, terminal                            │
│                                                             │
│  Dépendances : SDK + interfaces (via registry)             │
│  Communication : NATS uniquement                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP / WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE                            │
│                                                             │
│  deploy/  infrastructure/  scripts/  docker-compose.*.yml  │
│                                                             │
│  Dépendances : core + interfaces + plugins                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Dépendances réelles observées

#### Core → SDK

```python
# core/kernel.py
from sdk.event import EventType  # ✅ Attendu

# core/main.py
from sdk.module import ModuleSDK  # ✅ Attendu
```

**Status** : ✅ Conforme à l'architecture

#### Core → Plugins (via registry)

```python
# core/registry/module_registry.py
from plugins.registry import PluginRegistry  # ✅ Attendu
```

**Status** : ✅ Conforme, mais nécessite validation

#### Interfaces → Core

```python
# interfaces/api/main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.routers import message as message_router
from api.routers import state as state_router
```

**Status** : ⚠️ Utilise `sys.path` hacking (contredit le principe d'isolation)

#### Launcher → Tous

```bash
# ethan (ligne 9-10)
export ETHAN_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"
```

**Status** : ✅ Solution pragmatique pour le développement

---

## 4. Architecture actuelle

### 4.1 Points forts

#### ✅ Isolation du Core

- Core n'importe pas `cli/`, `interfaces/`, `plugins/` directement
- Pas de `os.getenv()` dans core (configuration injectée)
- Pas de `sys.path` hacking dans core/bootstrap.py (utilise `insert` uniquement pour le bootstrap)
- Pas de `signal` handling dans core
- Pas de `print()` / `input()` dans core

#### ✅ Modularité

- Modules indépendants avec interfaces claires (ABC)
- Communication event-driven via NATS
- Plugins system avec sandbox
- SDK public bien défini

#### ✅ Documentation

- README.md exhaustif
- ARCHITECTURE.md détaillé
- Documentation par couche
- schémas d'architecture

#### ✅ Tooling

- Ruff pour linting
- Pytest pour tests
- Maturin pour build Rust
- Hatchling pour packaging Python
- Pre-commit hooks
- Docker Compose pour orchestration

#### ✅ Observabilité

- Logging structuré
- Télémétrie intégrée
- Healthchecks Docker
- Systemd service avec journald

### 4.2 Faiblesses

#### ❌ Désalignement Documentation vs Réalité

**README.md ligne 5-8 :**
```
core — Cerveau. Zéro UI. Zéro IO direct. Zéro dépendance OS/CLI.
cli — Terminal UI. Zéro logique cognitive. Client gRPC uniquement.
plugins — Extensions. Process indépendants. Connectés via NATS.
interfaces — Ponts vers le monde extérieur.
```

**Réalité observée :**
- Core expose une API Python (`core.kernel.CognitiveKernel`), pas gRPC
- CLI n'utilise pas gRPC, mais des événements NATS + états Redis
- Core utilise NATS directement (pas seulement gRPC)
- `core/kernel.py` fait des imports de `core.bus`, `core.registry`, etc. (couplage fort interne)

#### ❌ Double implementation Kernel

```
core/main.go      # Entrypoint Go (théorique)
core/main.py      # Entrypoint Python (réel)
core/bootstrap.py # Bootstrap Python (utilisé par Docker)
core/kernel.py    # Kernel Python (CognitiveKernel)
```

**Problème :** Aucun lien évident entre `core/main.go` et les fichiers Python. Le kernel Go mentionné dans le README n'existe pas ou n'est pas utilisé.

#### ❌ Dépendances implicites

**interfaces/api/main.py ligne 13 :**
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**Problème :** Contredit le principe d'isolation du core.

#### ❌ Dossiers vides ou morts

- `core/__pycache__/` — présent dans le repo (ne devrait pas)
- `core/agents/` — vide
- `core/pkg/` — vide
- `sdk/__pycache__/` — présent
- `plugins/__pycache__/` — présent

#### ❌ Incohérences de nommage

- `core/orchestration/` vs `core/orchestrator/` — deux dossiers
- `core/registry/module.py` vs `core/registry/module_registry.py` — doublon ?
- `core/state/interface.py` vs `core/state/redis_state.py` — pattern OK mais nom confus

#### ❌ Composants orphelins

- `runtime/` — Go runtime séparé, pas de lien évident avec `core/`
- `rust/` — Crates Rust (whisper, etc.), isolé
- `jarvis-OS/` — dossier à la racine, nature inconnue
- `examples/openjarvis/` — ancien projet intégré ?

#### ❌ Scripts incohérents

- `install/doctor.sh` — existe mais n'est pas appelé par `./ethan doctor`
- `install/repair.sh` — existe mais n'est pas appelé par `./ethan`
- Les scripts `scripts/cmd-*.sh` utilisent tous `ethan-lib.sh` excepté `cmd-doctor.sh`

#### ❌ Healthchecks incorrects

**docker-compose.yml ligne 135 :**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]
```

**Réalité :** L'endpoint est `/health` (pas `/v1/health`), causant des échecs de healthcheck.

---

## 5. Cartographie des dépendances

### 5.1 Dépendances Core

```
core/
├── agents/          → core.types, core.events, core.bus
├── api/             → core.types, core.events, core.bus
├── approval/        → core.types, core.events, core.security
├── audit/           → core.types, core.events, core.bus
├── auth/            → core.types, core.events
├── autonomy/        → core.types, core.events, core.bus, core.llm
├── bootstrap/       → core.types, core.events, core.bus
├── bus/             → core.types, core.events (pas de dépendances externes)
├── capabilities/    → core.types, core.events
├── cmd/             → core.types, core.bus
├── cognition/       → core.types, core.events, core.bus, core.llm, core.memory
├── config/          → core.types (pur)
├── context/         → core.types, core.state
├── cost/            → core.types, core.events
├── deployment/      → core.types
├── events/          → core.types (pur)
├── executive/       → core.types, core.events, core.bus, core.goals
├── executor/        → core.types, core.events, core.bus
├── facts/           → core.types, core.events, core.bus
├── gateway/         → core.types, core.bus
├── goals/           → core.types, core.events, core.bus, core.state
├── ingest/          → core.types, core.events, core.bus
├── intent/          → core.types, core.events
├── learning/        → core.types, core.events, core.bus, core.state
├── llm/             → core.types, core.events, sdk (⚠️)
├── memory/          → core.types, core.events, core.bus, core.state
├── metacognition/   → core.types, core.events, core.bus
├── metrics/         → core.types
├── modules/         → core.types, core.events (ABC)
├── orchestration/   → ⚠️ DOUBLON avec orchestrator/
├── orchestrator/    → core.types, core.events, core.bus
├── planner/         → core.types, core.events, core.bus, core.capabilities
├── providers/       → core.types (interfaces)
├── registry/        → core.types, core.events
├── resolver/        → core.types, core.capabilities
├── response/        → core.types
├── router/          → core.types, core.events, core.bus
├── safety/          → core.types, core.events
├── scheduler/       → core.types, core.events, core.bus
├── security/        → core.types, core.events
├── service/         → core.types
├── skills/          → core.types, core.tools
├── state/           → core.types (ABC + implémentations)
├── telemetry/       → core.types, core.events
├── tools/           → core.types, core.events, core.security
└── types/            # PUR (pas de dépendances)
```

### 5.2 Dépendances Interfaces

```
interfaces/
├── api/             → core (via sys.path), nats, fastapi, sdk
├── channels/        → sdk, interfaces.api
├── cli/             → sdk, interfaces.api
├── desktop/         → sdk, interfaces.api
├── mcp/             → sdk, interfaces.api
├── shell/           → sdk
└── webui/           # Frontend isolé (HTTP vers API)
```

### 5.3 Dépendances Plugins

```
plugins/
├── browser/         → sdk, plugins.sdk
├── builtin/         → sdk, plugins.sdk
├── memory/          → sdk, plugins.sdk
├── registry/        → sdk, plugins.sdk
├── sandbox/         → sdk, plugins.sdk
├── sdk/             → sdk (autoref)
├── store/           → sdk, plugins.sdk
└── terminal/        → sdk, plugins.sdk
```

### 5.4 Dépendances SDK

```
sdk/
├── autonomy.py      → event.py (internal)
├── event.py         # PUR
├── goals.py         → event.py (internal)
├── learning.py      → event.py (internal)
├── metacognition.py → event.py (internal)
├── module.py        → event.py (internal)
└── python/          → Top-level SDK Python
```

---

## 6. Dette technique

### 6.1 Code mort

| Composant | Localisation | Raison |
|-----------|-------------|--------|
| `core/main.go` | core/main.go | Entrypoint Go jamais utilisé (Python utilisé à la place) |
| `core/go.mod` | core/go.mod | Module Go inutilisé |
| `runtime/` | runtime/ | Runtime Go séparé, aucun lien visible |
| `rust/` | rust/ | Crates Rust (peut-être utilisées par des plugins) |
| `jarvis-OS/` | racine | Dossier suspect, possibly legacy |
| `core/agents/` | core/agents/ | Dossier vide |
| `core/pkg/` | core/pkg/ | Dossier vide |
| `__pycache__/` | multiples | Devrait être dans .gitignore seulement |
| `examples/openjarvis/` | examples/ | Ancien projet intégré ? |

### 6.2 Doublons

- `core/orchestration/` et `core/orchestrator/` — deux dossiers avec des rôles similaires
- `core/registry/module.py` et `core/registry/module_registry.py` — possible doublon
- `install/doctor.sh` et `scripts/cmd-doctor.sh` — deux implémentations
- `core/state/interface.py` — interface abstraite, mais nom confus avec `core/state/redis_state.py`

### 6.3 Incohérences

- README.md promet gRPC mais l'API est HTTP (FastAPI)
- README.md promet `core.main:main` mais utilise `core.bootstrap:main`
- Healthchecks Docker utilisent `/v1/health` au lieu de `/health`
- `core/kernel.py` utilise des imports absolus (`from core.X import Y`) au lieu d'absolus depuis la racine
- `interfaces/api/main.py` utilise `sys.path.insert()` pour importer `core`

### 6.4 Dette de conception

- **Couplage core ↔ sdk** : Core importe SDK directement, violating the principle "SDK dépend de Core, pas l'inverse"
- **Absence de tests** : `core/tests/` existe mais semble vide ou minimal
- **Dualité Python/Go** : Core a des fichiers `.go` et `.py`, unclear which is canonical
- **Configuration dispersée** : `core/config/` existe mais de nombreux fichiers utilisent `os.getenv()` directly

---

## 7. Risques

### 7.1 Risques architecturaux

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Dépendance circulaire core ↔ sdk | Élevée | Élevé | Clarifier les boundaries |
| Dualité Go/Python dans core | Moyenne | Élevé | Choisir un langage dominant |
| Dossiers vides en production | Faible | Faible | Nettoyement |
| Incohérence README vs réalité | Élevée | Moyen | Mettre à jour la doc |
| sys.path hacking dans interfaces | Moyenne | Moyen | Utiliser un package installé |

### 7.2 Risques opérationnels

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Healthchecks incorrects | Élevée | Élevé | Corriger les endpoints |
| Timeout healthchecks (90s) | Moyenne | Moyen | Documenter, ajuster si besoin |
| PYTHONPATH requis | Élevée | Élevé | Launcher corrige le problème |
| Containers non-ready au boot | Élevée | Élevé | Attente healthchecks ajoutée |

---

## 8. Recommandations

### 8.1 Court terme (1-2 semaines)

1. **Corriger la documentation**
   - Mettre à jour README.md pour refléter la réalité (HTTP + NATS, pas gRPC)
   - Clarifier le rôle de `core/main.go` vs `core/bootstrap.py`

2. **Corriger les healthchecks**
   - ✅ Fait: `/v1/health` → `/health`
   - Vérifier tous les endpoints

3. **Nettoyement mineur**
   - Supprimer `__pycache__/` du repo
   - Supprimer les dossiers vides (`core/agents/`, `core/pkg/`)

### 8.2 Moyen terme (1-2 mois)

1. **Clarifier la dualité Go/Python**
   - Décider si Core est en Go ou Python
   - Si Go : décommissionner `core/kernel.py`, `core/bootstrap.py`
   - Si Python : supprimer `core/main.go`, `core/go.mod`

2. **Éliminer les doublons**
   - Fusionner `core/orchestration/` et `core/orchestrator/`
   - Unifier `core/registry/module.py` et `module_registry.py`

3. **Améliorer les imports**
   - Installer le package en mode éditable (`pip install -e .`)
   - Supprimer `sys.path.insert()` dans `interfaces/api/main.py`
   - Le launcher `ethan` gère déjà `PYTHONPATH`

### 8.3 Long terme (3-6 mois)

1. **Architectural decisions**
   - Décider du sort de `runtime/` (Go) et `rust/`
   - Décider du sort de `jarvis-OS/`
   - Clarifier la relation entre ETHAN et OpenJarvis

2. **Testing**
   - Ajouter des tests d'intégration
   - Tests de healthchecks automatisés
   - CI/CD avec vérification des imports

3. **Observabilité**
   - Ajouter des métriques Prometheus
   - Ajouter des traces OpenTelemetry
   - Dashboard Grafana pour les services

---

## 9. Cartographie des dépendances (visuelle)

```
┌──────────────────────────────────────────────────────────────┐
│                        ETHAN Stack                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │  interfaces/ │      │   plugins/   │      │   sdk/    │ │
│  │              │      │              │      │           │ │
│  │  api/        │      │  browser/    │      │ autonomy  │ │
│  │  cli/        │      │  builtin/    │      │ event     │ │
│  │  webui/      │      │  memory/     │      │ goals     │ │
│  │  desktop/    │      │  registry/   │      │ learning  │ │
│  │  shell/      │      │  sandbox/    │      │ module    │ │
│  │  mcp/        │      │  sdk/        │      │ goals     │ │
│  │              │      │  store/      │      │ meta      │ │
│  │  Dépendent:  │      │  terminal/   │      │           │ │
│  │  - core      │      │              │      │ PUR       │ │
│  │  - sdk       │      │  Dépendent:  │      │           │ │
│  │              │      │  - sdk       │      └───────────┘ │
│  └──────┬───────┘      └──────┬───────┘                  │
│         │                     │                           │
│         │    ┌────────────────▼───────────┐               │
│         │    │                            │               │
│         │    │         core/              │               │
│         │    │                            │               │
│         │    │  kernel.py (Python)        │               │
│         │    │  bootstrap.py              │               │
│         │    │  main.py                   │               │
│         │    │                            │               │
│         │    │  Dépend de:                │               │
│         │    │  - sdk/                    │               │
│         │    │  - nats (NATS)             │               │
│         │    │  - redis (Redis)           │               │
│         │    │  - postgres (PostgreSQL)   │               │
│         │    │                            │               │
│         │    │  Dépendances internes:     │               │
│         │    │  - bus/                    │               │
│         │    │  - registry/               │               │
│         │    │  - state/                  │               │
│         │    │  - modules/                │               │
│         │    │  - types/                  │               │
│         │    │  - cognition/              │               │
│         │    │  - memory/                 │               │
│         │    │  - planner/                │               │
│         │    │  - executive/              │               │
│         │    │  - learning/               │               │
│         │    │  - metacognition/          │               │
│         │    │  - autonomy/               │               │
│         │    │  - goals/                  │               │
│         │    │  - security/               │               │
│         │    │  - scheduler/              │               │
│         │    │  - tools/                  │               │
│         │    │  - llm/                    │               │
│         │    │  - providers/              │               │
│         │    │                            │               │
│         │    └────────────────────────────┘               │
│         │                                                  │
│         │    ┌────────────────▼───────────┐               │
│         │    │                            │               │
│         │    │      Infrastructure         │               │
│         │    │                            │               │
│         │    │  deploy/                    │               │
│         │    │  infrastructure/            │               │
│         │    │  scripts/                   │               │
│         │    │  docker-compose*.yml        │               │
│         │    │                            │               │
│         │    │  Dépend de:                 │               │
│         │    │  - core/                    │               │
│         │    │  - interfaces/              │               │
│         │    │  - plugins/                 │               │
│         │    │                            │               │
│         │    └────────────────────────────┘               │
│         │                                                  │
└─────────┼──────────────────────────────────────────────────┘
          │
          │
┌─────────▼──────────────────────────────────────────────────┐
│                                                              │
│  ⚠️  Composants orphelins / legacy:                         │
│                                                              │
│  - runtime/       : Go runtime séparé, pas de lien          │
│  - rust/          : Crates Rust isolées                     │
│  - jarvis-OS/     : Legacy ?                                 │
│  - examples/      : Mix de prototypes et legacy             │
│  - core/main.go   : Entrypoint Go inutilisé                 │
│  - core/go.mod    : Module Go inutilisé                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 10. Conclusion

ETHAN présente une **architecture théoriquement solide** avec une séparation claire des responsabilités, une isolation du core, et une modularité via les plugins et le SDK.

Cependant, plusieurs **incohérences et dettes techniques** compromettent cette architecture :

1. **Documentation vs Réalité** : Le README promet gRPC mais l'API est HTTP
2. **Dualité Go/Python** : Core a des fichiers `.go` jamais utilisés
3. **Imports non conformes** : `sys.path` hacking dans `interfaces/api/main.py`
4. **Healthchecks incorrects** : `/v1/health` au lieu de `/health`
5. **Dossiers vides** : `core/agents/`, `core/pkg/`
6. **Composants orphelins** : `runtime/`, `rust/`, `jarvis-OS/`

### Priorités d'action

1. **P0** : Corriger les healthchecks et la documentation
2. **P1** : Décider du sort de `runtime/` et `rust/`
3. **P1** : Éliminer les doublons (`orchestration/` vs `orchestrator/`)
4. **P2** : Nettoyer les dossiers vides et `__pycache__/`
5. **P2** : Ajouter des tests d'intégration
6. **P3** : Clarifier la stratégie Go vs Python

---

**Fin du rapport**