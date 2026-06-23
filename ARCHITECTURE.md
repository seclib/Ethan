# ETHAN — System Architecture

## 1. System Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         Interfaces                             │
│  ┌──────┐ ┌─────────┐ ┌──────┐ ┌────────┐ ┌───────────────┐  │
│  │ CLI │ │ Web UI  │ │ VSC │ │  API   │ │ Shell (ESIL)  │  │
│  └──┬───┘ └────┬────┘ └──┬───┘ └───┬────┘ └──────┬────────┘  │
│     │          │         │        │             │             │
│     └──────────┴─────────┴────────┴─────────────┘             │
│                        │                                       │
│                        ▼                                       │
│                 ┌──────────────┐                               │
│                 │ Event Ingest │                               │
│                 └──────┬───────┘                               │
└────────────────────────┼───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                      Event Bus (NATS)                          │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                           Kernel                               │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────────┐  │
│  │  Router    │  │ Scheduler  │  │ State Manager            │  │
│  └────────────┘  └────────────┘  └─────────────────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────────┐  │
│  │ Capability │  │ Goal Mgr   │  │ Telemetry               │  │
│  │ Registry   │  │            │  │                         │  │
│  └────────────┘  └────────────┘  └─────────────────────────┘  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                         Modules                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Executive│ │ Planner  │ │  Memory  │ │ Reflective       │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────────────┐  │
│  │ Autonomy │ │ Learning │ │ Metacognition                 │  │
│  └──────────┘ └──────────┘ └──────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                      Persistence Layer                         │
│  ┌─────────────────┐              ┌─────────────────────────┐  │
│  │      Redis      │              │    PostgreSQL           │  │
│  │  (live state)   │              │  (events, state, goals) │  │
│  └─────────────────┘              └─────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Breakdown

### 2.1 Kernel

The kernel is the central orchestrator. It is a Go binary that manages module lifecycles, routes events, and maintains system state.

**Components:**

| Component | Responsibility |
|-----------|---------------|
| **Router** | Receives events from NATS; dispatches to subscribed modules based on capability declarations |
| **Scheduler** | Time-based and condition-based task execution |
| **State Manager** | Reads/writes system state to Redis; commits state transitions to PostgreSQL |
| **Capability Registry** | Stores module capability declarations; validates compatibility at registration |
| **Goal Manager** | Tracks active goals; emits goal-evaluation events |
| **Telemetry** | Collects module health, event latency, error rates |

**Key constraints:**

- The kernel does not perform inference
- The kernel does not execute module business logic
- The kernel does not interpret event payloads beyond routing metadata

### 2.2 Memory

Memory is a distributed system with two tiers.

**Working Memory (Redis):**

- Active session state
- Current conversation context
- Recent event cache (last N events)
- Module scratch space (ephemeral)

**Long-term Memory (PostgreSQL):**

- Event log (append-only)
- Goal history and outcomes
- Learned patterns and preferences
- Module state snapshots

**Memory Modules:**

- `memory` — core storage and retrieval
- `context` — assembles context for module consumption
- `vector` — semantic similarity (via pgvector or external provider)

**Properties:**

- All memory entries are immutable once persisted
- Updates create new entries with parent references
- No module directly modifies another module's memory keys

### 2.3 Planner

The planner decomposes high-level goals into executable tasks.

**Responsibilities:**

- Receives `goal.created` or `goal.updated` events
- Decomposes goals into a directed acyclic graph (DAG) of tasks
- Emits `task.created` events for each sub-task
- Adjusts plan based on task outcomes

**Inputs:**

- Goal description and constraints
- Available module capabilities
- Historical success rates (from memory)

**Outputs:**

- Task DAG with dependencies
- Execution schedule

### 2.4 Capabilities

A capability is a versioned contract that declares what a module can do.

**Schema:**

```json
{
  "name": "llm.inference",
  "version": "1.0.0",
  "inputs": ["llm.request"],
  "outputs": ["llm.response"],
  "state_reads": ["llm:config"],
  "state_writes": ["llm:metrics"],
  "dependencies": ["openai.api_key"]
}
```

**Registry enforcement:**

- No two modules may write to the same state key (unless explicitly declared as shared)
- Missing dependencies block module registration
- Version mismatches generate warnings but do not block registration

### 2.5 Interfaces

Interfaces are thin clients. They translate user actions into events and observe system state.

| Interface | Location | Transport | Event Source |
|-----------|----------|-----------|--------------|
| CLI | `cli/` | local exec | `command.executed` |
| Web UI | `ethan-ui/` | HTTP/SSE | `ui.interaction` |
| API | `api/` | HTTP/REST | `http.request` |
| VSCode | `frontend/` | TCP/WebSocket | `extension.action` |
| Shell | `ethan-shell/` | local exec + completion | none (proxy through CLI) |

**Interface contract:**

- No business logic
- No direct module calls
- All state reads go through the state API
- All actions emit events

---

## 3. Data Flow: Request Lifecycle

### 3.1 Synchronous Path (CLI / API)

```
1. User action
   ↓
2. Interface normalizes input → Intent Object
   ↓
3. Interface emits event on NATS
   ↓
4. Kernel receives event; looks up subscriptions in capability registry
   ↓
5. Kernel forwards event to matching modules
   ↓
6. Modules execute; write state to Redis; emit result events
   ↓
7. Kernel persists state transitions to PostgreSQL
   ↓
8. Interface observes state change (polling or push)
   ↓
9. Interface presents result to user
```

### 3.2 Asynchronous Path (Autonomous)

```
1. Module detects condition or goal evaluation triggers
   ↓
2. Module emits event autonomously
   ↓
3. Kernel routes event to interested modules
   ↓
4. Pipeline executes without user involvement
   ↓
5. State updates propagate
   ↓
6. Goal manager evaluates progress; emits updates
```

### 3.3 Failure Handling

- Module crash → kernel restarts module (configurable policy)
- Event bus partition → kernel queues locally until bus recovers
- State inconsistency → PostgreSQL is source of truth; Redis rebuilds on startup
- Capability violation → kernel rejects event and logs violation

---

## 4. Communication Model

### 4.1 Event Bus (NATS)

All inter-module communication uses NATS.

**Subjects:**

```
ethan.module.<name>.<event_type>
```

**Example:**

```
ethan.module.executive.goal.created
ethan.module.planner.task.decomposed
ethan.module.memory.entry.stored
```

**Guarantees:**

- At-least-once delivery
- Ordering per subject
- No guaranteed ordering across subjects

### 4.2 State API (Redis)

Modules read and write state via Redis keys with namespace isolation.

**Namespace convention:**

```
<module_name>:<key>
```

**Example:**

```
memory:entry:abc123
planner:task:456
executive:goal:789
```

### 4.3 Persistence API (PostgreSQL)

- Event sourcing — every state transition is an event stored in `events` table
- Snapshots — periodic state snapshots in `snapshots` table
- Goals — persistent goal objects in `goals` table
- Learning outcomes — in `outcomes` table

---

## 5. Plugin System

### 5.1 Architecture

Plugins extend ETHAN without modifying core code. There are two plugin types:

- **CLI plugins** — add commands to the CLI; run in CLI process
- **Module plugins** — add cognitive modules; run as separate processes

### 5.2 Discovery

At startup, the CLI scans:

1. `cli/plugins/` (built-in)
2. `~/.local/share/ethan/plugins/` (user-installed)

Module plugins are discovered by the kernel at container/module startup.

### 5.3 Validation

Plugin metadata (`ETHAN_PLUGIN`) is validated:

- `api_version` must match current ETHAN API version
- Required fields: `name`, `version`, `commands` or `capabilities`
- Dependencies are checked (for CLI plugins, optional pip install)

### 5.4 Isolation

- CLI plugins share CLI process; cannot access other plugins' state
- Module plugins are separate processes with capability-based access control
- Plugins cannot modify core modules

### 5.5 Lifecycle

```
Install → Validate → Register → Load → Execute → Unregister → Remove
```

---

## 6. Deployment Topology

### 6.1 Single-Node (Development)

```
┌──────────────────────────────────────┐
│         Host Machine                 │
│  ┌────────┐  ┌────────────────────┐ │
│  │ Docker │  │  CLI / Web UI      │ │
│  │ Compose│  │  (localhost)       │ │
│  └────────┘  └────────────────────┘ │
└──────────────────────────────────────┘
```

### 6.2 Production (Systemd + Docker)

- Systemd user service (`ethan.service`) manages Docker Compose stack
- Automatic restart on failure
- Journald for logs
- CLI installed to `~/.local/bin/ethan`

### 6.3 Configuration Hierarchy

1. CLI arguments (highest priority)
2. Environment variables (`ETHAN_*`)
3. User config file (`~/.config/ethan/config.json`)
4. Local override (`~/.config/ethan/config.local.json`)
5. Defaults (lowest priority)

---

## 7. Non-Functional Requirements

### 7.1 Reliability

- Module restarts: automatic, with exponential backoff
- State persistence: all critical state writes are atomic (Redis transactions or DB writes)
- Event loss: NATS durable subscriptions; events persisted to PostgreSQL

### 7.2 Observability

- Structured logs (500-entry ring buffer in CLI; full history in PostgreSQL)
- Event telemetry: timing, module health, error rates
- goal lifecycle tracking

### 7.3 Security

- No secrets in code or events
- All secrets via environment variables or Docker secrets
- Module capabilities enforce namespace isolation on state access
- No silent state mutations

### 7.4 Maintainability

- Module replacement requires no kernel changes
- Interface replacement requires no module changes
- Plugin installation via CLI (no code modification)