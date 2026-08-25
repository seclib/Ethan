# ETHAN — Cognitive Operating System Runtime

[![CI](https://github.com/seclib/Ethan/actions/workflows/ci.yml/badge.svg)](https://github.com/seclib/Ethan/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Status-Alpha-yellow)

ETHAN est un **Cognitive OS Runtime** event-driven. Kernel Python, communication via NATS JetStream, persistance PostgreSQL + Redis.

> **Statut** : 🔴 NON-PRODUCTION READY — Voir [ETHAN_REFACTORING_PLAN.md](ETHAN_REFACTORING_PLAN.md)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ETHAN Stack                              │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   CLI    │  │   API    │  │  WebUI   │  │ Desktop  │    │
│  │ (Python) │  │ (FastAPI)│  │ (Next.js)│  │ (Electron)│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│       │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┘        │
│                              │                                │
│                     ┌────────▼────────┐                      │
│                     │   Event Bus      │                      │
│                     │  (NATS + JS)     │                      │
│                     └────────┬────────┘                      │
│                              │                                │
│              ┌───────────────┼───────────────┐                │
│              │               │               │                │
│        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐          │
│        │  Kernel    │  │   API     │  │  Modules  │          │
│        │ (bootstrap)│  │ (FastAPI) │  │ (8 modules)│         │
│        └───────────┘  └───────────┘  └───────────┘          │
│              │               │               │                │
│              └───────────────┼───────────────┘                │
│                              │                                │
│        ┌─────────────────────┼─────────────────────┐          │
│        │                     │                     │          │
│  ┌─────▼─────┐        ┌─────▼─────┐        ┌─────▼─────┐    │
│  │ PostgreSQL │        │   Redis   │        │  Prometheus│    │
│  │ (persistent)│       │ (live state)       │ (metrics) │    │
│  └───────────┘        └───────────┘        └───────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Prérequis
sudo apt install docker.io docker-compose-v2 curl wget
# Vérifier
./ethan doctor

# Démarrer
./ethan up

# Vérifier
./ethan status

# Voir les logs
./ethan logs api
```

### URLs après démarrage

| Service | URL |
|---------|-----|
| API Gateway | http://localhost:8000 |
| WebUI | http://localhost:3001 |
| NATS Monitoring | http://localhost:8222 |
| Prometheus | http://localhost:9090 |

### Obtenir un token JWT

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin"}'
```

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Kernel** | Python 3.12, event-driven, asyncio |
| **API** | FastAPI (port 8000) |
| **Event Bus** | NATS JetStream |
| **Live State** | Redis 7 |
| **Persistance** | PostgreSQL 16 |
| **WebUI** | Next.js (port 3000) |
| **CLI** | Python (thin client) |
| **Orchestration** | Docker Compose |
| **Métriques** | Prometheus |
| **Secrets** | Docker secrets (prod) |

## Modules Cognitifs

| Module | Rôle |
|--------|------|
| Executive | Coordination des buts, priorités |
| Planner | Décomposition de buts en tâches |
| Memory | Mémoire court-terme (Redis) + long-terme (PostgreSQL) |
| Reflective | Auto-évaluation, métacognition |
| Learning | Apprentissage et optimisation |
| Metacognition | Conscience du système |
| Autonomy | Proactivité, initiatives |
| Tools | Exécution d'outils (browser, code, etc.) |

## Commandes CLI

```bash
./ethan up          # Démarrer tous les services
./ethan down        # Arrêter tous les services
./ethan status      # Vérifier l'état
./ethan doctor      # Diagnostic complet
./ethan logs        # Voir les logs
./ethan cli         # Lancer le CLI interactif
./ethan webui       # Démarrer la WebUI (dev)
./ethan migrate     # Migrations DB
```

## Déploiement

```bash
# Dev
./ethan up

# Prod (hardening requis — voir ETHAN_REFACTORING_PLAN.md)
docker compose -f docker-compose.prod.yml up -d
```

## Documentation

| Document | Description |
|----------|-------------|
| [ETHAN_REFACTORING_PLAN.md](ETHAN_REFACTORING_PLAN.md) | Plan de stabilisation et refactorisation |
| [docs/architecture.md](docs/architecture.md) | Architecture détaillée |
| [docs/boot-from-scratch.md](docs/boot-from-scratch.md) | Installation complète |
| [docs/sre-runbook.md](docs/sre-runbook.md) | Runbook opérationnel |
| [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) | Audit sécurité |
| [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) | État des lieux production |

## Licence

Apache-2.0