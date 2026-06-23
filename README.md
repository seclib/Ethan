# ETHAN — Cognitive Runtime

A distributed cognitive runtime for hosting, scheduling, and managing autonomous reasoning modules. ETHAN does not answer prompts. It runs cognition.

---

## Definition

ETHAN is a substrate for autonomous intelligence. It provides the infrastructure for modules to observe, reflect, and act independently of user interaction. Intelligence is not a single model call. It is a pipeline of specialized modules that communicate through an event bus, persist state externally, and run continuously.

The system treats LLMs as replaceable inference engines. No module depends on a single provider. No interface contains business logic. The kernel orchestrates; modules reason; users observe.

---

## Architecture

```
Interfaces (CLI, Web UI, API, VSCode)
         │
         ▼
    Event Bus (NATS)
         │
         ▼
      Kernel
  ┌────┴────┐
  │ Router  │ Scheduler │ State │ Capabilities │ Goals
  └────┬────┘
       │
       ▼
    Modules
  ┌─────┴─────┐
  │ Executive │
  │ Planner   │
  │ Memory    │
  │ Reflective│
  │ Autonomy  │
  │ Learning  │
  └───────────┘
       │
       ▼
 Persistence (Redis + PostgreSQL)
```

**Kernel**: event router, module registry, state manager, scheduler. Does not reason.

**Modules**: independent processes with single responsibilities. Executive, Planner, Memory, Reflective, Autonomy, Learning.

**Interfaces**: thin clients. CLI, Web UI, VSCode extension, REST API. Zero business logic.

**State**: externalized. Redis for live state, PostgreSQL for persistent event log and memory.

---

## CLI Usage

```bash
ethan chat              # Interactive session
ethan run <message>     # One-shot inference
ethan status            # System state (mode, goal, tasks)
ethan logs              # Structured logs
ethan memory            # Command history
ethan suggest           # Smart suggestions
ethan daemon            # Background cache daemon
ethan plugin            # Plugin management
ethan config            # Configuration
ethan service           # systemd integration
```

The CLI is a command registry. Commands register themselves via `@register()`. No hardcoded dispatch. Plugins add commands automatically.

---

## Interfaces

| Interface | Location | Status |
|-----------|----------|--------|
| CLI | `cli/` | Stable |
| Web UI | `ethan-ui/` | Beta |
| VSCode | `frontend/` | Alpha |
| API | `api/` | Stable |
| Shell | `ethan-shell/` | Stable |

All interfaces are interchangeable. None is privileged. All communicate through the same event bus.

---

## Core Principles

- **Event-driven only** — no direct module-to-module calls
- **State externalized** — Redis (live) + PostgreSQL (persistent); no in-memory critical state
- **Modular capabilities** — every module exposes a versioned contract
- **Kernel neutrality** — the kernel routes events. It does not reason or contain business logic
- **Model agnostic** — LLMs are replaceable engines. No provider lock-in
- **Plugin-first** — extend without modifying core
- **Observable** — every event is logged. No silent mutations
- **Failure is normal** — modules crash. The kernel restarts. State survives.

---

## Getting Started

```bash
docker compose up -d
bash cli/install.sh
export PATH="$HOME/.local/bin:$PATH"
ethan status
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details.
See [MANIFESTO.md](MANIFESTO.md) for philosophical foundation.
See [ROADMAP.md](ROADMAP.md) for phased delivery plan.