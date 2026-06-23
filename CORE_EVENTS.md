# ETHAN Core System Events

## 1. user.input

**Purpose**: Raw user input enters the system from any interface.

**Source**: CLI, API, Web UI, VSCode

**Subject**: `ethan.interface.<source>`

**Schema**:
```json
{
  "type": "interface.command",
  "source": "cli",
  "payload": {
    "cmd": "ethan status",
    "args": []
  }
}
```

**Handlers**: Kernel (ingest → intent engine)

---

## 2. kernel.plan

**Purpose**: A decomposed execution plan is ready.

**Source**: Planner module

**Subject**: `ethan.planner.plan.created`

**Schema**:
```json
{
  "type": "planner.plan.created",
  "source": "planner",
  "payload": {
    "plan_id": "plan-abc-123",
    "goal_id": "goal-def-456",
    "tasks": [
      {
        "id": "task-001",
        "capability": "docker.build",
        "params": {"image": "myapp"},
        "depends_on": []
      }
    ]
  }
}
```

**Handlers**: Executor (task assignment)

---

## 3. capability.request

**Purpose**: A capability invocation request to a module.

**Source**: Executor

**Subject**: `ethan.capability.<name>`

**Schema**:
```json
{
  "type": "capability.invoke",
  "source": "executor",
  "payload": {
    "task_id": "task-001",
    "capability": "docker.build",
    "params": {"image": "myapp"}
  },
  "context": {
    "correlation_id": "req-abc-123"
  }
}
```

**Handlers**: Module that registered the capability

---

## 4. memory.store

**Purpose**: Request to persist data in memory.

**Source**: Any module or kernel

**Subject**: `ethan.memory.store.request`

**Schema**:
```json
{
  "type": "memory.store.request",
  "source": "planner",
  "payload": {
    "key": "planner:task:task-001",
    "value": {"status": "running", "started_at": "..."},
    "ttl_seconds": 3600
  }
}
```

**Handlers**: Memory module (store → Redis/PostgreSQL)

**Success response**: `memory.store.complete`

---

## 5. plugin.register

**Purpose**: A plugin declares its capabilities to the system.

**Source**: Plugin loader, module startup

**Subject**: `ethan.registry.capability.registered`

**Schema**:
```json
{
  "type": "registry.capability.registered",
  "source": "hello-world",
  "payload": {
    "capabilities": [
      {
        "name": "hello.greet",
        "version": "1.0.0",
        "module": "hello-world",
        "inputs": ["hello.greet.request"],
        "outputs": ["hello.greet.complete"]
      }
    ]
  }
}
```

**Handlers**: Capability registry (validate → store → broadcast `registry.updated`)

---

## 6. error.occurred

**Purpose**: A system error occurred at any layer.

**Source**: Kernel, module, executor, ingest

**Subject**: `ethan.system.error`

**Schema**:
```json
{
  "type": "system.error",
  "source": "planner",
  "payload": {
    "error": "capability not found: missing.module",
    "component": "planner",
    "request_id": "req-abc-123"
  }
}
```

**Handlers**: Telemetry (log, metric counter, alert)

**Related error subjects**:
| Subject | Source | Condition |
|---------|--------|-----------|
| `ethan.ingest.error` | Ingest | Invalid event rejected |
| `ethan.planner.plan.failed` | Planner | Plan generation failed |
| `ethan.executor.task.failed` | Executor | Task execution failed |
| `ethan.capability.failed` | Module | Capability invocation failed |
| `ethan.response.error` | Kernel | Response delivery failed |
| `ethan.system.error` | Any | Unhandled system error |

---

## Event Type Constants (Python)

```python
# These already exist in sdk/event.py
EventType.INTERFACE_COMMAND       # user.input
EventType.PLANNER_PLAN_CREATED    # kernel.plan
EventType.CAPABILITY_INVOKE        # capability.request
EventType.MEMORY_STORE_REQUEST     # memory.store
EventType.REGISTRY_CAPABILITY_REGISTERED  # plugin.register
EventType.SYSTEM_ERROR            # error.occurred
```

## Subject Constants (Go)

```go
// These already exist in kernel/bus/subjects.go
bus.SubjectInterfaceCLI           // user.input
bus.SubjectPlannerPlanCreated     // kernel.plan
// capability.request is dynamic: "ethan.capability." + name
// memory.store.request is dynamic: "ethan.memory."
bus.SubjectRegistryCapabilityRegistered  // plugin.register
bus.SubjectSystemError            // error.occurred