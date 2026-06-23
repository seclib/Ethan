# ETHAN — System Overview

Master reference document for the ETHAN Cognitive Runtime.

---

## 1. Complete Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                        Interfaces Layer                            │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │   CLI    │  │   Web    │  │ VSCode   │  │     API          │  │
│  │  ethan   │  │  UI      │  │ Bridge   │  │  (REST/WS)       │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │             │            │                     │           │
│       └─────────────┴────────────┴─────────────────────┘           │
│                        │                                           │
│                        ▼                                           │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ Event Ingest Layer                                        │   │
│  │  • Normalize input → Intent Object                        │   │
│  │  • Emit `command.executed`, `ui.interaction`, etc.         │   │
│  └───────────────────────────────────────────────────────────┘   │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                        Event Bus (NATS)                            │
│                                                                   │
│  Subjects: ethan.module.<name>.<event_type>                       │
│  Guarantees: at-least-once, ordered per subject                   │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                         Kernel Layer                              │
│                                                                   │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────────┐   │
│  │   Router   │  │ Scheduler  │  │ State Manager             │   │
│  └────────────┘  └────────────┘  └──────────────────────────┘   │
│  ┌────────────────────┐  ┌──────────────────────────────────┐   │
│  │ Capability Registry│  │ Goal Manager                     │   │
│  │ • Module contracts  │  │ • Active goals                  │   │
│  │ • Dependency checks│  │ • Evaluation events             │   │
│  │ • Conflict detect  │  └──────────────────────────────────┘   │
│  └────────────────────┘                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Planner + Executor                                        │   │
│  │ • Goal → Task decomposition                               │   │
│  │ • Capability resolution                                   │   │
│  │ • Task assignment + retry                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Telemetry                                                 │   │
│  │ • Module health                                            │   │
│  │ • Event latency                                            │   │
│  │ • Error rates                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                        Modules Layer                               │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐     │
│  │Executive │ │ Planner  │ │  Memory  │ │ Reflective       │     │
│  │• Goals   │ │• decompose│ │• store   │ │• evaluate        │     │
│  │• plans   │ │• tasks   │ │• recall  │ │• outcomes        │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────────────┐     │
│  │ Autonomy │ │ Learning │ │ Metacognition                 │     │
│  │• initiate│ │• patterns│ │• self-assessment              │     │
│  └──────────┘ └──────────┘ └──────────────────────────────┘     │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Persistence Layer                              │
│                                                                   │
│  ┌─────────────────────────┐        ┌─────────────────────────┐   │
│  │         Redis            │        │     PostgreSQL           │   │
│  │  • Live state            │        │  • Event log (append)   │   │
│  │  • Active goals         │        │  • Command history      │   │
│  │  • Recent events        │        │  • Module snapshots     │   │
│  │  • Cache (TTL)          │        │  • Goals / outcomes     │   │
│  │  • Working memory       │        │  • Embeddings (pgvector)│   │
│  └─────────────────────────┘        └─────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer Breakdown

### 2.1 Interfaces Layer
| Interface | Implementation | Transport | Purpose |
|-----------|---------------|-----------|---------|
| CLI | `cli/` | local exec | Primary user interface |
| Web UI | `ethan-ui/` | HTTP/SSE | Browser-like terminal UI |
| VSCode | `frontend/` (Tauri) | TCP/WebSocket | Editor integration |
| API | `api/` | HTTP/REST | Machine-readable access |
| Shell | `ethan-shell/` | local exec | Bash/Zsh/Fish completion |

**Rule**: No interface contains business logic. All emit events, all observe state.

### 2.2 Event Bus Layer
- **Technology**: NATS with JetStream
- **Subjects**: `ethan.module.<name>.<event_type>`
- **Patterns**: pub/sub, request/reply, queue groups
- **Guarantees**: at-least-once delivery, per-subject ordering

### 2.3 Kernel Layer
| Component | Responsibility |
|-----------|---------------|
| Router | Dispatch events to subscribed modules |
| Scheduler | Time-based and condition-based execution |
| State Manager | Redis reads/writes, PostgreSQL commits |
| Capability Registry | Module contracts, validation, queries |
| Goal Manager | Track and evaluate active goals |
| Planner | Decompose goals into task DAGs |
| Executor | Assign tasks, track outcomes, retry |
| Telemetry | Health, latency, error metrics |

**Rule**: Kernel does not reason. It does not execute business logic.

### 2.4 Modules Layer
Each module is an independent process:
- **Executive**: goal coordination, priority management
- **Planner**: task decomposition via capability registry
- **Memory**: store/recall/context/embeddings
- **Reflective**: outcome evaluation, self-assessment
- **Autonomy**: goal initiation, self-directed action
- **Learning**: pattern extraction, improvement proposals
- **Metacognition**: system self-awareness, resource management

**Rule**: Modules do not call each other. They emit events.

### 2.5 Persistence Layer
| Store | Purpose | Features |
|-------|---------|----------|
| Redis | Live state | TTL, atomic ops, pub/sub |
| PostgreSQL | Permanent state | JSONB, pgvector, event sourcing |

**Data**:
- Events (append-only)
- Goals (state machine)
- Tasks (DAG state)
- Memory entries (immutable)
- Embeddings (vector similarity)

---

## 3. Data Flow: Request Lifecycle

### 3.1 Synchronous (CLI / API)

```
User Input
    │
    ▼
Interface → Normalize → Intent Object
    │
    ▼
Interface → Publish `command.executed` → NATS
    │
    ▼
Kernel Router → Receive event
    │
    ▼
Kernel → Query Capability Registry
    │
    ▼
Kernel → Dispatch to subscribed modules
    │
    ▼
Modules → Execute → Write state to Redis
    │
    ▼
Modules → Publish result events → NATS
    │
    ▼
Kernel → Persist state transitions → PostgreSQL
    │
    ▼
Interface → Observe state change (polling or push)
    │
    ▼
Interface → Present result to user
```

### 3.2 Asynchronous (Autonomous)

```
Module detects condition / Goal evaluation triggers
    │
    ▼
Module → Publish event autonomously → NATS
    │
    ▼
Kernel → Route to interested modules
    │
    ▼
Pipeline executes (no user involvement)
    │
    ▼
State updates propagate (Redis + PostgreSQL)
    │
    ▼
Goal Manager → Evaluate progress → Emit updates
```

### 3.3 Capability Resolution Flow

```
Planner receives `goal.created`
    │
    ▼
Planner → Query Capability Registry
    │
    ▼
Registry → Return matching capabilities
    │
    ▼
Planner → Decompose goal → `task.created` + capability assignment
    │
    ▼
Executor → Resolve task to module via capability
    │
    ▼
Executor → `task.assigned` → module
    │
    ▼
Module → `task.completed` / `task.failed`
    │
    ▼
Executor → `task.finished` → Goal Manager
```

---

## 4. Interface Relationships

### 4.1 CLI ↔ Kernel
- CLI publishes `command.executed` events
- CLI polls `/state` for responses
- No direct module access

### 4.2 Web UI ↔ Kernel
- Web UI connects to API via HTTP/SSE
- API translates UI events to NATS events
- UI observes state via API polling

### 4.3 VSCode ↔ Kernel
- Extension connects to API only
- Extension sends `ethan.send`, `ethan.focus`
- Extension observes `/state`, `/goals`, `/tasks`
- Zero intelligence in extension

### 4.4 API ↔ Kernel
- API server (`api/`) bridges HTTP ↔ NATS
- Endpoints emit events on bus
- Endpoints query state from Redis/PostgreSQL

---

## 5. Configuration Hierarchy

```
1. CLI arguments (highest)
   ↓
2. Environment variables (ETHAN_*)
   ↓
3. ~/.config/ethan/config.local.json
   ↓
4. ~/.config/ethan/config.json
   ↓
5. Defaults (lowest)
```

**Storage**: `~/.config/ethan/`

---

## 6. Plugin System

### 6.1 Types
- **CLI plugins** — add commands, run in CLI process
- **Module plugins** — add capabilities, run as separate processes

### 6.2 Discovery
- Built-in: `cli/plugins/`, `modules/*`
- User: `~/.local/share/ethan/plugins/<name>/`

### 6.3 Contract
```python
ETHAN_PLUGIN = {
    "name": "plugin-name",
    "version": "1.0.0",
    "api_version": "2",
    "commands": {...},      # CLI plugins
    "capabilities": [...],  # Module plugins
    "dependencies": []
}
```

---

## 7. Non-Functional Properties

### 7.1 Reliability
- Module restarts: automatic, exponential backoff
- State persistence: all critical writes atomic
- Event loss: NATS durable + PostgreSQL backup

### 7.2 Observability
- Structured logs: 500-entry ring buffer (CLI) + full history (PostgreSQL)
- Event telemetry: timing, module health, errors
- Goal lifecycle: full audit trail

### 7.3 Security
- No secrets in code or events
- Secrets via env vars or Docker secrets
- Namespace isolation on state access
- No silent state mutations

### 7.4 Maintainability
- Module replacement: no kernel changes
- Interface replacement: no module changes
- Plugin install: no code modification

---

## 8. Deployment Topologies

### 8.1 Development (Single-node Docker Compose)
```
Host Machine
  ├── Docker Compose
  │   ├── NATS
  │   ├── Redis
  │   ├── PostgreSQL
  │   ├── Kernel
  │   ├── Modules (x6)
  │   └── API
  └── CLI / Web UI
```

### 8.2 Production (Systemd + Docker)
- Systemd user service manages Docker Compose
- Auto-restart on failure
- Journald for logs
- CLI in `~/.local/bin/`

---

## 9. Success Criteria

1. Adding a module requires no kernel changes
2. Adding an interface requires no module changes
3. System state survives full restart
4. A plugin can be installed non-developer users
5. Multiple LLM providers are swappable by config

---

## 10. Key File Locations

| Component | Path |
|-----------|------|
| CLI | `cli/` |
| Core services | `cli/core/` |
| Commands | `cli/commands/` |
| Registry | `cli/registry.py`, `kernel/registry/` |
| Capabilities | `kernel/registry/capability.go` |
| Planner | `kernel/planner/` |
| Memory | `cli/core/memory.py`, `modules/memory/` |
| Event bus | `kernel/bus/` |
| API | `api/` |
| Web UI | `ethan-ui/` |
| VSCode | `frontend/` (Tauri) |
| Shell | `ethan-shell/` |
| Systemd | `cli/systemd/` |
| Plugins | `cli/plugins/`, `modules/*/capabilities.py` |
| Config | `cli/core/config.py`, `~/.config/ethan/` |
| Logs | `cli/core/logging.py`, `~/.ethan/logs.json` |
| Daemon | `cli/core/daemon.py` |