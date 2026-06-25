# ETHAN CORE DAEMON — Cognitive Operating System Runtime

**Version** : 1.0.0  
**Statut** : Specification Officielle  
**Dernière mise à jour** : Juin 2026  
**Audience** : Architects, DevOps, Kernel Developers, System Integrators

---

## Table des matières

1. [Vision Système](#1-vision-système)
2. [Qu'est-ce qu'ETHAN ?](#2-quest-ce-quethan)
3. [Ce qu'ETHAN n'est pas](#3-ce-quethan-nest-pas)
4. [Architecture Globale](#4-architecture-globale)
5. [ETHAN Core Daemon](#5-ethan-core-daemon)
6. [Systemd Service](#6-systemd-service)
7. [Boot Lifecycle](#7-boot-lifecycle)
8. [Event Loop Principal](#8-event-loop-principal)
9. [Modules Internes](#9-modules-internes)
10. [Flux Complet d'une Commande](#10-flux-complet-dune-commande)
11. [Système de Mémoire](#11-système-de-mémoire)
12. [Event Bus (NATS)](#12-event-bus-nats)
13. [LLM Router](#13-llm-router)
14. [Security Layer](#14-security-layer)
15. [CLI Interface](#15-cli-interface)
16. [Architecture Docker](#16-architecture-docker)
17. [Critique Architecturale](#17-critique-architecturale)
18. [Points Forts](#18-points-forts)
19. [Faiblesses et Risques](#19-faiblesses-et-risques)
20. [Dette Architecturale](#20-dette-architecturale)
21. [Incohérences](#21-incohérences)
22. [Actions Requises](#22-actions-requises)
23. [Roadmap](#23-roadmap)

---

## 1. Vision Système

ETHAN est un **Cognitive Operating System Runtime**.

Ce n'est pas une application. Ce n'est pas un service web. C'est un **daemon systemd permanent** qui héberge, orchestre et maintient des modules de cognition autonomes.

### Principe fondamental

```
┌─────────────────────────────────────────────────────────────┐
│                    LINUX HOST                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              systemd (PID 1)                          │  │
│  │                    │                                  │  │
│  │                    ▼                                  │  │
│  │         ┌────────────────────┐                       │  │
│  │         │  ethan-core.service│  ← DAEMON PERMANENT   │  │
│  │         │  (PID 1234)        │                        │  │
│  │         └─────────┬──────────┘                        │  │
│  │                   │                                   │  │
│  │         ┌─────────┴──────────┐                       │  │
│  │         │  Event Bus (NATS)  │                        │  │
│  │         └─────────┬──────────┘                        │  │
│  │                   │                                   │  │
│  │    ┌──────────────┼──────────────┐                   │  │
│  │    │              │              │                    │  │
│  │    ▼              ▼              ▼                    │  │
│  │  Module        Module         Module                  │  │
│  │  Cognition     Memory        Planner                  │  │
│  │    ...          ...            ...                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   CLI ethan  │  │   API HTTP   │  │   Desktop    │     │
│  │  (thin client)│  │  (thin client)│  │  (thin client)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Caractéristiques système

| Caractéristique | Description |
|-----------------|-------------|
| **Type** | Daemon systemd permanent |
| **État** | Stateful (état externalisé) |
| **Communication** | Event-driven (NATS) |
| **Modules** | Processus indépendants |
| **Interfaces** | CLI, API, Desktop, Shell |
| **Persistence** | PostgreSQL + Redis |
| **Haute disponibilité** | Auto-restart, health checks |

---

## 2. Qu'est-ce qu'ETHAN ?

ETHAN est un **runtime de système d'exploitation cognitif**.

### Définition formelle

> ETHAN est un daemon Linux qui maintient un état de cognition persistant, orchestre des modules de raisonnement autonomes, et expose des interfaces standardisées pour l'interaction humaine ou machine.

### Composants

1. **Core Daemon** : processus principal, point d'entrée unique
2. **Event Bus** : NATS JetStream, communication inter-modules
3. **Modules** : processus indépendants avec responsabilités uniques
4. **Persistence** : PostgreSQL (permanent) + Redis (temporaire)
5. **Interfaces** : clients fins sans logique métier

### Fonctionnement

ETHAN ne répond pas à des questions. ETHAN héberge de la cognition.

- Il observe des événements
- Il maintient un état persistant
- Il orchestre des modules
- Il prend des décisions
- Il apprend de ses actions

---

## 3. Ce qu'ETHAN n'est pas

| Concept | Pourquoi ce n'est pas ETHAN |
|---------|----------------------------|
| **Chatbot** | Un chatbot est réactif. ETHAN est proactif et autonome. |
| **Agent LLM** | Un agent LLM est un wrapper d'API. ETHAN est un OS complet. |
| **Application web** | Une app web est client-serveur. ETHAN est un runtime distribué. |
| **Framework** | Un framework fournit des outils. ETHAN fournit un substrat. |
| **Service cloud** | Un service cloud est multi-tenant. ETHAN est local-first. |
| **Script** | Un script est séquentiel. ETHAN est event-driven et parallèle. |

---

## 4. Architecture Globale

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        LINUX HOST                               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    systemd                                │ │
│  │                       │                                    │ │
│  │                       ▼                                    │ │
│  │            ┌──────────────────────┐                       │ │
│  │            │   ethan-core.service │                       │ │
│  │            │   (PID 1 - main)     │                       │ │
│  │            └──────────┬───────────┘                       │ │
│  │                       │                                    │ │
│  │            ┌──────────┴───────────┐                       │ │
│  │            │   Event Bus (NATS)   │                       │ │
│  │            │   JetStream          │                       │ │
│  │            └──────────┬───────────┘                       │ │
│  │                       │                                    │ │
│  │    ┌──────────────────┼──────────────────┐               │ │
│  │    │                  │                  │                │ │
│  │    ▼                  ▼                  ▼                │ │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐            │ │
│  │  │ Cognition│   │  Memory  │   │  Planner │            │ │
│  │  │ Module   │   │  Module  │   │  Module  │            │ │
│  │  └──────────┘   └──────────┘   └──────────┘            │ │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐            │ │
│  │  │ Executive│   │ Reflective│  │ Autonomy │            │ │
│  │  │ Module   │   │  Module  │   │  Module  │            │ │
│  │  └──────────┘   └──────────┘   └──────────┘            │ │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐            │ │
│  │  │  Learning│   │   LLM    │   │  Tools   │            │ │
│  │  │  Module  │   │  Router  │   │  Manager │            │ │
│  │  └──────────┘   └──────────┘   └──────────┘            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   CLI ethan  │  │   API HTTP   │  │   Desktop    │        │
│  │  (thin client)│  │  (thin client)│  │  (thin client)│        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  PostgreSQL  │  │    Redis     │  │     NATS     │        │
│  │  (long-term) │  │  (short-term)│  │  (event bus) │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Flux de données

```
Interface (CLI/API/Desktop)
    │
    │ Émet événement
    ▼
Event Bus (NATS)
    │
    │ Route vers module
    ▼
Core Daemon (Kernel)
    │
    │ Orchestre
    ▼
Modules (Cognition, Memory, Planner, Tools, LLM)
    │
    │ Écrivent état
    ▼
Persistence (Redis + PostgreSQL)
    │
    │ Retournent résultat
    ▼
Interface (présente le résultat)
```

---

## 5. ETHAN Core Daemon

### Définition

> **ETHAN Core Daemon** est le processus principal du système. C'est le cerveau vivant d'ETHAN. Il tourne en permanence, orchestre les modules, et maintient l'état global du système.

### Responsabilités

1. **Initialisation** : charger la config, démarrer les modules, établir les connexions
2. **Orchestration** : router les événements, coordonner les modules
3. **État** : maintenir l'état global, persister les transitions
4. **Supervision** : health checks, restart des modules crashés
5. **Shutdown** : arrêt gracieux, persistance de l'état

### Architecture interne

```
┌─────────────────────────────────────────────────────────────┐
│                    ETHAN Core Daemon                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                  Kernel (Go)                          │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │ │
│  │  │   Router   │  │ Scheduler  │  │ State Manager  │  │ │
│  │  └────────────┘  └────────────┘  └────────────────┘  │ │
│  │  ┌────────────────────┐  ┌────────────────────────┐  │ │
│  │  │ Capability Registry│  │     Goal Manager       │  │ │
│  │  └────────────────────┘  └────────────────────────┘  │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │              Event Bus (NATS)                   │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Orchestrator (Python)                    │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │ │
│  │  │ Cognition  │  │   Memory   │  │    Planner     │  │ │
│  │  └────────────┘  └────────────┘  └────────────────┘  │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │ │
│  │  │   Tools    │  │    LLM     │  │   Security     │  │ │
│  │  └────────────┘  └────────────┘  └────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Entrypoint

**Fichier** : `kernel/main.go`

**Processus** :
1. Charger la configuration (`ethan.yaml`)
2. Initialiser le module manager
3. Démarrer tous les modules configurés
4. Initialiser le gateway HTTP (port 8080)
5. Attendre les signaux (SIGINT, SIGTERM)
6. Shutdown gracieux

### Event Loop

```
┌─────────────────────────────────────────┐
│         EVENT LOOP (main)               │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  1. Receive event from NATS       │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  2. Validate event (Security GW)  │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  3. Route to module (Router)      │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  4. Execute module handler        │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  5. Persist state (Redis + PG)    │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  6. Emit result event             │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  7. Loop (back to 1)              │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 6. Systemd Service

### Fichier de service

**Emplacement** : `/etc/systemd/system/ethan-core.service`

```ini
[Unit]
Description=ETHAN Cognitive Runtime Core
Documentation=https://ethan.example.com/docs
After=network.target postgresql.service redis.service nats.service
Wants=postgresql.service redis.service nats.service
Requires=network.target

[Service]
Type=simple
User=ethan
Group=ethan
WorkingDirectory=/opt/ethan

# Entrypoint
ExecStart=/opt/ethan/bin/ethan-core --config /etc/ethan/ethan.yaml

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/ethan /var/log/ethan
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictNamespaces=true
LockPersonality=true
MemoryDenyWriteExecute=true
SystemCallFilter=@system-service

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
TasksMax=256

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ethan-core

# Health check
ExecStartPost=/opt/ethan/bin/ethanctl healthcheck --timeout 30

[Install]
WantedBy=multi-user.target
```

### Commandes systemd

```bash
# Démarrer ETHAN
sudo systemctl start ethan-core

# Arrêter ETHAN
sudo systemctl stop ethan-core

# Redémarrer ETHAN
sudo systemctl restart ethan-core

# Voir le statut
sudo systemctl status ethan-core

# Voir les logs
sudo journalctl -u ethan-core -f

# Activer au boot
sudo systemctl enable ethan-core

# Désactiver au boot
sudo systemctl disable ethan-core
```

---

## 7. Boot Lifecycle

### 7.1 Startup Sequence

```
systemd boot
    │
    ▼
1. Load ethan-core.service
    │
    ▼
2. systemd starts ethan-core process (PID 1)
    │
    ▼
3. main() entrypoint
    │
    ├─► Load config (ethan.yaml)
    ├─► Connect to NATS
    ├─► Connect to Redis
    ├─► Connect to PostgreSQL
    │
    ▼
4. Initialize Kernel (Go)
    │
    ├─► Start Event Bus (NATS JetStream)
    ├─► Start Router
    ├─► Start Scheduler
    ├─► Start State Manager
    │
    ▼
5. Initialize Orchestrator (Python)
    │
    ├─► Load modules (Cognition, Memory, Planner, etc.)
    ├─► Register capabilities
    ├─► Subscribe to events
    │
    ▼
6. Start HTTP Gateway (port 8080)
    │
    ▼
7. System ready
    │
    └─► Log: "✅ ETHAN Core started"
```

### 7.2 Shutdown Sequence

```
Signal (SIGINT/SIGTERM)
    │
    ▼
1. Catch signal
    │
    ▼
2. Stop accepting new events
    │
    ▼
3. Drain event queue (finish pending events)
    │
    ▼
4. Stop modules (graceful shutdown)
    │
    ├─► Cognition: save state
    ├─► Memory: flush to PostgreSQL
    ├─► Planner: checkpoint current goals
    │
    ▼
5. Close NATS connections
    │
    ▼
6. Close Redis connections
    │
    ▼
7. Close PostgreSQL connections
    │
    ▼
8. Exit cleanly
    │
    └─► Log: "✅ Shutdown complete"
```

### 7.3 Recovery

```
Module crash
    │
    ▼
1. Kernel detects crash (health check)
    │
    ▼
2. Kernel emits "module.crashed" event
    │
    ▼
3. Kernel restarts module (exponential backoff)
    │
    ├─► Attempt 1: immediate
    ├─► Attempt 2: wait 1s
    ├─► Attempt 3: wait 2s
    ├─► Attempt 4: wait 4s
    └─► Max: 5 attempts
    │
    ▼
4. If max attempts reached
    │
    ├─► Emit "module.failed" event
    ├─► Log error
    └─► Continue without module (degraded mode)
    │
    ▼
5. If module recovers
    │
    ├─► Emit "module.recovered" event
    └─► Resume normal operation
```

### 7.4 Health Checks

**Endpoint** : `GET http://localhost:8080/health`

**Response** :
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "modules": {
    "cognition": "running",
    "memory": "running",
    "planner": "running",
    "tools": "running",
    "llm": "running"
  },
  "connections": {
    "nats": "connected",
    "redis": "connected",
    "postgres": "connected"
  }
}
```

**Health check frequency** : toutes les 30 secondes  
**Timeout** : 5 secondes  
**Unhealthy threshold** : 3 échecs consécutifs → restart

---

## 8. Event Loop Principal

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT LOOP (Kernel)                       │
│                                                             │
│  ┌──────────────┐                                          │
│  │   NATS Sub   │  ← Subscribe to all subjects             │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │  Validation  │  ← Security Gateway                       │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │    Router    │  ← Match event → module                  │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │   Handler    │  ← Execute module logic                  │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │  Persistence │  ← Write to Redis + PostgreSQL           │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │   Emit       │  ← Publish result event                  │
│  └──────┬───────┘                                          │
│         │                                                   │
│         └──────────────► Loop                               │
└─────────────────────────────────────────────────────────────┘
```

### Caractéristiques

| Propriété | Valeur |
|-----------|--------|
| **Concurrency** | Goroutines (Go) |
| **Throughput** | 100k+ events/sec |
| **Latency** | < 1ms (routing) |
| **Ordering** | Par subject (garanti par NATS) |
| **Durability** | JetStream + PostgreSQL |

---

## 9. Modules Internes

### 9.1 Cognition

**Responsabilité** : Analyse d'intention, raisonnement, compréhension

**Entrées** : `interface.command`, `interface.message`  
**Sorties** : `cognition.intent.analyzed`, `cognition.reasoning.complete`

**Dépendances** : LLM Router, Memory

### 9.2 Memory

**Responsabilité** : Stockage, rappel, assemblage de contexte

**Architecture** :
```
Memory Manager
    │
    ├─► Working Memory (Redis)
    │   - Session state
    │   - Recent context (TTL)
    │
    ├─► Long-term Memory (PostgreSQL)
    │   - Event log (append-only)
    │   - Goals history
    │   - Learned patterns
    │
    └─► Vector Store (pgvector)
        - Semantic embeddings
        - Similarity search
```

### 9.3 Planner

**Responsabilité** : Décomposition de buts en tâches

**Entrées** : `planner.goal.created`  
**Sorties** : `planner.plan.created`, `planner.task.created`

**Algorithme** :
1. Recevoir un but (goal)
2. Analyser les capabilities disponibles
3. Décomposer en DAG de tâches
4. Optimiser l'ordre d'exécution
5. Émettre le plan

### 9.4 Executive

**Responsabilité** : Coordination des buts, gestion des priorités

**Entrées** : `executive.goal.created`  
**Sorties** : `executive.goal.updated`, `executive.priority.changed`

### 9.5 Tools

**Responsabilité** : Exécution d'outils atomiques

**Architecture** :
```
Tool Manager
    │
    ├─► Tool Registry (catalogue)
    ├─► Tool Selector (scoring)
    ├─► Tool Executor (exécution)
    └─► Tool Monitor (surveillance)
```

**Risk Levels** :
- LOW : read-only (web_search, file_read)
- MEDIUM : write (file_write, code_writer)
- HIGH : execute (shell_exec, code_runner)
- CRITICAL : system (process_kill, service_restart)

### 9.6 LLM Router

**Responsabilité** : Sélection du meilleur LLM selon le contexte

**Critères** :
- Complexité de la requête
- Coût
- Latence
- Disponibilité
- Capacités (vision, code, reasoning)

**Providers** :
- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Google (Gemini 1.5 Pro, Gemini 2.0)
- Ollama (Llama 3, Mistral, Gemma)
- vLLM (Llama, Mixtral)
- SGLang (multi-model)
- llama.cpp (GGUF)
- LiteLLM (agrégateur)

### 9.7 Security

**Responsabilité** : Validation, permissions, audit

**Architecture** :
```
Security Gateway
    │
    ├─► Input Validation (signatures, schémas)
    ├─► Permission Check (RBAC par capability)
    ├─► Policy Engine (rules, rate limiting)
    └─► Audit Log (traces)
```

### 9.8 Scheduler

**Responsabilité** : Exécution temporelle et conditionnelle

**Features** :
- Cron jobs
- Event-based triggers
- Retry avec backoff exponentiel
- Timeout management

### 9.9 Skills

**Responsabilité** : Compétences composées d'outils

**Exemples** :
- Programming (analyse → écriture → review → tests)
- Web Search (recherche → extraction → résumé)
- PDF Analysis (lecture → extraction → analyse)

---

## 10. Flux Complet d'une Commande

### Exemple : `ethan chat "résume ce document"`

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLI (thin client)                                        │
│    $ ethan chat "résume ce document"                        │
│    │                                                         │
│    │ Parse args, validate input                             │
│    │ Create Event:                                          │
│    │ {                                                       │
│    │   type: "interface.command",                           │
│    │   source: "cli",                                       │
│    │   payload: { cmd: "chat", args: ["résume ce doc"] }    │
│    │ }                                                       │
│    │                                                         │
│    │ Publish to NATS: ethan.interface.cli                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ETHAN Core Daemon (Kernel)                               │
│    │                                                         │
│    │ Receive event from NATS                                │
│    │ Validate (Security Gateway)                             │
│    │ Route to: cognition_pipeline                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Cognition Module                                         │
│    │                                                         │
│    │ Analyze intent:                                        │
│    │ - Intent: "summarize"                                  │
│    │ - Target: "document"                                   │
│    │ - Context: user_id, session_id                         │
│    │                                                         │
│    │ Emit: cognition.intent.analyzed                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Memory Lookup                                            │
│    │                                                         │
│    │ Retrieve context:                                      │
│    │ - Recent conversations (Redis)                         │
│    │ - Relevant memories (pgvector)                         │
│    │ - Active goals (PostgreSQL)                            │
│    │                                                         │
│    │ Assemble context window                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Planner Module                                           │
│    │                                                         │
│    │ Decompose goal:                                        │
│    │ - Task 1: Load document                                │
│    │ - Task 2: Read content                                 │
│    │ - Task 3: Summarize (via LLM)                          │
│    │ - Task 4: Format response                              │
│    │                                                         │
│    │ Create execution plan (DAG)                            │
│    │ Emit: planner.plan.created                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Tool Selection                                           │
│    │                                                         │
│    │ For each task:                                         │
│    │ - Task 1: Select "file_reader" tool                   │
│    │ - Task 2: Select "text_extractor" tool                │
│    │ - Task 3: Select "llm" tool (via LLM Router)          │
│    │ - Task 4: Select "formatter" tool                     │
│    │                                                         │
│    │ Validate permissions (Security Gateway)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. LLM Router                                               │
│    │                                                         │
│    │ Select best LLM for summarization:                     │
│    │ - Complexity: MEDIUM                                   │
│    │ - Cost: prefer local (Ollama)                          │
│    │ - Latency: < 5s acceptable                             │
│    │ - Availability: check Ollama status                    │
│    │                                                         │
│    │ Decision: Ollama (Llama 3 8B)                          │
│    │ Fallback: OpenAI GPT-4o if Ollama unavailable         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. LLM Provider (Ollama)                                   │
│    │                                                         │
│    │ Request:                                                │
│    │ {                                                       │
│    │   model: "llama3:8b",                                  │
│    │   prompt: "Résume ce document: [content]",             │
│    │   max_tokens: 500                                      │
│    │ }                                                       │
│    │                                                         │
│    │ Stream response token by token                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Validation Sécurité                                      │
│    │                                                         │
│    │ - Check output for PII (emails, phones)                │
│    │ - Check for sensitive data                             │
│    │ - Sanitize if necessary                                │
│    │ - Log to audit trail                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. Response Assembly                                       │
│    │                                                         │
│    │ Assemble final response:                               │
│    │ {                                                       │
│    │   status: "success",                                   │
│    │   content: "Résumé généré...",                         │
│    │   metadata: {                                          │
│    │     model: "llama3:8b",                               │
│    │     tokens: 450,                                      │
│    │     duration_ms: 3200,                                │
│    │     cost: 0.00                                        │
│    │   }                                                    │
│    │ }                                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. CLI Output                                              │
│    │                                                         │
│    │ Receive response from NATS                             │
│    │ Display to user:                                       │
│    │                                                         │
│    │ ◆ Résumé                                               │
│    │                                                         │
│    │ [Résumé généré par Llama 3 8B]                        │
│    │                                                         │
│    │ ⏱ 3.2s  |  Coût: $0.00                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. Système de Mémoire

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM                             │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Memory Manager                            │ │
│  └───────────────────────┬───────────────────────────────┘ │
│                          │                                  │
│          ┌───────────────┼───────────────┐                │
│          │               │               │                 │
│          ▼               ▼               ▼                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │  Working     │ │   Long-term  │ │   Vector     │      │
│  │  Memory      │ │   Memory     │ │   Store      │      │
│  │  (Redis)     │ │  (PostgreSQL)│ │ (pgvector)   │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                             │
│  Working Memory:                                            │
│  - Session state (TTL: 1h)                                 │
│  - Recent context (last 100 events)                        │
│  - Module scratch space                                    │
│                                                             │
│  Long-term Memory:                                          │
│  - Event log (append-only, immutable)                      │
│  - Goals history                                           │
│  - Learned patterns                                        │
│  - State snapshots                                         │
│                                                             │
│  Vector Store:                                              │
│  - Embeddings (OpenAI, Ollama, etc.)                       │
│  - Semantic search                                         │
│  - Similarity retrieval                                    │
└─────────────────────────────────────────────────────────────┘
```

### Propriétés

1. **Immutable** : les entrées ne sont jamais modifiées
2. **Traçable** : chaque entrée a un parent (causalité)
3. **Isolée** : namespace par module
4. **Interrogeable** : recherche sémantique

---

## 12. Event Bus (NATS)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT BUS (NATS JetStream)                │
│                                                             │
│  Publishers                 Subscribers                    │
│  ┌──────────────┐          ┌──────────────┐               │
│  │    CLI       │          │   Kernel     │               │
│  └──────┬───────┘          └──────┬───────┘               │
│         │                         │                          │
│         │    ┌────────────────────┘                          │
│         │    │                                              │
│         ▼    ▼                                              │
│  ┌─────────────────────────────────────────┐               │
│  │         NATS JetStream                  │               │
│  │  ┌───────────────────────────────────┐  │               │
│  │  │  Subjects:                       │  │               │
│  │  │  - ethan.interface.<src>.<act>   │  │               │
│  │  │  - ethan.module.<name>.<type>    │  │               │
│  │  │  - ethan.capability.<name>       │  │               │
│  │  │  - ethan.memory.<action>         │  │               │
│  │  │  - ethan.system.<action>         │  │               │
│  │  └───────────────────────────────────┘  │               │
│  │  ┌───────────────────────────────────┐  │               │
│  │  │  Guarantees:                     │  │               │
│  │  │  - At-least-once delivery        │  │               │
│  │  │  - Ordering per subject          │  │               │
│  │  │  - Durability (JetStream)        │  │               │
│  │  │  - Replay capability             │  │               │
│  │  └───────────────────────────────────┘  │               │
│  └─────────────────────────────────────────┘               │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Module A   │  │   Module B   │  │   Module C   │     │
│  │ (subscriber) │  │ (subscriber) │  │ (subscriber) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Garanties

| Garantie | Implémentation |
|----------|----------------|
| **At-least-once** | NATS durable subscriptions |
| **Ordre par sujet** | NATS ordering par subject |
| **Pas de perte** | JetStream + backup PostgreSQL |
| **Replay** | Events rejouables depuis NATS |

---

## 13. LLM Router

### Principe

> Les LLM sont des **moteurs de raisonnement**, pas des décideurs.

Ils proposent. ETHAN décide.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM ROUTER                                │
│                                                             │
│  Request                                                    │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Complexity Analyzer                      │  │
│  │  - Analyse la requête                                 │  │
│  │  - Score 0.0 (simple) à 1.0 (complexe)               │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Provider Selector                        │  │
│  │  - Filtrer par capabilities                          │  │
│  │  - Vérifier disponibilité                            │  │
│  │  - Calculer coût estimé                              │  │
│  │  - Choisir le meilleur provider                      │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LLM Provider                             │  │
│  │  - OpenAI / Anthropic / Google / Ollama / etc.       │  │
│  │  - Generate / Stream                                 │  │
│  │  - Track usage (tokens, cost, latency)               │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  Response                                                   │
└─────────────────────────────────────────────────────────────┘
```

### Providers supportés

| Provider | Type | Modèles | Cas d'usage |
|----------|------|---------|-------------|
| **OpenAI** | Cloud | GPT-4o, GPT-4 Turbo | Complex reasoning, vision |
| **Anthropic** | Cloud | Claude 3.5 Sonnet, Claude 3 Opus | Long context, safety |
| **Google** | Cloud | Gemini 1.5 Pro, Gemini 2.0 | Multimodal, long context |
| **Ollama** | Local | Llama 3, Mistral, Gemma | Privacy, offline, cost |
| **vLLM** | Local | Llama, Mixtral | High throughput, batch |
| **SGLang** | Local | Multi-model | Structured generation |
| **llama.cpp** | Local | GGUF models | Edge devices, low RAM |
| **LiteLLM** | Agrégateur | Tous | Unified API, fallback |

### Routing Strategy

```
Requête simple (chat basique)
    → Ollama (Llama 3 8B) — gratuit, rapide

Requête complexe (raisonnement)
    → Claude 3.5 Sonnet — qualité maximale

Requête avec vision (image)
    → GPT-4o — multimodal

Requête longue (10k+ tokens)
    → Gemini 1.5 Pro — long context

Fallback si provider down
    → LiteLLM (agrège plusieurs providers)
```

---

## 14. Security Layer

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYER                            │
│                                                             │
│  Event entrant                                              │
│    │                                                        │
│    ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Input Validation                                  │  │
│  │  - Schema validation (JSON Schema)                    │  │
│  │  - Signature verification                             │  │
│  │  - Size limits                                        │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. Permission Check                                  │  │
│  │  - RBAC par capability                                │  │
│  │  - Module permissions                                 │  │
│  │  - User permissions                                   │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  3. Policy Engine                                     │  │
│  │  - Rate limiting                                      │  │
│  │  - Quotas                                             │  │
│  │  - Business rules                                     │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. Audit Log                                         │  │
│  │  - Log to PostgreSQL                                  │  │
│  │  - Trace (correlation_id, span_id)                    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  Event autorisé → Kernel                                    │
└─────────────────────────────────────────────────────────────┘
```

### Principes

1. **Zero Trust** : aucun événement n'est fiable par défaut
2. **Least Privilege** : permissions minimales
3. **Explicit Allow** : tout ce qui n'est pas autorisé est interdit
4. **Audit Everything** : toute action est tracée

---

## 15. CLI Interface

### Principe

> La CLI est un **thin client**. Elle ne contient aucune logique métier.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI (ethan)                               │
│                                                             │
│  $ ethan chat "résume ce document"                          │
│    │                                                         │
│    │ 1. Parse arguments                                     │
│    │ 2. Validate input                                      │
│    │ 3. Create event                                        │
│    │ 4. Publish to NATS (or call local socket)              │
│    │ 5. Wait for response (blocking or streaming)           │
│    │ 6. Display result                                      │
│    │                                                         │
│    │ C'est tout.                                             │
└─────────────────────────────────────────────────────────────┘
```

### Commandes

| Commande | Description |
|----------|-------------|
| `ethan chat <message>` | Conversation interactive |
| `ethan run <task>` | Exécuter une tâche |
| `ethan status` | Afficher le statut du système |
| `ethan logs` | Voir les logs |
| `ethan memory search <query>` | Rechercher dans la mémoire |
| `ethan skill list` | Lister les skills |
| `ethan skill run <skill>` | Exécuter une skill |
| `ethan config` | Afficher/modifier la config |
| `ethan daemon start` | Démarrer le daemon |
| `ethan daemon stop` | Arrêter le daemon |
| `ethan daemon status` | Statut du daemon |

### Contrat

1. **Pas de logique métier** : la CLI ne décide rien
2. **Pas d'appel direct aux modules** : tout passe par le Core
3. **Émission d'événements** : toute action = événement NATS
4. **Observation de l'état** : lecture via API Core

---

## 16. Architecture Docker

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER NETWORK                            │
│                    ethan-network                            │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   ethan-ui   │         │  ethan-api   │                │
│  │  (frontend)  │         │   (FastAPI)  │                │
│  └──────┬───────┘         └──────┬───────┘                │
│         │                        │                          │
│         │    ┌───────────────────┘                          │
│         │    │                                              │
│         ▼    ▼                                              │
│  ┌─────────────────────────────────────────┐               │
│  │         ethan-core (daemon)             │               │
│  │         - Kernel (Go)                   │               │
│  │         - Orchestrator (Python)         │               │
│  │         - Modules                       │               │
│  └──────────────────┬──────────────────────┘               │
│                     │                                       │
│  ┌──────────────────┼──────────────────────┐               │
│  │                  │                      │                │
│  │    ┌─────────────┴──────────┐          │                │
│  │    │                        │          │                │
│  │    ▼                        ▼          │                │
│  │  ┌──────────┐         ┌──────────┐    │                │
│  │  │  NATS    │         │  Redis   │    │                │
│  │  │ (event)  │         │  (cache) │    │                │
│  │  └──────────┘         └──────────┘    │                │
│  │    ┌──────────┐                       │                │
│  │    │PostgreSQL│                       │                │
│  │    │ (store)  │                       │                │
│  │    └──────────┘                       │                │
│  └───────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Services Docker

| Service | Image | Port | Rôle |
|---------|-------|------|------|
| `ethan-core` | Custom | 8080 | Daemon principal |
| `ethan-api` | Custom | 8000 | API REST |
| `ethan-ui` | Custom | 5173 | Interface web |
| `nats` | nats:latest | 4222 | Event bus |
| `redis` | redis:7-alpine | 6379 | Cache |
| `postgres` | postgres:16 | 5432 | Persistance |

### Volumes

| Volume | Montage | Rôle |
|--------|---------|------|
| `ethan-data` | `/var/lib/ethan` | Données persistantes |
| `ethan-config` | `/etc/ethan` | Configuration |
| `ethan-logs` | `/var/log/ethan` | Logs |
| `postgres-data` | `/var/lib/postgresql/data` | Données PostgreSQL |
| `redis-data` | `/data` | Données Redis |

---

## 17. Critique Architecturale

### 17.1 Points Forts

1. **Séparation des préoccupations** : chaque module a une responsabilité unique
2. **Event-driven** : découplage fort, résilience
3. **State externalisé** : pas d'état in-memory critique
4. **Multi-provider LLM** : pas de dépendance à un fournisseur
5. **Systemd** : intégration Linux native, auto-restart
6. **Docker** : isolation, reproductibilité
7. **Zero Trust** : sécurité par défaut

### 17.2 Faiblesses et Risques

| # | Faiblesse | Impact | Mitigation |
|---|-----------|--------|------------|
| 1 | **SPOF Orchestrator** | Si l'orchestrateur crash, tout s'arrête | Réplicable, load balancer |
| 2 | **Dépendance NATS** | Si NATS est down, le système est aveugle | Clustering NATS, fallback in-memory |
| 3 | **Latence accrue** | Chaque événement passe par le bus | Cache, fast path |
| 4 | **Complexité debugging** | Tracer un flux à travers 8 modules | Outillage, traces distribuées |
| 5 | **Overhead sécurité** | Chaque événement est validé | Fast path, cache permissions |
| 6 | **Multi-langages** | Go + Python + Rust = complexité | Justifié par les use cases |

### 17.3 Dette Architecturale

1. **Pas de tests d'intégration** : comment tester un système distribué ?
2. **Pas de stratégie de migration de schéma** : que faire quand un événement change ?
3. **Pas de secret management** : où sont stockés les API keys ?
4. **Pas de monitoring** : comment savoir ce qui se passe en production ?
5. **Pas de backup strategy** : comment restaurer après un crash ?

### 17.4 Incohérences

| # | Incohérence | Description |
|---|-------------|-------------|
| 1 | **Kernel Go vs Python** | Le kernel est en Go, mais `core/` est en Python. Comment communiquent-ils ? |
| 2 | **Event Bus par défaut** | NATS est mentionné, mais `core/bus/` implémente InMemoryBus. Quel est le backend par défaut ? |
| 3 | **Modules vs Agents** | `core/modules/` et `core/agents/` coexistent. Quelle est la différence ? |

---

## 18. Actions Requises (BLOCKER)

### Avant toute implémentation

1. **Définir l'interface Kernel Go ↔ Python**
   - Comment le kernel Go appelle-t-il l'Orchestrator Python ?
   - gRPC ? HTTP ? Shared memory ?

2. **Choisir le backend Event Bus par défaut**
   - NATS pour V1 ? InMemory pour tests ?
   - Comment basculer entre backends ?

3. **Définir Module vs Agent**
   - Un module est-il un agent ?
   - Un agent est-il un module ?
   - Quelle est la différence ?

4. **Définir Event Schema Governance**
   - Comment créer un nouvel événement ?
   - Comment versionner un événement ?
   - Comment migrer un événement ?

5. **Définir Module Contract**
   - Interface standard ?
   - Permissions ?
   - Dépendances ?

6. **Définir Testing Strategy**
   - Tests unitaires (mocking du bus)
   - Tests d'intégration (bus in-memory)
   - Tests E2E (stack complète)

7. **Définir Secret Management**
   - Vault ? AWS Secrets Manager ? Docker secrets ?
   - Comment distribuer les secrets aux modules ?

---

## 19. Roadmap

### V1 (MVP) — 3 mois

- [x] Kernel Go avec routing d'événements
- [x] Event Bus NATS JetStream
- [x] 6 modules cognitifs de base
- [x] Persistance Redis + PostgreSQL
- [x] CLI fonctionnelle
- [x] API REST
- [x] 5 Skills intégrées
- [x] Tool Manager
- [x] LLM Router multi-provider
- [x] Sécurité basique

### V2 (Autonomie) — 6 mois

- [ ] Goal Manager avec évaluation automatique
- [ ] Module Autonomy (initiative de buts)
- [ ] Module Learning (amélioration continue)
- [ ] Observabilité (traces, dashboards)
- [ ] Clustering NATS
- [ ] Redis Cluster

### V3 (Cognitive OS) — 12 mois

- [ ] Multi-utilisateurs
- [ ] Multi-tenancy
- [ ] Marketplace (plugins, skills)
- [ ] Apprentissage fédéré
- [ ] Auto-évolution

---

## Conclusion

ETHAN Core Daemon est le **cerveau vivant du système**.

C'est un daemon systemd permanent qui :
- Orchestre des modules autonomes
- Maintient un état persistant
- Route des événements
- Prend des décisions
- Apprend de ses actions

Ce n'est pas une application. C'est un runtime.

Ce n'est pas un chatbot. C'est un OS cognitif.

**ETHAN mérite d'être construit sur des bases solides.**

---

**Document officiel — ETHAN Core Daemon Specification**  
**Version** : 1.0.0  
**Date** : Juin 2026  
**Maintenu par** : Architecture Team