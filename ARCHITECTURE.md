# ETHAN — Architecture Redesigned

## 4 Couches. 1 Règle : une couche ne traverse pas les barrières.

```
ethan/
├── core/           ← Cerveau. Process serveur. Expose gRPC.
├── cli/            ← Terminal UI. Client gRPC uniquement.
├── plugins/        ← Extensions. Process indépendants. NATS.
├── interfaces/     ← API REST, Desktop, Shell, WebUI, MCP.
├── infra/          ← Docker, K8s, systemd, scripts.
├── docs/           ← Documentation.
├── tests/          ← Tests E2E.
├── examples/       ← Exemples d'utilisation.
├── proto/          ← Schémas protobuf partagés.
└── pyproject.toml  ← Monorepo (workspace uv/pdm).
```

---

## 1. `core/` — Le cerveau (AI Brain)

**Principe fondateur** : `core` ne fait aucune hypothèse sur son interface. Pas d'import de `cli`, pas d'import de `api`, pas de `print()`, pas de `input()`. C'est un process serveur pur qui expose son API via gRPC.

### Structure

```
core/
├── __init__.py
├── main.py                 # Point d'entrée du daemon core
│
├── bus/                    # Event Bus
│   ├── interface.py        # ABC EventBus
│   ├── nats_bus.py         # Implémentation NATS JetStream
│   └── memory_bus.py       # Implémentation mémoire (tests)
│
├── cognition/              # Pipeline cognitive
│   ├── orchestrator.py     # Orchestrateur central
│   ├── planner.py          # Décomposition de buts
│   ├── executor.py         # Exécution de tâches
│   └── evaluator.py        # Évaluation des résultats
│
├── modules/                # Modules de base (réactifs)
│   ├── base.py             # Module + Agent (classes abstraites)
│   ├── interface.py        # ModuleInterface avec capabilities
│   ├── capability.py       # Capability dataclass
│   ├── dependency.py       # Dependency dataclass
│   ├── permissions.py      # Permissions ACL
│   └── factory.py          # ModuleFactory (création par config)
│
├── modules/memory/         # Module mémoire
├── modules/llm/            # Module LLM router
├── modules/tools/          # Module outils
│
├── registry/               # Registres
│   ├── capability.py       # CapabilityRegistry
│   ├── module.py           # ModuleRegistry (cycle de vie)
│   └── events.py           # EventSchemaRegistry (validation + migration)
│
├── types/                  # Types partagés
│   ├── event.py            # Event, EventType
│   ├── message.py          # Message
│   ├── goal.py             # Goal
│   ├── plan.py             # Plan, Task
│   └── result.py           # Result
│
├── config/                 # Configuration
│   ├── loader.py           # Chargement de config
│   ├── schema.py           # Validation de config
│   └── secrets.py          # Gestion des secrets
│
├── telemetry/              # Métriques et logs
│   ├── metrics.py          # Prometheus metrics
│   └── logger.py           # Logger structuré
│
├── grpc/                   # Serveur gRPC (pont Go↔Python)
│   └── server.py           # Implémentation OrchestratorService
│
├── pyproject.toml          # Dépendances core uniquement
└── tests/
    ├── conftest.py
    ├── test_bus.py
    ├── test_registry.py
    ├── test_modules.py
    └── test_cognition.py
```

### FORBIDDEN

```python
# ❌ INTERDIT : core ne doit JAMAIS :
from cli.colors import ...      # Pas d'import CLI
print(...)                      # Pas d'IO directe
input(...)                      # Pas d'interaction utilisateur
sys.exit(...)                   # Pas de décision de sortie
os.system(...)                  # Pas de commande shell
```

### Exported API

`core` expose UNIQUEMENT :
1. **gRPC service** (port 50051) — `ProcessEvent`, `GetState`, `ExecuteTask`, `HealthCheck`
2. **Python API** via `ethan.core.xxx` — pour les interfaces qui tournent dans le même process

---

## 2. `cli/` — Terminal UI (thin client)

**Principe fondateur** : `cli` est un client terminal. Il ne contient AUCUNE logique cognitive. Il traduit des frappes clavier en événements et affiche des réponses.

### Structure

```
cli/
├── __init__.py
├── ethan                    # Entry point (#!/usr/bin/env python)
├── install.sh               # Script d'installation
│
├── registry.py              # Découverte des commandes (mécanique pure)
│
├── commands/                # Commandes CLI (1 fichier = 1 commande)
│   ├── chat.py              # ethan chat
│   ├── status.py            # ethan status
│   ├── router.py            # ethan router <task>
│   ├── plugins.py           # ethan plugin list/install/remove
│   ├── config.py            # ethan config
│   ├── logs.py              # ethan logs
│   └── help.py              # ethan help
│
├── core/                    # ⚠️ RENOMMER en "ui/" ou "render/"
│   ├── colors.py            # ANSI colors (terminal uniquement)
│   ├── icons.py             # Icones unicode
│   ├── streamer.py          # Streaming output
│   ├── spinner.py           # Spinner animation
│   ├── errors.py            # Formatage d'erreurs
│   ├── ux.py                # Suggestions, autocomplete
│   ├── discovery.py         # CommandRegistry (métadonnées)
│   └── client.py            # Client gRPC vers core
│
├── plugins/                 # Plugins CLI (commandes additionnelles)
│   └── example/
│       ├── manifest.json
│       └── plugin.py
│
├── completion/              # Scripts de complétion shell
├── systemd/                 # Service user systemd
├── xfce/                    # Intégration bureau XFCE
│
├── pyproject.toml
└── tests/
```

### FORBIDDEN

```python
# ❌ INTERDIT : cli ne doit JAMAIS :
from core.cognition import ...    # Pas d'import direct du cerveau
from core.registry import ...     # Pas d'accès aux registres
exec(...)                         # Pas d'exécution de code métier
```

### Communication avec core

```
cli ──gRPC──► core:50051
```

`cli` parle UNIQUEMENT à `core` via gRPC. Pas d'import direct.

---

## 3. `plugins/` — Extensions

**Principe fondateur** : Un plugin est un processus indépendant. Il se connecte au EventBus NATS et déclare ses capabilities. Il ne touche jamais au kernel ni au CLI.

### Structure

```
plugins/
├── __init__.py
├── loader.py                # Chargeur de plugins (découverte, validation)
├── interface.py             # PluginInterface (ce qu'un plugin DOIT exposer)
├── validator.py             # Validation des manifestes
│
├── sdk/                     # SDK pour développer des plugins
│   ├── __init__.py
│   ├── base.py              # Plugin base class
│   ├── events.py            # Wrapper Event Bus pour plugins
│   └── manifest.py          # Générateur de manifest
│
├── store/                   # Plugins installés (via plugin install)
│   └── <source>/
│       ├── my-plugin/
│       │   ├── manifest.json
│       │   ├── plugin.py
│       │   └── requirements.txt
│
├── pyproject.toml
└── tests/
```

### Plugin Manifest

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "api_version": "2",
  "type": "module",           // "module" | "cli" | "tool"
  "capabilities": ["memory.store", "llm.generate"],
  "permissions": {
    "events_subscribe": ["planner.*"],
    "events_publish": ["memory.*"]
  }
}
```

### FORBIDDEN

```python
# ❌ INTERDIT : un plugin ne doit JAMAIS :
import core           # Pas d'import du core
import cli            # Pas d'import du CLI
os.system(...)        # Pas de shell direct
open("/etc/...")     # Pas d'accès système hors permissions
```

### Communication

```
plugin ──NATS──► ethan.module.<name>.<action>
plugin ──gRPC──► core:50051 (uniquement GetState)
```

Un plugin ne peut que :
1. Publier/souscrire à des événements NATS
2. Lire l'état via gRPC (lecture seule)

---

## 4. `infra/` — Infrastructure système

**Principe fondateur** : `infra` ne contient AUCUN code Python exécuté par le runtime. C'est de la configuration, des scripts, des templates.

### Structure

```
infra/
├── docker/
│   ├── docker-compose.yml       # Stack complète
│   ├── docker-compose.dev.yml   # Surcharge dev
│   ├── docker-compose.prod.yml  # Surcharge prod
│   ├── Dockerfile.core          # Core daemon
│   ├── Dockerfile.cli           # CLI standalone
│   └── .dockerignore
│
├── systemd/
│   ├── ethan-core.service       # Service core
│   ├── ethan-cli.service        # Service CLI (session)
│   └── ethan.target             # Multi-user target
│
├── kubernetes/
│   ├── namespace.yaml
│   ├── core-deployment.yaml
│   ├── core-service.yaml
│   ├── nats-deployment.yaml
│   ├── redis-deployment.yaml
│   └── postgres-deployment.yaml
│
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   └── posthog/
│       └── config.yml
│
├── desktop/
│   ├── launchd/                  # macOS
│   ├── windows/                  # Windows service
│   └── tauri/                    # Tauri updater config
│
├── scripts/
│   ├── install.sh                # Installateur
│   ├── update.sh                 # Mise à jour
│   ├── backup.sh                 # Sauvegarde PostgreSQL
│   └── healthcheck.sh            # Check de santé
│
├── traefik/
│   ├── traefik.yml
│   └── dynamic/
│
└── README.md                     # Documentation déploiement
```

### FORBIDDEN

```python
# ❌ INTERDIT : infra ne doit JAMAIS contenir :
# - Du code Python importé par core ou cli
# - Des modules Python
# - Des tests unitaires (sauf tests d'infra)
```

---

## 5. `interfaces/` — Ponts vers le monde extérieur

Nouveau répertoire pour toutes les interfaces non-CLI.

```
interfaces/
├── api/                        # API REST (FastAPI)
│   ├── main.py
│   ├── routers/
│   └── client.py               # Client gRPC vers core
│
├── desktop/                    # Application Tauri
│   ├── src/                    # Rust (Tauri backend)
│   └── web/                    # Frontend (React/TypeScript)
│
├── shell/                      # ethan-shell (prompt natif)
│   ├── adapters/               # bash, zsh, fish
│   └── launcher/               # Lanceur de session
│
├── mcp/                        # Model Context Protocol
│   └── server.py               # Serveur MCP
│
└── webui/                      # Interface web (Textual)
    ├── app.py
    └── components/
```

---

## Règles de dépendance — Tableau récapitulatif

| De → Vers | `core` | `cli` | `plugins` | `interfaces` | `infra` |
|-----------|--------|-------|-----------|--------------|---------|
| **`core`** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **`cli`** | ✅ gRPC only | ✅ | ✅ (découverte) | ❌ | ❌ |
| **`plugins`** | ✅ gRPC read-only | ❌ | ✅ | ❌ | ❌ |
| **`interfaces`** | ✅ gRPC only | ❌ | ❌ | ✅ | ❌ |
| **`infra`** | ❌ | ❌ | ❌ | ❌ | ✅ |

**Légende** :
- ✅ = autorisé
- ✅ gRPC only = communication via réseau uniquement
- ❌ = interdit

---

## Règles absolues (forbidden interactions)

### Règle #1 : `core` ne fait pas d'IO utilisateur
```python
# JAMAIS dans core/
print()          # ×
input()          # ×
sys.exit()       # ×
os.system()      # ×
open("/dev/")    # ×
```

### Règle #2 : `cli` n'importe pas `core` directement
```python
# JAMAIS dans cli/
from core.cognition import ...    # ×
from core.registry import ...     # ×
```

### Règle #3 : Les plugins n'importent ni `core` ni `cli`
```python
# JAMAIS dans plugins/
from core import ...    # ×
from cli import ...     # ×
```

### Règle #4 : `infra` ne contient pas de code exécutable Python
```python
# JAMAIS dans infra/
# - Du code Python importé par core ou cli
# - Des modules Python
# - Des tests unitaires (sauf tests d'infra)
```

---

## Migration du code existant

| Actuel | Nouveau | Raison |
|--------|---------|--------|
| `cli/core/colors.py` | `cli/colors.py` | C'est du rendu terminal |
| `cli/core/loading.py` | `cli/spinner.py` | Animation terminale |
| `cli/core/streaming.py` | `cli/streamer.py` | Affichage stream |
| `cli/core/client.py` | `cli/client.py` | Client gRPC |
| `cli/core/discovery.py` | `cli/discovery.py` | Mécanique CLI pure |
| `core/plugins.py` | `plugins/loader.py` | Logique de plugins dans plugins/ |
| `core/agent/*` | `core/cognition/*` | Agents = partie de la cognition |
| `modules/` | `core/modules/*` | Modules = partie du core |
| `kernel/` (Python) | `core/` | Fusion dans core |
| `kernel/` (Go) | `core/grpc/` | Serveur gRPC dans core |
| `api/` | `interfaces/api/` | API = une interface parmi d'autres |
| `ethan-ui/` | `interfaces/webui/` | WebUI = interface |
| `ethan-shell/` | `interfaces/shell/` | Shell = interface |
| `deploy/` | `infra/` | Déploiement = infra |
| `frontend/` + `desktop/` | `interfaces/desktop/` | Desktop = interface |
| `docs/` | `docs/` (reste) | Documentation transverse |

---

## Résumé

```
ethan/
├── core/           ← Cerveau. Process serveur. Expose gRPC.
├── cli/            ← Terminal UI. Client gRPC uniquement.
├── plugins/        ← Extensions. Process indépendants. NATS.
├── interfaces/     ← API REST, Desktop, Shell, WebUI, MCP.
├── infra/          ← Docker, K8s, systemd, scripts.
├── docs/           ← Documentation.
├── tests/          ← Tests E2E.
├── examples/       ← Exemples d'utilisation.
├── proto/          ← Schémas protobuf partagés.
└── pyproject.toml  ← Monorepo (workspace uv/pdm).
```

**4 couches. 1 règle : une couche ne traverse pas les barrières.**