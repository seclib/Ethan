# ETHAN Event Lifecycle Specification

## 1. Lifecycle Overview

Every event in the system follows exactly 5 steps:

```
[1] EMIT ──► [2] INTERCEPT ──► [3] ROUTE ──► [4] PROCESS ──► [5] RESPOND
```

Each step is a discrete phase with defined input, output, and tracing boundaries.

---

## 2. Step Details

### 2.1 EMIT

**Purpose**: Create and publish an event onto the bus.

**Trigger**: Any component generates an event (interface input, module output, timer expiry).

**Rules**:
- Event must have a unique `id` (UUID or timestamp+nano)
- Event must have a valid `type` (from `EventType` registry)
- Event must have a `source` identifying the emitter
- Event must have a `timestamp` (ISO 8601 UTC)
- Payload and context are optional but recommended

**Tracing**:
- Generate `correlation_id` if not inherited
- Generate `span_id` for this emit step
- Record `emit_timestamp`

**Pseudocode**:
```
function emit(source, type, payload):
    event = {
        id: generate_id(),
        type: type,
        source: source,
        timestamp: now(),
        payload: payload,
        context: {
            correlation_id: payload.context.correlation_id ?? generate_id(),
            span_id: generate_id(),
            parent_span_id: payload.context.span_id ?? nil
        }
    }
    bus.publish(event)
    return event.id
```

---

### 2.2 INTERCEPT

**Purpose**: Validate and enrich the event before routing.

**Trigger**: Event arrives at the kernel (via NATS subscriber).

**Steps**:
1. Deserialize JSON → Event struct
2. Validate required fields (`id`, `type`, `source`, `timestamp`)
3. Reject invalid events → emit `ingest.error`
4. Enrich context if missing (add `ingest_timestamp`)
5. Pass to Router

**Validation rules**:
| Check | Failure action |
|-------|---------------|
| Missing `id` | Auto-generate, log warning |
| Missing `type` | Emit `ingest.error`, drop event |
| Missing `source` | Emit `ingest.error`, drop event |
| Malformed JSON | Emit `ingest.error`, drop event |
| Unknown event type | Log warning, route anyway |

**Tracing**:
- Record `ingest_timestamp`
- Record `intercept_latency`
- Attach `kernel_span_id`

**Pseudocode**:
```
function intercept(event):
    if !validate(event):
        emit("ingest", "ingest.error", {reason: "invalid", event_id: event.id})
        return nil
    
    event.context.ingest_timestamp = now()
    event.context.kernel_span_id = generate_id()
    return event
```

---

### 2.3 ROUTE

**Purpose**: Determine which component(s) should receive the event.

**Trigger**: Event passes interception.

**Algorithm**:
1. Match event `type` against routing table
2. Resolve target component (planner, executor, module, etc.)
3. If capability-based: query registry for target module
4. If queue group: select one subscriber
5. If broadcast: deliver to all matching subscribers

**Routing table**:
| Event Type | Target | Pattern |
|-----------|--------|---------|
| `interface.command` | Kernel | Broadcast |
| `kernel.request.created` | Planner | Queue (one instance) |
| `planner.plan.created` | Executor | Queue (one instance) |
| `executor.task.assigned` | Module | Queue (one per capability) |
| `module.capability.result` | Executor | Direct (by correlation_id) |
| `response.*` | Interface | Direct (by correlation_id) |
| `registry.capability.registered` | Registry | Queue |
| `system.*` | All | Broadcast |

**Tracing**:
- Record `route_target`
- Record `route_latency`
- Attach `routing_span_id`

**Pseudocode**:
```
function route(event):
    target = routing_table.match(event.type)
    if target == nil:
        log("unroutable event:", event.type)
        return

    event.context.route_target = target.name
    event.context.route_timestamp = now()
    event.context.routing_span_id = generate_id()
    
    forward(event, target)
```

---

### 2.4 PROCESS

**Purpose**: Execute the component's business logic.

**Trigger**: Routed event arrives at the target component.

**Steps**:
1. Component receives event
2. Component executes its logic (request decomposition, task execution, etc.)
3. Component may emit sub-events during processing
4. Component produces a result

**Processing types**:
| Component | Input Event | Processing | Output Events |
|-----------|-------------|------------|---------------|
| Planner | `kernel.request.created` | Decompose goal → task DAG | `planner.plan.created` |
| Executor | `planner.plan.created` | Assign tasks, track results | `executor.task.assigned`, `executor.plan.done` |
| Memory | `memory.*.request` | Store/recall/context | `memory.*.complete` |
| Registry | `registry.capability.registered` | Validate, store, broadcast | `registry.updated` |
| Response | `executor.plan.done` | Build response | `response.ok` |

**Tracing**:
- Record `process_start_timestamp`
- Record `process_end_timestamp`
- Record `process_latency = process_end - process_start`
- Attach `process_span_id`
- All sub-events inherit `correlation_id` and set `parent_span_id`

**Pseudocode**:
```
function process(event, component):
    event.context.process_start = now()
    event.context.process_span_id = generate_id()
    
    result = component.handle(event)
    
    event.context.process_end = now()
    event.context.process_latency = event.context.process_end - event.context.process_start
    
    return result
```

---

### 2.5 RESPOND

**Purpose**: Return the result to the originating interface or caller.

**Trigger**: Processing completes.

**Response types**:
| Type | When |
|------|------|
| `response.ok` | Processing succeeded |
| `response.error` | Processing failed with error |
| `response.timeout` | Processing exceeded timeout |
| `response.rejected` | Processing not possible (no capability) |

**Delivery**:
1. Response is published to `ethan.response.<correlation_id>`
2. Interface subscribes to `ethan.response.<correlation_id>` (temporary subscription)
3. If no subscriber exists, response is logged and discarded
4. If timeout (no response within TTL), interface emits timeout event

**Tracing**:
- Record `respond_timestamp`
- Record `total_latency = respond_timestamp - emit_timestamp`
- Attach `respond_span_id`
- Write full trace to telemetry store

**Pseudocode**:
```
function respond(event, result):
    response = {
        id: generate_id(),
        type: "response." + result.status,
        source: event.context.route_target,
        timestamp: now(),
        payload: result.data,
        context: {
            correlation_id: event.context.correlation_id,
            span_id: generate_id(),
            parent_span_id: event.context.process_span_id,
            emit_timestamp: event.context.emit_timestamp,
            ingest_timestamp: event.context.ingest_timestamp,
            route_timestamp: event.context.route_timestamp,
            process_start: event.context.process_start,
            process_end: event.context.process_end,
            respond_timestamp: now(),
            total_latency_ms: now() - event.context.emit_timestamp
        }
    }
    bus.publish("ethan.response." + event.context.correlation_id, response)
    telemetry.store_trace(response.context)
```

---

## 3. Complete Lifecycle Timeline

```
EMIT         INTERCEPT      ROUTE         PROCESS       RESPOND
│            │              │             │             │
▼            ▼              ▼             ▼             ▼
┌──────┐    ┌─────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ Create │──►│Validate │──►│ Match  │──►│Execute │──►│ Return │
│ Event │   │Enrich   │   │Forward │   │Result  │   │Result  │
└──────┘   └─────────┘    └────────┘   └────────┘   └────────┘
    │            │              │             │            │
    ▼            ▼              ▼             ▼            ▼
trace:       trace:         trace:        trace:        trace:
emit_ts      ingest_ts      route_ts      process_ts    respond_ts
span_id      kernel_span    routing_span  process_span  respond_span
correlation──►──────correlation_id (inherited throughout)────────────►
```

---

## 4. Tracing Model

### 4.1 Trace Context Fields

| Field | Generated at | Inherited | Description |
|-------|-------------|-----------|-------------|
| `correlation_id` | EMIT | yes (never changed) | Root trace ID for the entire request |
| `span_id` | EMIT | no | Current processing span |
| `parent_span_id` | — | yes | Span that triggered this processing |
| `emit_timestamp` | EMIT | yes | When the root event was created |
| `ingest_timestamp` | INTERCEPT | no | When kernel received the event |
| `route_target` | ROUTE | no | Component that will process |
| `process_start` | PROCESS | no | When processing began |
| `process_end` | PROCESS | no | When processing ended |
| `process_latency` | PROCESS | no | Duration of processing |
| `respond_timestamp` | RESPOND | no | When response was sent |
| `total_latency_ms` | RESPOND | no | End-to-end duration |

### 4.2 Span Relationships

```
correlation_id: "req-abc-123"
  │
  ├─ span_id: "emit-001" (parent: nil)
  │
  ├─ span_id: "intercept-002" (parent: "emit-001")
  │
  ├─ span_id: "route-003" (parent: "intercept-002")
  │
  ├─ span_id: "process-004" (parent: "route-003")
  │     │
  │     ├─ span_id: "sub-emit-005" (parent: "process-004")
  │     │     │
  │     │     └─ span_id: "sub-process-006" (parent: "sub-emit-005")
  │     │
  │     └─ span_id: "sub-emit-007" (parent: "process-004")
  │
  └─ span_id: "respond-008" (parent: "process-004")
```

### 4.3 Telemetry Record

After RESPOND, the full trace is stored:

```json
{
  "correlation_id": "req-abc-123",
  "spans": [
    {"id": "emit-001", "parent": null, "component": "cli", "type": "emit", "ts": "..."},
    {"id": "intercept-002", "parent": "emit-001", "component": "kernel", "type": "intercept", "ts": "...", "latency_ms": 0.2},
    {"id": "route-003", "parent": "intercept-002", "component": "kernel", "type": "route", "ts": "...", "target": "planner"},
    {"id": "process-004", "parent": "route-003", "component": "planner", "type": "process", "ts": "...", "latency_ms": 45.1},
    {"id": "respond-008", "parent": "process-004", "component": "kernel", "type": "respond", "ts": "...", "total_latency_ms": 52.3}
  ],
  "total_latency_ms": 52.3,
  "status": "ok"
}
```

---

## 5. Error Lifecycle

When an error occurs at any step:

```
EMIT ──► INTERCEPT ──► ROUTE ──► PROCESS ──► RESPOND
                                   │
                                   ▼
                                FAILURE
                                   │
                                   ▼
                              response.error
                                   │
                                   ▼
                              RESPOND (error)
```

Errors are:
- Logged at the step where they occur
- Attached to the response as `error` field
- Counter metrics incremented in telemetry
- Propagated through the same lifecycle (the error response goes through RESPOND)

---

## 6. Lifecycle in Go (kernel/main.go)

```go
func (s *Service) HandleEvent(ev types.Event) {
    // 1. INTERCEPT
    if err := s.ingest.Process(ev); err != nil {
        return // error event already emitted
    }

    // 2. EMIT was done by the interface, ROUTE happens via NATS subject match

    // 3. PROCESS (simplified: planner + executor)
    intent := s.intent.Extract(ev)
    req := types.NewRequest(ev, intent.Name, []string{intent.Name}, types.RequestContext{
        CorrelationID:   ev.Context["correlation_id"],
        Timestamp:       ev.Timestamp.Unix(),
    })
    plan, err := s.planner.Decompose(req)
    if err != nil || plan == nil {
        // RESPOND with rejection
        s.builder.Build(req, nil, fmt.Errorf("no capability for intent: %s", intent.Name))
        return
    }
    results := s.executor.Execute(*plan)

    // 4. RESPOND
    resp := s.builder.Build(req, results, nil)
    _ = resp
}
```

---

## 7. Lifecycle in Python (api/routers/message.py)

```python
async def post_message(request):
    # 1. EMIT event to NATS
    event = Event(id=str(uuid4()), type="interface.message", source="api")
    await nats.publish("ethan.interface.api", event.dict())

    # Kernel handles INTERCEPT → ROUTE → PROCESS → RESPOND

    # 5. Interface observes RESPOND on subscription
    # (response is delivered asynchronously)
    return MessageResponse(success=True, event_id=event.id)
```

---

## Appendix A: Telemetry API

The tracing system exposes:

| Operation | Description |
|-----------|-------------|
| `telemetry.store_trace(trace)` | Persist completed trace |
| `telemetry.query_trace(correlation_id)` | Retrieve trace by ID |
| `telemetry.list_traces(filter)` | List traces by time/status/source |
| `telemetry.metrics()` | Aggregate latency metrics |

Each trace is immutable once stored. No modification after RESPOND.

---

## Appendix B: Lifecycle Constants

```python
class LifecyclePhase:
    EMIT = "emit"
    INTERCEPT = "intercept"
    ROUTE = "route"
    PROCESS = "process"
    RESPOND = "respond"
    ERROR = "error"

class TraceField:
    CORRELATION_ID = "correlation_id"
    SPAN_ID = "span_id"
    PARENT_SPAN_ID = "parent_span_id"
    EMIT_TS = "emit_timestamp"
    INGEST_TS = "ingest_timestamp"
    ROUTE_TS = "route_timestamp"
    ROUTE_TARGET = "route_target"
    PROCESS_START = "process_start"
    PROCESS_END = "process_end"
    PROCESS_LATENCY = "process_latency"
    RESPOND_TS = "respond_timestamp"
    TOTAL_LATENCY = "total_latency_ms"
    STATUS = "status"
    ERROR = "error"