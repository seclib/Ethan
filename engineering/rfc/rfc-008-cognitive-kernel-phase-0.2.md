# RFC-008 — Cognitive Kernel Architecture (Phase 0.2)

> **Status**: Proposed
> **Date**: 2026-06-23
> **Author**: Architecture Team
> **PR**: TBD

---

## Table of Contents

1. [Summary](#1-summary)
2. [Motivation](#2-motivation)
3. [Architecture Overview](#3-architecture-overview)
4. [NATS Event Bus](#4-nats-event-bus)
5. [State Layer](#5-state-layer)
6. [Module System](#6-module-system)
7. [Cognitive Kernel](#7-cognitive-kernel)
8. [Goal Manager](#8-goal-manager)
9. [Scheduler](#9-scheduler)
10. [API Gateway](#10-api-gateway)
11. [Observability](#11-observability)
12. [Deployment](#12-deployment)
13. [Implementation Plan](#13-implementation-plan)
14. [Risks and Mitigations](#14-risks-and-mitigations)

---

## 1. Summary

Ethan Phase 0.2 transforms the current monolithic cognitive loop into a **distributed, event-driven cognitive system**. The Kernel becomes an orchestrator — it does NOT think, it routes. Cognitive modules are independent services communicating exclusively via NATS.

### Key Principles

- **Everything is event-driven** — No direct module-to-module calls
- **Modules are independent** — Isolated, independently scalable
- **Kernel orchestrates, does not think** — Zero cognitive logic
- **LLMs are replaceable** — Provider abstraction
- **State is externalized** — Redis (live) + PostgreSQL (persistent)

---

## 2. Motivation

### Current State (Phase 0.1)

```
CognitiveLoop (monolithic)
├── perceive
├── reason       ← LLM call embedded
├── plan         ← LLM call embedded  
├── execute
├── observe
├── update_memory
└── reflect      ← LLM call embedded
```

**Problems:**
- All cognitive logic in a single process
- LLM providers tightly coupled
- No scalability — cannot scale reasoning independently
- No event-driven communication
- State lives in memory, lost on restart
- No observability across cognitive steps

### Target State (Phase 0.2)

```
API → NATS → [reasoning module] → NATS → [planning module] → NATS → ...
             ↑                    ↑
        independent service  independent service
```

**Benefits:**
- Scale reasoning independently (5 replicas, 1 planning)
- Swap LLM provider per module
- Distributed tracing across all steps
- State survives restarts
- Each module testable in isolation

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway (FastAPI)                        │
│  /v1/intent/text  /v1/intent/voice  /v1/intent/api  /health        │
└────────────────────────┬────────────────────────────────────────────┘
                         │ HTTP → Event (NATS publish)
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     NATS Event Bus (JetStream)                       │
│                                                                      │
│  Topics: ethan.intent.*  ethan.module.*  ethan.capability.*         │
│          ethan.memory.*  ethan.system.*   ethan.schedule.*          │
└────┬──────────┬──────────┬──────────┬──────────┬────────────────────┘
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐
│Cognitive │ │Module    │ │Scheduler │ │Goal      │ │Observability    │
│Kernel    │ │Registry  │ │          │ │Manager   │ │(OpenTelemetry)  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────────────┘
     │                                               │
     ▼                                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         State Layer                                  │
│                                                                      │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────┐  │
│  │  Redis (Live)      │  │  PostgreSQL (P)    │  │  Prometheus   │  │
│  │  - Sessions        │  │  - Goals           │  │  + Grafana    │  │
│  │  - Cache           │  │  - History         │  │               │  │
│  │  - Pub/Sub         │  │  - Module state    │  └───────────────┘  │
│  └────────────────────┘  └────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. NATS Event Bus

### 4.1 Topic Structure

```
ethan.>
├── intent.>
│   ├── user                    # Raw user input → Kernel
│   └── response                # Final response ← Kernel
│
├── module.>
│   ├── reasoning               # Reasoning request
│   │   └── done                # Reasoning response
│   ├── planning
│   │   └── done
│   ├── execution
│   │   └── done
│   ├── memory
│   │   └── done
│   └── reflection
│       └── done
│
├── capability.>
│   ├── {name}
│   └── {name}.done
│
├── memory.>
│   ├── store
│   ├── retrieve
│   └── search
│
├── system.>
│   ├── kernel.started
│   ├── kernel.shutdown
│   ├── module.registered
│   └── module.unregistered
│
├── schedule.>
│   ├── trigger
│   └── completed
│
└── audit
```

### 4.2 Event Schema

```python
@dataclass
class Event:
    """Standard event envelope for all NATS messages."""
    id: str                          # UUID
    type: str                        # "intent.user", "module.reasoning.done", etc.
    source: str                      # Service identifier
    timestamp: datetime              # UTC
    version: str = "1.0"             # Schema version
    
    data: Dict[str, Any]             # Payload
    metadata: Dict[str, Any]         # trace_id, span_id, auth, correlation_id
    
    reply_to: Optional[str] = None   # NATS reply subject for request-reply
```

### 4.3 Producer/Consumer Patterns

| Pattern | Use Case | Mechanism |
|---------|----------|-----------|
| **Publish/Subscribe** | System events, audit log | NATS pub/sub |
| **Request-Reply** | Kernel → Module chain | NATS reply subject |
| **Queue Group** | Load-balanced module instances | NATS queue groups |
| **Stream (JetStream)** | Durable message persistence | JetStream consumers |
| **Key-Value Store** | Module heartbeats | NATS KV bucket |

### 4.4 Reliability Strategy

```
1. JetStream Persistence
   └── Messages survive broker restart

2. Outbox Pattern (PostgreSQL)
   └── Events written to events_outbox before NATS publish
   └── Background process retries failed publishes

3. Competing Consumers (NATS Queue Groups)
   └── Module-reasoning with scale=2 → automatic load balancing

4. Timeout + Retry
   └── Kernel enforces 30s timeout per module call
   └── 3 retries with exponential backoff (1s, 4s, 9s)

5. Health Checks
   └── Kernel pings modules every 5s via NATS heartbeat
   └── Miss 3 heartbeats → module marked dead
```

---

## 5. State Layer

### 5.1 Redis — Live State

```
Key                          │ Type      │ TTL    │ Description
─────────────────────────────┼───────────┼────────┼────────────────────
session:{session_id}         │ Hash      │ 24h    │ Session state
session:{session_id}:history │ List      │ 24h    │ Recent interactions
goal:{goal_id}               │ Hash      │ 72h    │ Active goal
module:{module_id}:heartbeat │ String    │ 30s    │ Module liveness
user:{user_id}:context       │ Hash      │ 1h     │ User context cache
lock:{resource}              │ String    │ 10s    │ Distributed lock
```

### 5.2 PostgreSQL — Persistent State

```
Table           │ Key Columns               │ Description
────────────────┼───────────────────────────┼────────────────────
goals           │ id, user_id, status       │ All goals created
goal_steps      │ goal_id, module, status   │ Each chain step
sessions        │ id, user_id, created_at   │ Session metadata
modules         │ id, version, capabilities │ Module registry
audit_log       │ id, timestamp, action     │ Immutable audit trail
users           │ id, roles, permissions    │ User data
events_outbox   │ id, topic, payload        │ Outbox pattern
```

### 5.3 Data Models

```python
@dataclass
class Goal:
    """A cognitive goal representing a user request end-to-end."""
    id: str
    status: GoalStatus  # pending | in_progress | completed | failed
    intent: Intent
    chain: List[ChainStep]
    result: Optional[Any]
    timeline: Timeline
    metadata: Dict[str, Any]

@dataclass
class ChainStep:
    """Single step in a goal's cognitive chain."""
    module: str           # "reasoning", "planning", etc.
    status: StepStatus    # pending | running | completed | failed | skipped
    result: Optional[Any]
    duration_ms: Optional[float]
    retry_count: int = 0
```

---

## 6. Module System

### 6.1 Module Interface

```python
class CognitiveModule(ABC):
    """Interface for all cognitive modules in Ethan."""

    @abstractmethod
    def get_manifest(self) -> ModuleManifest:
        """Declare module identity and capabilities."""
        ...

    @abstractmethod
    async def initialize(self, context: ModuleContext) -> None:
        """Initialize module resources (LLM connection, models, caches)."""
        ...

    @abstractmethod
    async def handle_event(self, event: Event) -> Optional[Event]:
        """Process incoming event, return response event (or None)."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Release resources."""
        ...

@dataclass
class ModuleManifest:
    """Identity and capabilities declaration."""
    id: str                          # "reasoning-v1"
    name: str                        # "Reasoning Module"  
    version: str                     # "1.0.0"
    capabilities: List[str]          # ["reasoning.analyze", "reasoning.infer"]
    topics_subscribed: List[str]     # ["ethan.module.reasoning"]
    topics_published: List[str]      # ["ethan.module.reasoning.done"]
    dependencies: List[str]          # ["provider.llm"]
    health_check_interval: int = 5   # seconds
```

### 6.2 Module Registry

```python
class ModuleRegistry(ABC):
    """Discover and manage cognitive modules."""

    @abstractmethod
    async def discover(self) -> List[ModuleManifest]:
        """Discover modules via NATS heartbeat, config, or Docker labels."""
        ...

    @abstractmethod
    async def register(self, manifest: ModuleManifest) -> None:
        """Register a module."""

    @abstractmethod
    async def unregister(self, module_id: str) -> None:
        """Remove a module."""

    @abstractmethod
    async def health_check(self, module_id: str) -> bool:
        """Ping a module."""

    @abstractmethod
    def find_by_capability(self, capability: str) -> List[ModuleManifest]:
        """Find modules providing a capability."""
```

### 6.3 Standard Modules (Phase 0.2)

| Module | Responsibility | Topics | Dependencies |
|--------|---------------|--------|--------------|
| **Reasoning** | Analyze intent, infer meaning | `ethan.module.reasoning` | LLM Provider |
| **Planning** | Decompose into steps | `ethan.module.planning` | LLM Provider |
| **Execution** | Execute capabilities | `ethan.module.execution` | Capability Registry |
| **Memory** | Store/retrieve context | `ethan.module.memory` | Redis |
| **Reflection** | Learn from outcomes | `ethan.module.reflection` | LLM Provider |

---

## 7. Cognitive Kernel

### 7.1 Responsibilities

The Cognitive Kernel is **NOT a cognitive engine**. It is an event orchestrator responsible for:

1. **Boot sequence** — Connect NATS, Redis, PG, discover modules
2. **Intent routing** — Receive intent events, create goals
3. **Chain orchestration** — Route events through module chain in order
4. **State management** — Persist goal state in Redis + PostgreSQL
5. **Error handling** — Retry, timeout, fallback, degradation
6. **Health monitoring** — Track module liveness
7. **Graceful shutdown** — Drain in-flight goals

### 7.2 Boot Sequence

```
1. Load configuration
2. Connect to NATS (with retry, backoff)
3. Connect to Redis + PostgreSQL (with retry)
4. Initialize Module Registry
5. Create NATS subscriptions:
   ├── ethan.intent.>      → handle_intent()
   ├── ethan.module.*.done  → handle_module_response()
   └── ethan.system.>      → handle_system_event()
6. Start Scheduler
7. Start Health Check loop (every 5s)
8. Publish system.kernel.started
```

### 7.3 Intent → Response Flow

```
handle_intent(event):
  │
  ├── 1. Validate (schema, auth placeholder)
  ├── 2. Check permissions (Safety layer)
  ├── 3. Create Goal in PostgreSQL (status: pending)
  ├── 4. Create trace (OpenTelemetry span)
  ├── 5. Store initial state in Redis (status: in_progress)
  │
  ├── 6. Execute chain:
  │     ├── module_reasoning  → publish + await reply
  │     ├── module_planning   → publish + await reply  
  │     ├── module_execution  → publish + await reply
  │     ├── module_memory     → publish + await reply
  │     └── module_reflection → publish + await reply
  │
  ├── 7. Complete Goal in PostgreSQL
  ├── 8. Publish response event (ethan.intent.response)
  ├── 9. Publish audit event (ethan.audit)
  └── 10. Close trace
```

### 7.4 Pseudocode

```python
class CognitiveKernel:
    """Orchestrates cognitive modules via NATS. Does NOT contain cognitive logic."""

    def __init__(
        self,
        event_bus: EventBus,
        state_manager: StateManager,
        module_registry: ModuleRegistry,
        scheduler: Scheduler,
        goal_manager: GoalManager,
        safety: SafetyChecker,
        tracer: Tracer,
    ):
        ...

    async def start(self):
        """Boot sequence."""
        await self.bus.connect()
        await self.state.connect()
        await self.registry.discover()
        await self._subscribe()
        await self.scheduler.start()
        await self.bus.publish(Event(
            type="system.kernel.started",
            source="kernel",
            data={"version": __version__},
        ))

    async def _handle_intent(self, event: Event):
        """Full intent-to-response flow."""
        # 1. Permission check
        if not await self.safety.check_permission(...):
            await self._reject(event, "permission_denied")
            return

        # 2. Create goal
        goal = await self.goal_manager.create(
            intent=event.data["intent"],
            user_id=event.metadata["auth"]["user_id"],
        )

        # 3. Execute cognitive chain
        async with self.tracer.start_span("cognitive_chain") as span:
            chain = ["reasoning", "planning", "execution", "memory", "reflection"]
            for module_name in chain:
                step_result = await self._call_module(module_name, goal)
                await self.goal_manager.update_step(goal.id, module_name, step_result)

        # 4. Complete and respond
        await self.goal_manager.complete(goal.id)
        await self._publish_response(goal)

    async def _call_module(self, module_name: str, goal: Goal) -> StepResult:
        """Call a module via NATS request-reply with timeout and retry."""
        manifests = self.registry.find_by_capability(f"module.{module_name}")
        if not manifests:
            return StepResult(status="skipped", error="no_module_available")

        module = manifests[0]
        request = Event(
            type=f"module.{module_name}",
            source="kernel",
            data={"goal_id": goal.id, "intent": goal.intent},
            reply_to=f"module.{module_name}.done.{goal.id}",
        )

        for attempt in range(3):
            try:
                response = await self.bus.request(
                    topic=f"ethan.module.{module_name}",
                    event=request,
                    timeout=30.0,
                )
                return StepResult(status="completed", result=response.data)
            except TimeoutError:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s
                continue

        return StepResult(status="failed", error="max_retries_exceeded")
```

---

## 8. Goal Manager

### 8.1 Goal Lifecycle

```
Intent Received
       │
       ▼
    ┌────────┐
    │pending │
    └────────┘
       │
    Kernel starts chain
       │
       ▼
    ┌────────────┐
    │in_progress │
    └────────────┘
       │
    ┌──┴──┐
    │     │
    ▼     ▼
┌────────┐ ┌────────┐
│completed│ │ failed │
└────────┘ └────────┘
```

### 8.2 Goal Decomposition

```
Goal: "Analyze Q3 financial report and summarize"
  │
  ├── Step 1: reasoning
  │     └── Extract intent, identify entities (Q3, financial, report)
  │
  ├── Step 2: planning
  │     └── Plan: { retrieve_report → analyze_data → generate_summary }
  │
  ├── Step 3: execution
  │     └── Execute each plan step via capabilities
  │
  ├── Step 4: memory
  │     └── Store interaction context
  │
  └── Step 5: reflection
        └── Learn: was user satisfied? Improve next time?
```

---

## 9. Scheduler

### 9.1 Responsibilities

- Trigger periodic tasks (cron-like)
- Retry failed goal steps
- Clean up expired sessions
- Emit heartbeat events

### 9.2 Triggers

| Trigger Type | Source | Example |
|-------------|--------|---------|
| Cron | Config | `0 */6 * * *` — memory cleanup |
| Event | NATS | On `capability.completed` |
| Timeout | Kernel | After 30s module timeout |
| Manual | API | POST `/v1/schedule` |

```python
class Scheduler(ABC):
    @abstractmethod
    async def start(self):
        """Start scheduler loop."""

    @abstractmethod
    async def schedule_cron(self, expression: str, topic: str, payload: dict):
        """Register a cron trigger."""

    @abstractmethod
    async def cancel(self, job_id: str):
        """Cancel a scheduled job."""
```

---

## 10. API Gateway

### 10.1 Entry Points

```
POST /v1/intent/text      → Parse text → Publish ethan.intent.user
POST /v1/intent/voice     → Parse transcript → Publish ethan.intent.user  
POST /v1/intent/api       → Parse structured input → Publish ethan.intent.user
POST /v1/intent/automation → Parse trigger → Publish ethan.intent.user
GET  /health               → Return system status
```

### 10.2 Request → Event Flow

```
1. HTTP POST /v1/intent/text { "input": "Hello", ... }
2. API Gateway validates request (Pydantic)
3. Creates Intent object
4. Publishes NATS event:
   topic: ethan.intent.user
   payload: { intent, session_id, metadata }
5. Subscribes to response topic:
   topic: ethan.intent.response.{session_id}
6. Waits for response (with timeout)
7. Returns HTTP 200 with response body
```

### 10.3 Authentication (Placeholder)

```python
class AuthMiddleware(BaseHTTPMiddleware):
    """Placeholder authentication — validates JWT or API key."""
    
    async def dispatch(self, request, call_next):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token:
            raise HTTPException(401, "Missing auth token")
        # TODO: Integrate with Safety layer (ADR-1009)
        request.state.user = {"id": "user_42", "roles": ["user"]}
        return await call_next(request)
```

---

## 11. Observability

### 11.1 Logging Strategy

```yaml
format: json
fields:
  - timestamp
  - level
  - service
  - trace_id
  - span_id
  - message
  - module
  - goal_id
  - duration_ms

levels:
  - fatal   # System cannot recover
  - error   # Module failure, retry exhausted
  - warn    # Module timeout, retry attempt
  - info    # Goal completed, module registered
  - debug   # Event received, step started
```

### 11.2 Metrics (Prometheus)

```
Metric                          │ Type      │ Labels
────────────────────────────────┼───────────┼────────────────────────
ethan_goals_total               │ Counter   │ status, module
ethan_goals_duration_seconds    │ Histogram │ module (buckets: 0.1, 1, 5, 30, 120)
ethan_events_published_total    │ Counter   │ topic
ethan_modules_active            │ Gauge     │ module_id
ethan_kernel_uptime_seconds     │ Gauge     │ -
ethan_llm_calls_total           │ Counter   │ provider, model
ethan_llm_duration_seconds      │ Histogram │ provider
ethan_safety_checks_total       │ Counter   │ result (allow/deny)
```

### 11.3 Tracing (OpenTelemetry)

```
Trace: User Request "Analyze Q3 report"
  ├── Span: api-gateway.handle_request
  │   └── Event: published to nats:ethan.intent.user
  ├── Span: kernel.handle_intent
  │   ├── Span: goal_manager.create
  │   ├── Span: kernel.call_module (reasoning)
  │   │   └── Span: module-reasoning.handle_event
  │   │       └── Span: llm.provider.call
  │   ├── Span: kernel.call_module (planning)
  │   │   └── Span: module-planning.handle_event
  │   ├── Span: kernel.call_module (execution)
  │   ├── Span: kernel.call_module (memory)
  │   └── Span: kernel.call_module (reflection)
  └── Span: api-gateway.respond
```

---

## 12. Deployment

### 12.1 Docker Compose Services

```yaml
services:
  # Infrastructure
  nats:                # Event bus + JetStream persistence
  redis:               # Live state, cache
  postgres:            # Persistent state, audit trail

  # Core
  api-gateway:         # FastAPI entry point
  cognitive-kernel:    # Event orchestrator

  # Modules
  module-reasoning:    # LLM-based reasoning (scale: 2)
  module-planning:     # Goal decomposition
  module-execution:    # Capability execution
  module-memory:       # Memory management
  module-reflection:   # Learning & adaptation

  # Observability
  prometheus:          # Metrics collection
  grafana:             # Metrics visualization
  jaeger:              # Distributed tracing
```

### 12.2 Service Interaction Matrix

```
              │ NATS  Redis  PG   Prom  Jaeger  API
──────────────┼─────────────────────────────────────────
API Gateway   │  W     -     -     W     W       -
Kernel        │  RW    RW    W     W     W       -
module-*      │  RW    R     -     W     W       -
Prometheus    │  -     -     -     -     -       -
Grafana       │  -     -     -     R     R       -
```

### 12.3 Scaling Strategy

| Service | Scale | Strategy |
|---------|-------|----------|
| API Gateway | 2+ | Stateless HTTP, behind load balancer |
| Kernel | 1 (active) | Single orchestrator, NATS queue group for HA |
| module-reasoning | 2–5 | NATS queue group, LLM calls are bottleneck |
| module-planning | 1–2 | Less CPU-intensive |
| module-execution | 2+ | Depends on capability count |
| module-memory | 1 | Redis-bound, fast |
| module-reflection | 1 | Background, not on critical path |

---

## 13. Implementation Plan

### Phase 0.2.1 — NATS Event Bus (3 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `kernel/bus/interface.py` — EventBus ABC | Interface |
| 2 | Create `kernel/bus/nats_bus.py` — NATS implementation | NATS pub/sub + JetStream |
| 3 | Test topic structure, request-reply, queue groups | Tests pass |

### Phase 0.2.2 — State Layer (2 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `kernel/state/interface.py` + `redis_state.py` | Redis session/cache |
| 2 | Create `postgres_state.py` + migrations | PG schema + outbox |

### Phase 0.2.3 — Module SDK + Registry (2 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `sdk/module.py` — CognitiveModule ABC + ModuleManifest | SDK |
| 2 | Create `kernel/registry/` — ModuleRegistry + discovery | Registry working |

### Phase 0.2.4 — Cognitive Kernel (3 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `kernel/kernel.py` — Kernel class + boot sequence | Boot sequence |
| 2 | Implement `_handle_intent` + chain orchestration | Intent flow |
| 3 | Implement retry, timeout, error handling | Resilience |

### Phase 0.2.5 — Scheduler (1 day)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `kernel/scheduler/` — cron triggers + event scheduling | Scheduler |

### Phase 0.2.6 — Observability (2 days)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `kernel/telemetry/tracer.py` + `metrics.py` | OpenTelemetry + Prometheus |
| 2 | Create `kernel/telemetry/logger.py` — structured JSON logging | Logging |

### Phase 0.2.7 — Docker Compose (1 day)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create Dockerfiles + `docker-compose.yml` + NATS config | Full deployment |

**Total: 14 days**

---

## 14. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| NATS request-reply timeout | User waits indefinitely | Low | 30s timeout + fallback response |
| Module crash during goal | Goal incomplete | Medium | Retry 3x, then mark step failed |
| Redis down | No live state | Low | Kernel fails fast, health check |
| LLM provider outage | Reasoning module dead | Medium | Provider fallback (Anthropic → OpenAI) |
| Event order race condition | Wrong chain order | Low | Kernel serializes per goal |
| Memory leak in module | OOM kill | Medium | Resource limits in Docker |
| NATS broker failure | Complete outage | Very Low | NATS cluster (3 nodes in prod) |

---

## References

- [Constitution Architecturale](/engineering/architecture/constitution.md)
- [ADR-1004](/engineering/adr/ADR-1004-cognitive-loop-architecture.md) — Cognitive Loop
- [ADR-1007](/engineering/adr/ADR-1007-event-driven-architecture.md) — Event-Driven Architecture
- [ADR-1008](/engineering/adr/ADR-1008-plugin-discovery-loading.md) — Plugin Discovery
- [ADR-1009](/engineering/adr/ADR-1009-safety-permission-model.md) — Safety & Permission

---

*RFC-008 — Version 1.0 — 2026-06-23*