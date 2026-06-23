# RFC-0001 — ETHAN Core Architecture

**Status**: Proposed  
**Authors**: ETHAN Architecture Team  
**Date**: 2024-01-15  
**Target**: v1.0.0

---

## 1. Overview

This RFC defines the core architecture of ETHAN as a distributed cognitive runtime.

ETHAN is not an AI assistant. It is a substrate for autonomous cognition — a system that hosts, schedules, and manages independent cognitive modules which communicate through an event bus, persist state externally, and run continuously without requiring synchronous user prompts.

---

## 2. System Overview

### 2.1 Definition

ETHAN is composed of three interdependent layers:

1. **Kernel** — orchestrator; routes events, maintains state, schedules execution
2. **Modules** — independent cognitive processes; each performs a single cognitive function
3. **Interfaces** — user-facing endpoints; CLI, Web UI, API, desktop applications

### 2.2 Design Constraints

- **Event-driven only** — no direct module-to-module calls; all communication via event bus
- **State externalized** — critical state stored in Redis (live) and PostgreSQL (persistent); no in-memory critical state
- **Module independence** — each module is a standalone process with its own lifecycle
- **Kernel neutrality** — the kernel does not reason, decide strategy, or contain business logic
- **LLM replaceability** — no hard dependency on any model or provider; LLMs are treated as external inference engines

---

## 3. Cognitive Kernel

### 3.1 Responsibility

The kernel is the sole orchestrator of the runtime. Its responsibilities are:

- **Event routing** — receives events from the bus and dispatches them to subscribed modules
- **Module registry** — maintains a registry of active modules, their capabilities, and their event subscriptions
- **State management** — provides a consistent view of system state through Redis; persists state transitions to PostgreSQL
- **Lifecycle management** — starts, stops, and restarts modules; enforces resource limits
- **Scheduling** — executes time-based and event-based schedules

### 3.2 Non-responsibilities

The kernel does not:

- Perform reasoning or inference
- Execute business logic
- Make strategic decisions
- Interpret event payloads beyond routing metadata

### 3.3 Interfaces

| Interface | Protocol | Purpose |
|-----------|----------|---------|
| Event Bus | NATS | All inter-module communication |
| State API | Redis | Live state reads/writes |
| Persistence API | PostgreSQL | Event log, module state, goals |
| Registry API | gRPC/REST | Module registration, capability discovery |

---

## 4. Capability System

### 4.1 Definition

A **capability** is a typed, versioned contract that a module exposes to the kernel and other modules.

Capabilities declare:

- **Input events** — event types the module consumes
- **Output events** — event types the module emits
- **State requirements** — Redis keys or DB tables the module reads/writes
- **Dependencies** — external services or other capabilities required

### 4.2 Registry

The kernel maintains a capability registry. At startup, each module registers its capabilities. The kernel validates:

- No capability name conflicts (unless explicitly overridden)
- State key uniqueness across modules
- Required dependencies are available

### 4.3 Isolation

Capabilities are isolated by namespace. A module cannot access another module's state keys unless explicitly granted through capability declaration. This enforces separation of concerns at the infrastructure level.

---

## 5. Memory System

### 5.1 Architecture

ETHAN uses a two-tier memory model:

- **Working memory** (Redis) — fast, volatile, holds current session state, active goals, recent events
- **Long-term memory** (PostgreSQL) — persistent, stores event history, learned patterns, module states, goal history

### 5.2 Modules

The memory system itself is implemented as a set of modules:

- **Memory Module** — stores and retrieves conversation and interaction history
- **Vector Store** — semantic similarity search (via pgvector or external provider)
- **Context Manager** — assembles context for module consumption from working and long-term memory

### 5.3 Properties

- Memory is not a monolith. It is composed of independent modules with distinct concerns.
- No module directly modifies another module's memory entries; all writes go through the memory module's capabilities.
- Memory entries are immutable once persisted; updates create new entries with parent references.

---

## 6. Interface Layer

### 6.1 Principle

All interfaces are thin clients. They contain no business logic. They translate user actions into events and present system state to the user.

### 6.2 Interfaces

| Interface | Implementation | Status |
|-----------|---------------|--------|
| CLI | `cli/` — command registry, thin client | Stable |
| Web UI | `ethan-ui/` — Textual-based terminal UI | Beta |
| VSCode Extension | `frontend/` — Tauri desktop | Alpha |
| REST API | `api/` — FastHTTP server | Stable |
| Shell Integration | `ethan-shell/` — bash/zsh completion | Stable |

### 6.3 Event Mapping

Each interface maps user actions to event emissions:

- CLI command → emits `command.executed` event
- Web UI message → emits `interface.message` event
- API request → emits `http.request` event

Interfaces never call modules directly. They emit events and observe state.

---

## 7. Execution Pipeline

### 7.1 Event Flow

```
User Action → Interface → Event Bus → Kernel → Module(s) → State Update → Event Bus → Other Modules
```

### 7.2 Pipeline Stages

1. **Ingest** — interface transforms user input into a normalized event with source, timestamp, context
2. **Route** — kernel matches event to subscribed modules based on capability declarations
3. **Process** — one or more modules execute their logic; may emit additional events
4. **Persist** — state changes are written to Redis (immediate) and PostgreSQL (eventual)
5. **Respond** — interface observes state changes and presents results to user

### 7.3 Concurrency

Modules run as independent OS processes. The kernel does not serialize execution across modules. Concurrent execution is expected; state consistency is maintained through Redis atomic operations and PostgreSQL transactions.

---

## 8. Plugin Architecture

### 8.1 Discovery

ETHAN supports two plugin locations:

- **Built-in**: `cli/plugins/` and `modules/*` (shipped with repository)
- **User**: `~/.local/share/ethan/plugins/<name>/` (installed independently)

### 8.2 Plugin Contract

A plugin is a directory containing:

```
plugin.py           # Entry point — must define ETHAN_PLUGIN dict
requirements.txt    # Optional pip dependencies
README.md           # Documentation (optional)
```

The `ETHAN_PLUGIN` contract includes:

- `name` — unique identifier
- `version` — semantic version
- `api_version` — must match ETHAN's current API version
- `commands` (for CLI plugins) — mapping of command names to handlers
- `dependencies` — list of pip packages
- `capabilities` (for module plugins) — same as module capability declaration

### 8.3 Lifecycle

1. Discovery — CLI scans plugin directories at startup
2. Validation — plugin metadata is checked for API version and required fields
3. Registration — capabilities and commands are registered with the kernel and CLI
4. Isolation — plugins run in the same process as the interface (CLI plugins) or as separate processes (module plugins); no shared mutable state

### 8.4 Versioning

Plugins must declare `api_version`. Incompatible plugins are rejected at discovery with a warning. The plugin manager CLI (`ethan plugin install/remove/list`) handles installation and validation.

---

## 9. Non-Goals

The following are explicitly out of scope for this RFC:

- **Conversation UX** — ETHAN does not optimize chat experience. Interfaces may present conversation, but the system does not treat conversation as primary.
- **Single-model optimization** — ETHAN does not favor any specific LLM provider or model. Replaceability is required.
- **Real-time guarantees** — event latency is not bounded by design; the system is asynchronous.
- **Horizontal scaling** — this RFC defines a single-node runtime. Multi-node clustering is a future consideration.
- **GUI framework** — the interface layer is protocol-agnostic; no UI framework is mandated.

---

## 10. Success Criteria

1. A module can be added, removed, or replaced without kernel changes
2. An interface can be added or removed without module changes
3. System state survives full restart (power loss → PostgreSQL intact)
4. A plugin can be installed by a non-developer user via `ethan plugin install <url>`
5. Multiple LLM providers can be swapped by configuration alone

---

## 11. References

- MANIFESTO.md — philosophical foundation
- ADR-1001 — Core is not an executor
- ADR-1002 — Planner-executor separation
- ADR-1003 — Single entry intent model
- `cli/` — reference implementation of interface and plugin layers