# ETHAN Internal Event Bus — Specification

## 1. Architecture

```
Publisher ──► Event Bus (NATS) ──► Subscriber
                                          ──► Subscriber (queue group)
```

- All system communication uses events
- No direct function calls between components
- No shared memory across modules
- Events are immutable once published

---

## 2. Event Schema

### 2.1 Wire Format

```json
{
  "id": "20260623150405.123456789",
  "type": "command.executed",
  "source": "cli",
  "timestamp": "2026-06-23T15:04:05.123Z",
  "payload": {
    "cmd": "ethan status"
  },
  "context": {
    "session_id": "sess-abc-123",
    "user_id": "fatsio",
    "correlation_id": "20260623150405.123456789"
  }
}
```

### 2.2 Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | yes | Unique event ID (timestamp + nanosecond + random) |
| `type` | `string` | yes | Fully qualified event type name |
| `source` | `string` | yes | Component that emitted the event |
| `timestamp` | `string` (ISO 8601) | yes | When the event was created |
| `payload` | `object` | no | Event-specific data |
| `context` | `object` | no | Tracing metadata |

### 2.3 Go Type (`kernel/types/event.go`)

```go
type Event struct {
    ID        string
    Type      string
    Source    string
    Timestamp time.Time
    Payload   map[string]any
    Context   map[string]string
}
```

### 2.4 Python Type

```python
@dataclass
class Event:
    id: str
    type: str
    source: str
    timestamp: datetime
    payload: dict
    context: dict
```

---

## 3. Event Types — Complete Registry

### 3.1 Interface Events (source: cli, api, web, vscode)

| Type | Source | Description |
|------|--------|-------------|
| `interface.command` | cli | Raw CLI command input |
| `interface.message` | cli, api, web | User text/voice input |
| `interface.intent` | api | Structured intent object |
| `interface.interaction` | web, vscode | UI interaction |
| `interface.status` | cli, api | Status query |

### 3.2 Kernel Events (source: kernel)

| Type | Description |
|------|-------------|
| `kernel.event.validated` | Event passed validation |
| `kernel.event.rejected` | Event rejected (invalid) |
| `kernel.request.created` | Request created from event |
| `kernel.capability.required` | Capability needed for request |
| `kernel.capability.resolved` | Capability matched |

### 3.3 Registry Events (source: registry, module)

| Type | Description |
|------|-------------|
| `registry.capability.registered` | New capability declared |
| `registry.capability.removed` | Capability removed |
| `registry.module.heartbeat` | Module health check |
| `registry.dependency.missing` | Required capability absent |

### 3.4 Planner Events (source: planner)

| Type | Description |
|------|-------------|
| `planner.goal.created` | New goal received |
| `planner.goal.decomposed` | Goal broken into tasks |
| `planner.plan.created` | Execution plan generated |
| `planner.plan.rejected` | Plan could not be created |
| `planner.plan.failed` | Plan generation failed |

### 3.5 Executor Events (source: executor)

| Type | Description |
|------|-------------|
| `executor.task.assigned` | Task assigned to module |
| `executor.task.running` | Task started execution |
| `executor.task.completed` | Task finished (success) |
| `executor.task.failed` | Task finished (error) |
| `executor.task.timeout` | Task timed out |
| `executor.task.retrying` | Task retry attempt |
| `executor.plan.executing` | Plan execution started |
| `executor.plan.done` | Plan execution finished |

### 3.6 Module Events (source: module.<name>)

| Type | Description |
|------|-------------|
| `module.task.assigned` | Module received task |
| `module.task.result` | Module returned result |
| `module.capability.invoke` | Capability invocation |
| `module.capability.result` | Capability result |

### 3.7 Memory Events (source: memory)

| Type | Description |
|------|-------------|
| `memory.store.request` | Store request |
| `memory.store.complete` | Store confirmed |
| `memory.recall.request` | Recall request |
| `memory.recall.complete` | Recall results |
| `memory.context.assembled` | Context window ready |

### 3.8 Response Events (source: kernel, executor)

| Type | Description |
|------|-------------|
| `response.ok` | Request completed successfully |
| `response.error` | Request completed with error |
| `response.timeout` | Request timed out |
| `response.rejected` | Request rejected (no capability) |

### 3.9 System Events (source: kernel, boot)

| Type | Description |
|------|-------------|
| `system.boot` | Kernel started |
| `system.shutdown` | Kernel stopping |
| `system.error` | Unhandled system error |
| `system.telemetry` | Periodic metrics |

---

## 4. Subject Naming (NATS)

### 4.1 Pattern

```
ethan.<domain>.<source>.<action>
```

| Segment | Values | Example |
|---------|--------|---------|
| `domain` | `interface`, `kernel`, `registry`, `planner`, `executor`, `module`, `memory`, `response`, `system`, `capability` | `planner` |
| `source` | Component name | `planner` |
| `action` | Event type action | `plan.created` |

### 4.2 Subject Table

| Subject | Publisher | Subscribers |
|---------|-----------|-------------|
| `ethan.interface.cli` | CLI | Kernel |
| `ethan.interface.api` | API gateway | Kernel |
| `ethan.kernel.request.created` | Kernel | Planner |
| `ethan.registry.capability.registered` | Module | Registry |
| `ethan.registry.updated` | Registry | All |
| `ethan.planner.plan.created` | Planner | Executor |
| `ethan.planner.plan.failed` | Planner | Kernel |
| `ethan.executor.task.assigned` | Executor | Module |
| `ethan.executor.task.completed` | Module | Executor |
| `ethan.executor.task.failed` | Module | Executor |
| `ethan.capability.<name>` | Executor | Module |
| `ethan.capability.<name>.completed` | Module | Executor |
| `ethan.memory.store.request` | Any | Memory |
| `ethan.memory.recall.complete` | Memory | Requestor |
| `ethan.response.<correlation_id>` | Kernel | Interface |
| `ethan.ingest.error` | Ingest | Telemetry |
| `ethan.system.error` | Kernel | Telemetry |

### 4.3 Wildcard Patterns

| Pattern | Matches |
|---------|---------|
| `ethan.interface.>` | All interface events |
| `ethan.planner.*` | All planner events |
| `ethan.capability.*` | All capability invocations |
| `ethan.capability.*.completed` | All capability results |
| `ethan.>` | All system events |

---

## 5. Pub/Sub Model

### 5.1 Go Interface

```go
type EventBus interface {
    Connect(addr string) error
    Publish(subject string, data []byte)
    Subscribe(pattern string, handler func([]byte)) (int, error)
    Close()
}
```

### 5.2 Python Interface

```python
class EventBus(ABC):
    async def connect(self, servers: str) -> None: ...
    async def publish(self, topic: str, event: Event) -> None: ...
    async def subscribe(self, topic: str, handler, queue: str = None) -> Subscription: ...
    async def request(self, topic: str, event: Event, timeout: float) -> Optional[Event]: ...
    async def close(self) -> None: ...
```

### 5.3 Delivery Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| At-least-once | NATS JetStream durable subscriptions |
| Ordered per subject | Same subject → same order |
| No message loss | JetStream persistence + PostgreSQL backup |
| Queue groups | Load-balanced between subscribers of same group |

### 5.4 Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Pub/Sub** | One publisher, many subscribers | Interface events, system broadcasts |
| **Queue Groups** | One publisher, one consumer from group | Task assignment (one module handles) |
| **Request/Reply** | Publish and wait for response | Capability query, status check |

---

## 6. Event Lifecycle

```
1. Source creates Event
2. Source publishes to NATS subject
3. NATS delivers to all matching subscribers
4. Each subscriber deserializes Event
5. Subscriber processes Event (async)
6. Subscriber may publish result Event
7. Result event delivered to its subscribers
```

**Example flow**:
```
CLI publishes: ethan.interface.cli
  │
  ▼
Kernel receives, creates Request
  │
  ▼
Planner receives, creates Plan
  │
  ▼
Executor receives, assigns task → ethan.capability.docker.build
  │
  ▼
Docker module receives, executes, publishes result
  │
  ▼
Executor receives result, publishes ethan.response.<correlation_id>
```

---

## 7. Error Handling

| Failure | Behavior |
|---------|----------|
| Publish fails | Logged, no retry (caller responsible) |
| Subscribe fails | Logged, system may not start |
| Handler panics | Caught and logged, subscription stays active |
| Unknown event type | Logged, event not routed |
| Malformed event | Logged, event not routed |

---

## 8. Existing Implementations

| Implementation | Language | File | Status |
|---------------|----------|------|--------|
| Abstract interface | Python | `kernel/bus/interface.py` | Stable |
| NATS JetStream impl | Python | `kernel/bus/nats_bus.py` | Stable |
| In-memory bus | Go | `kernel/bus/bus.go` | Development |
| Event type | Go | `kernel/types/event.go` | Development |

---

## Appendix A: Example Event Sequence

```
Step 1: User types "ethan status"
─────────────────────────────────
Publisher: CLI
Subject:   ethan.interface.cli
Event:
  id: 20260623150500.000000001
  type: interface.command
  source: cli
  payload: {"cmd": "ethan status"}

Step 2: Kernel receives, validates, creates request
─────────────────────────────────
Subject:   ethan.kernel.request.created
Event:
  type: kernel.request.created
  source: kernel
  payload: {"intent": "status", "request_id": "..."}

Step 3: Planner creates execution plan
─────────────────────────────────
Subject:   ethan.planner.plan.created
Event:
  type: planner.plan.created
  source: planner
  payload: {"plan_id": "...", "tasks": [...]}

Step 4: Executor publishes response
─────────────────────────────────
Subject:   ethan.response.20260623150500.000000001
Event:
  type: response.ok
  source: executor
  payload: {"status": "online", "mode": "idle", "goal": "none"}