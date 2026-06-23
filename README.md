# ETHAN — Cognitive Runtime

ETHAN is **not an AI assistant**. It is a distributed cognitive runtime — a system designed to run autonomous cognitive processes, orchestrate reasoning pipelines, and manage long-term goals.

ETHAN does not wait for prompts. It observes, reflects, and acts.

---

## What ETHAN Is

A **Cognitive Runtime** is a platform that hosts, schedules, and manages cognitive modules — small, independent programs that each perform a specific reasoning or perception task. These modules communicate through an event bus, persist state externally, and run continuously.

ETHAN provides the substrate. Modules provide the intelligence.

### Key properties

- **Event-driven** — all communication goes through an event bus; no direct module-to-module calls
- **State externalized** — Redis for live state, PostgreSQL for persistent state; no in-memory critical state
- **Kernel is an orchestrator** — the kernel routes events and maintains system state; it does not reason, decide strategy, or contain business logic
- **LLM-agnostic** — the system supports multiple providers (OpenAI, Anthropic, Ollama) and treats LLMs as replaceable inference engines
- **Observable** — every event is logged; the learning engine evaluates outcomes without modifying system state

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│                    Interfaces                       │
│  CLI    Web UI    VSCode    API    Desktop (Tauri)   │
└──────────┬─────────────────────────┬──────────────┘
           │                         │
           ▼                         ▼
┌────────────────────────────────────────────────────┐
│               Event Bus (NATS)                      │
├────────────────────────────────────────────────────┤
│                    Kernel                            │
│  Registry  Scheduler  State  Telemetry  Goals       │
├──────────┬──────────┬──────────┬───────────────────┤
│  Modules  │  Modules │  Modules │  Modules         │
│ Executive │ Planner  │ Memory   │ Reflective       │
│ Autonomy  │ Learning │ MetaCog  │ & more           │
└──────────┴──────────┴──────────┴───────────────────┘
┌────────────────────────────────────────────────────┐
│                 Persistence                         │
│  PostgreSQL (permanent)    Redis (live state)       │
└────────────────────────────────────────────────────┘
```

### Core components

| Component | Role |
|-----------|------|
| **Kernel** | Routes events, maintains system state, schedules modules |
| **Modules** | Independent cognitive units (executive, planner, memory, reflective, autonomy, learning, metacognition) |
| **Event Bus** | NATS — all inter-module communication |
| **State Layer** | Redis for live state; PostgreSQL for permanent storage |
| **Interfaces** | CLI, Web UI, VSCode extension, REST API, Tauri desktop app |

---

## Interfaces

### CLI (`cli/`)

The primary interface — a Unix-style toolchain:

```bash
ethan chat              # Interactive session
ethan status            # System state (online/mode/goal)
ethan run <message>     # One-shot inference
ethan logs              # View structured logs
ethan memory            # Command history
ethan daemon            # Background cache daemon
ethan plugin            # Plugin management
ethan config            # Configuration
ethan service           # systemd integration
```

The CLI is a **thin client** — zero business logic. All intelligence runs in Docker.

### Web UI (`ethan-ui/`)

Textual interface built with Textual — runs in any terminal with a browser-based chat view.

### VSCode Extension (`frontend/`)

Tauri-based desktop integration.

### API

REST API at `http://localhost:8000`:
- `POST /message` — send a message
- `GET /state` — system state
- `GET /health` — health check

---

## Principles

### Separation of concerns

Modules do not call each other. They emit events. The kernel routes them. No module knows how another module works internally.

### Persistence

All critical state is stored in PostgreSQL or Redis. No module holds irreversible state in memory. Restarting a module is safe.

### Modularity

Every module is an independent process. Modules can be added, removed, or replaced without touching the kernel.

### Observability

Every event, decision, and action is logged. The learning engine analyzes outcomes without modifying system state — it proposes improvements; the kernel decides whether to apply them.

### Safety

No secrets in code. No silent state mutations. No module can bypass the event bus.

---

## Getting Started

### Prerequisites

- Docker
- Python 3.11+
- curl

### Start ETHAN

```bash
git clone <repo>
cd ethan
docker compose up -d
```

### Install the CLI

```bash
bash cli/install.sh
export PATH="$HOME/.local/bin:$PATH"
ethan help
```

### Verify

```bash
ethan status        # Should show ONLINE
ethan chat          # Start interacting
```

---

## Project structure

```
cli/                  # Unified CLI (command registry, core services, commands)
core/                 # Core SDK (capabilities, providers, safety)
kernel/               # Kernel (event bus, state, registry, scheduler, goals)
modules/              # Cognitive modules (executive, planner, memory, reflective)
api/                  # REST API server
ethan-ui/             # Terminal-based Web UI
deploy/               # Docker, systemd, Prometheus, Grafana configs
engineering/          # RFCs, ADRs, architecture docs
docs/                 # Documentation (MkDocs)
plugins/              # Core plugin system
tests/                # Test suite
```

---

## vs Chatbots / AI Assistants

| | Chatbot / AI Assistant | ETHAN |
|---|---|---|
| **Interaction** | Prompt → Response | Event-driven, autonomous |
| **State** | Stateless or session-only | Persistent (PostgreSQL + Redis) |
| **Intelligence** | Monolithic LLM call | Distributed module pipelines |
| **Replaceability** | Tied to one model | LLM-agnostic |
| **Observability** | Black box | Every event logged and analyzed |
| **Extensibility** | Plugin API | Module system with event bus |

ETHAN is not a chatbot with plugins. It is a runtime that runs cognitive processes.

---

## License

Open-source. See [LICENSE](LICENSE).