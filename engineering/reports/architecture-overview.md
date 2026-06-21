# Architecture Overview — Ethan

> RFC-001 — Vue d'ensemble de l'architecture
> Date : 2026-06-21

---

## 1. Architecture Applicative

### 1.1 Backend Python

Le backend est organisé en plusieurs couches :

```
┌─────────────────────────────────────────────────────┐
│                   Apps Layer                         │
│  apps/api/    apps/gateway/     CLI (jarvis)         │
├─────────────────────────────────────────────────────┤
│                  Core Layer                          │
│  core/agents/   core/llm/    core/events/            │
│  core/auth/     core/memory/  core/metrics/          │
│  core/planner/  core/scheduler/  core/security/      │
│  core/config/   core/context/  core/plugins.py       │
├─────────────────────────────────────────────────────┤
│               Providers Layer                        │
│  providers/ollama.py  providers/openai.py            │
│  providers/anthropic.py                              │
├─────────────────────────────────────────────────────┤
│               Plugins Layer                          │
│  plugins/browser/   plugins/terminal/                │
├─────────────────────────────────────────────────────┤
│           Legacy Package (src/ethan/)           │
│  CLI, engine, agents, channels, mining, telemetry    │
│  traces, sessions, skills, tools, templates, etc.    │
├─────────────────────────────────────────────────────┤
│               Rust Workspace                         │
│  16 crates (core, engine, agents, tools, learning,   │
│  telemetry, traces, security, mcp, python, sessions,  │
│  workflow, skills, recipes, templates, a2a, scheduler)│
└─────────────────────────────────────────────────────┘
```

### 1.2 Frontend

```
┌─────────────────────────────────────────────────────┐
│                Frontend (React + Vite)               │
│                                                      │
│  App (React Router)                                  │
│  ├── Chat                                            │
│  ├── Dashboard                                       │
│  ├── Logs                                            │
│  └── Administration                                  │
│                                                      │
│  Components (shadcn/ui + tailwindcss)                │
│  ├── Chat messages, Markdown rendering               │
│  ├── Charts (Recharts)                               │
│  └── UI primitives (Base UI, Lucide icons)           │
│                                                      │
│  Desktop (Tauri 2)                                   │
│  └── Native window, system tray, shortcuts           │
└─────────────────────────────────────────────────────┘
```

### 1.3 Applications Desktop

```
┌─────────────────────────────────────────────────────┐
│            Desktop (Tauri 2)                         │
│                                                      │
│  frontend/src-tauri/                                 │
│  ├── src/ (Rust backend natif)                      │
│  ├── binaries/ (ressources natives)                 │
│  └── tauri.conf.json                                 │
│                                                      │
│  Fonctionnalités :                                   │
│  - Autostart                                         │
│  - Global shortcuts                                  │
│  - Notifications                                     │
│  - Dialog system                                     │
│  - Auto-updater                                      │
│  - Shell integration                                 │
└─────────────────────────────────────────────────────┘
```

---

## 2. Services Tier

### 2.1 Docker Services

| Service | Rôle | Dépend de |
|---------|------|-----------|
| **backend** | API FastAPI | ollama |
| **frontend** | Nginx (frontend build) | backend |
| **traefik** | Reverse proxy / SSL | - |
| **postgres** | Base de données | - |
| **redis** | Cache / sessions | - |
| **chromadb** | Vectorielle (dev) | - |
| **qdrant** | Vectorielle (prod) | - |
| **ollama** | LLM local | - |
| **prometheus** | Monitoring | - |
| **grafana** | Dashboards | prometheus |

### 2.2 Réseau

- Réseau dédié : `jarvis-network` (bridge)
- Tous les services sur ce réseau
- Traefik expose 80/443/8080

---

## 3. Flux de données

### 3.1 Requête API

```
Client ──► Traefik (80/443) ──► Frontend (Nginx) ──► Backend (FastAPI)
                                      │                     │
                                      │               ┌─────┴──────┐
                                      │               │   Ollama   │
                                      │               │  (LLM)     │
                                      │               └─────┬──────┘
                                      │                     │
                                      │               ┌─────┴──────┐
                                      │               │  Memory    │
                                      │               │ (SQLite/   │
                                      │               │  Redis/    │
                                      │               │  Qdrant)   │
                                      │               └────────────┘
```

### 3.2 Communication Agents

```
Agent A ──┬──► Event Bus ──┬──► Agent B
          │                 │
          │                 └──► Agent C
          └──► Prometheus Metrics
```

---

## 4. Extensions Points

### 4.1 Providers

- Interface `LLMProvider` (ABC)
- Registry : `ProviderRegistry`
- Ajout : implémenter l'interface + enregistrer

### 4.2 Plugins

- Dossier `plugins/` avec `plugin.yaml` + `main.py`
- Plugin manager : `core/plugins.py`
- Ajout : créer un dossier plugin + enregistrer

### 4.3 Agents

- Interface `Agent` (ABC)
- Registry : `AgentRegistry`
- Ajout : hériter de Agent + enregistrer

### 4.4 Memory Backends

- Interface `MemoryBackend`
- Backends : SQLite, Redis, ChromaDB, Qdrant
- Ajout : implémenter l'interface

---

## 5. Observation sur l'Architecture

### Points forts
- **Couches bien séparées** : apps, core, providers, plugins
- **Event-driven** : Event Bus pour découplage
- **Multi-langage** : Python + TypeScript + Rust
- **Extensible** : Providers, plugins, agents, memory backends
- **Testable** : Tests unitaires + intégration

### Points faibles
- **Dualité src/ethan/ vs core/** : Le code historique et les nouvelles abstractions coexistent sans stratégie de migration
- **Agents vides** : Le système d'agents est nouveau et pas encore intégré
- **SDK vide** : Les SDKs sont squelettiques
- **Pas de pipeline voix/vision** : Fonctionnalités demandées mais absentes
- **Pas de RAG complet** : Ingestion document absente
- **Workers vides** : Aucun worker asynchrone
- **Kubernetes vide** : Manifests K8s absents