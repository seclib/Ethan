# Architecture Actuelle — Ethan

> Document d'audit : état des lieux du dépôt Ethan.
> Date : 2026-06-21

---

## 1. Vue d'Ensemble

Ethan est une plateforme IA modulaire avec :

- **Backend Python** (FastAPI)
- **Frontend TypeScript** (Vite + React/Tauri)
- **Core** bibliothèques Python (LLM, Events, Auth, Memory, etc.)
- **Plugins** extensibles (browser, terminal)
- **Fournisseurs IA** (Ollama, OpenAI, Anthropic)
- **Déploiement Docker** complet

---

## 2. Structure des Répertoires

```
Ethan/
│
├── apps/                  # Points d'entrée applicatifs
│   ├── api/               # API publique
│   └── gateway/           # API Gateway
│
├── core/                  # Bibliothèques fondamentales
│   ├── agents/            # Moteur d'agents IA (vide)
│   ├── auth/              # Authentification & RBAC
│   ├── config/            # Configuration
│   ├── context/           # Gestion de contexte
│   ├── events/            # Event Bus asynchrone
│   ├── llm/               # Abstraction LLM (interface + registry)
│   ├── memory/            # Système de mémoire unifié
│   ├── metrics/           # Métriques Prometheus
│   ├── planner/           # Planificateur de tâches
│   ├── scheduler/         # Planificateur de jobs
│   ├── security/          # Sécurité (vide)
│   ├── __init__.py        # Module docstring
│   └── plugins.py         # Plugin manager
│
├── providers/             # Fournisseurs LLM concrets
│   ├── ollama.py          # Provider Ollama
│   ├── openai.py          # Provider OpenAI
│   └── anthropic.py       # Provider Anthropic
│
├── plugins/               # Plugins système
│   ├── browser/           # Plugin navigateur
│   └── terminal/          # Plugin terminal
│
├── sdk/                   # Kits de développement
│   ├── python/            # SDK Python (vide)
│   └── typescript/        # SDK TypeScript (vide)
│
├── workers/               # Workers asynchrones (vide)
│
├── frontend/              # Interface web
│   ├── src/               # Code source frontend
│   ├── src-tauri/         # Application desktop Tauri
│   ├── index.html
│   └── vite.config.ts
│
├── deploy/                # Déploiement
│   ├── docker/            # Dockerfiles + docker-compose
│   ├── traefik/           # Configuration Traefik
│   ├── prometheus/        # Configuration Prometheus
│   ├── grafana/           # Configuration Grafana
│   ├── kubernetes/        # Manifests K8s (vide)
│   ├── launchd/           # Service macOS
│   ├── systemd/           # Service Linux
│   └── windows/           # Scripts Windows
│
├── configs/               # Configuration applicative
│   └── ethan/        # Fichiers .toml, prompts
│
├── scripts/               # Scripts utilitaires
│
├── tests/                 # Tests (complets)
│
├── docs/                  # Documentation
│   ├── architecture/      # Architecture docs
│   ├── deployment/        # Guide déploiement
│   ├── development/       # Guide développement
│   └── getting-started/   # Guide démarrage
│
├── docker-compose.yml     # Production stack (racine)
├── docker-compose.dev.yml # Development stack (racine)
├── .env.example           # Variables d'environnement
└── Makefile               # Commandes automatisées
```

---

## 3. Composants Détail

### 3.1 Core — LLM Abstraction (`core/llm/`)

**État :** ✅ Fonctionnel

**Architecture :**
- Interface `LLMProvider` (ABC) avec chat, stream, embed, list_models
- `ProviderRegistry` pour enregistrer/récupérer les providers
- Instance globale `registry` + fonction `get_provider()`

**Points forts :**
- Interface claire et propre
- Registry extensible
- Changement de provider via configuration

**Points faibles :**
- Pas de fallback automatique si un provider échoue
- Pas de cache des réponses
- Pas de rate limiting

### 3.2 Core — Event System (`core/events/`)

**État :** ✅ Fonctionnel

**Architecture :**
- `EventBus` asynchrone publish/subscribe
- Priorités (LOW, NORMAL, HIGH, CRITICAL)
- Filtrage par type d'événement
- Handlers wildcard

**Points forts :**
- Asynchrone et non-bloquant
- Découplage total entre composants
- Instance globale `bus`

**Points faibles :**
- Pas de persistance des événements
- Pas de compatibilité NATS/Redis Streams
- Pas de rétention/tracing

### 3.3 Core — Memory (`core/memory/`)

**État :** ✅ Fonctionnel

**Backends disponibles :**
| Backend | Usage | Type |
|---------|-------|------|
| SQLite | Persistance locale | Relationnel |
| Redis | Cache / sessions | Clé-valeur |
| ChromaDB | Vectorielle dev | Vectoriel |
| Qdrant | Vectorielle prod | Vectoriel |

**Points faibles :**
- Pas d'interface unifiée (ABC MemoryBackend)
- Pas de gestion automatique du cycle de vie
- Pas d'indexation plein texte

### 3.4 Core — Auth (`core/auth/`)

**État :** ✅ Fonctionnel

**Fonctionnalités :**
- JWT tokens
- API Keys
- RBAC de base

### 3.5 Core — Planner (`core/planner/`)

**État :** ⚠️ Présent mais non vérifié

### 3.6 Core — Scheduler (`core/scheduler/`)

**État :** ⚠️ Présent mais non vérifié

### 3.7 Core — Security (`core/security/`)

**État :** ❌ Vide (dossier créé mais pas de contenu)

### 3.8 Core — Agents (`core/agents/`)

**État :** ❌ Vide (dossier créé mais pas de contenu)

### 3.9 Plugins (`plugins/`)

**État :** ✅ Fonctionnel

**Plugins disponibles :**
- `browser/` — Contrôle navigateur
- `terminal/` — Exécution commandes

**Points faibles :**
- Pas de gestionnaire de plugins dynamique
- Pas de SDK public
- Pas de sandbox

### 3.10 Providers (`providers/`)

**État :** ✅ Fonctionnel

**Fournisseurs :**
- Ollama (local)
- OpenAI (cloud)
- Anthropic (cloud)

**Points forts :**
- Interface commune
- Registry dynamique

### 3.11 Frontend (`frontend/`)

**État :** ✅ Fonctionnel

- **TypeScript** (Vite)
- **Desktop** (Tauri)
- API client intégré

---

## 4. Déploiement Docker

### 4.1 Services (docker-compose.yml)

| Service | Image | Port | Statut |
|---------|-------|------|--------|
| backend | Dockerfile.backend | 8000 | ✅ |
| frontend | Dockerfile.frontend | 80 | ✅ |
| postgres | postgres:16-alpine | 5432 | ✅ |
| redis | redis:7-alpine | 6379 | ✅ |
| chromadb | chromadb/chroma | 8000 | ✅ |
| qdrant | qdrant/qdrant | 6333 | ✅ |
| ollama | ollama/ollama | 11434 | ✅ |
| traefik | traefik:v3.1 | 80/443 | ✅ |
| prometheus | prom/prometheus | 9090 | ✅ |
| grafana | grafana/grafana | 3000 | ✅ |

### 4.2 Réseau

- Réseau dédié : `jarvis-network`
- Isolé des autres stacks

### 4.3 Volumes

12 volumes persistants (config, logs, workspace, memory, uploads, cache, models, postgres, redis, chromadb, qdrant, prometheus, grafana)

---

## 5. Dépendances Entre Composants

```
frontend ──► backend ──┬──► ollama
                        ├──► providers (OpenAI, Anthropic)
                        ├──► core/llm (abstraction)
                        ├──► core/memory (SQLite/Redis/Qdrant/ChromaDB)
                        ├──► core/events (Event Bus)
                        ├──► core/auth (JWT)
                        └──► plugins (browser, terminal)
```

**Pattern :** Le backend est le point central. Tous les services sont optionnels et désactivables.

---

## 6. Points Forts

- **Architecture modulaire** : Core, providers, plugins bien séparés
- **Services optionnels** : Tous les services Docker sont désactivables
- **Event-driven** : Event Bus pour découplage
- **LLM abstraction** : Interface commune pour tous les fournisseurs
- **Memory backends** : Plusieurs niveaux de mémoire
- **Docker complet** : Production-ready
- **Monitoring** : Prometheus + Grafana + alertes
- **Reverse proxy** : Traefik avec SSL Let's Encrypt
- **Healthchecks** : Tous les services

---

## 7. Points Faibles

1. **core/agents/** vide — Pas de système d'agents formel
2. **core/security/** vide — Pas de sandbox ni de validation
3. **sdk/** vide — Pas de SDK public
4. **workers/** vide — Pas de workers asynchrones
5. **Pas de pipeline voix** — STT/TTS/Wake Word absents
6. **Pas de pipeline vision** — Webcam/OCR absents
7. **Pas de RAG complet** — Ingestion documents absente
8. **Pas de cache LLM** — Réponses non mises en cache
9. **Pas de rate limiting** — Pas de protection contre l'abus
10. **Pas de tracing** — OpenTelemetry non intégré
11. **Pas de Kubernetes** — Manifests absents
12. **Plugins statiques** — Pas d'installation dynamique

---

## 8. Améliorations Proposées

| Priorité | Amélioration | Effort | Impact |
|----------|-------------|--------|--------|
| P0 | Système d'agents (core/agents/) | M | H |
| P0 | Sécurité/Sandbox (core/security/) | M | H |
| P1 | SDK public | L | H |
| P1 | Workers asynchrones | M | M |
| P1 | Cache LLM | L | M |
| P1 | Pipeline voix (STT/TTS) | H | H |
| P1 | Pipeline vision | M | M |
| P2 | RAG complet | M | H |
| P2 | Rate limiting | L | M |
| P2 | Tracing OpenTelemetry | M | M |
| P2 | Plugins dynamiques | M | M |
| P3 | Kubernetes manifests | M | L |
| P3 | Multi-arch images | M | L |

---

## 9. Métriques Clés

- **Fichiers Python** : ~120
- **Fichiers TypeScript** : ~40
- **Tests** : ~50 fichiers de test
- **Dockerfiles** : 6 (backend, frontend, gpu, sandbox)
- **Services Docker** : 10
- **Plugins** : 2 (browser, terminal)
- **Providers LLM** : 3 (Ollama, OpenAI, Anthropic)
- **Backends mémoire** : 4 (SQLite, Redis, ChromaDB, Qdrant)

---

## 10. Conclusion

Ethan est une base solide avec une architecture bien pensée. Les fondations sont en place (LLM abstraction, Event Bus, Docker, monitoring). Les priorités sont de compléter :

1. Le système d'agents (coeur de l'orchestration)
2. La sécurité (sandbox pour exécution de plugins)
3. Les pipelines voix et vision
4. Le SDK public
5. Les workers asynchrones