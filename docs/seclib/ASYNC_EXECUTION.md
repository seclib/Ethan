# ETHAN Asynchronous Execution Model

## 1. Architecture Overview

```
Interface ──► Event Bus (NATS)
                  │
                  ├─► Queue Group (Task Assignment) ──► Module A
                  │
                  ├─► Queue Group (Task Assignment) ──► Module B
                  │
                  └─► Parallel Fan-Out (broadcast) ──► Module C
                                                        Module D
```

Three execution primitives:
- **Parallel** — tasks with no interdependency run concurrently
- **Queued** — tasks assigned to queue groups (one consumer per group)
- **Retried** — failed tasks re-attempted with backoff

---

## 2. Execution Primitives

### 2.1 Parallel Execution

**Mechanism**: NATS broadcast fan-out.

**Usage**: When a plan contains independent tasks (no `DependsOn`).

**Flow**:
```
Planner creates plan with tasks T1, T2 (parallel)
    │
    ▼
Executor publishes T1 → ethan.capability.docker.build
Executor publishes T2 → ethan.capability.docker.publish
    │
    ▼
Both modules receive and execute concurrently
    │
    ▼
Executor collects all results via subscription callbacks
    │
    ▼
Executor aggregates → plan.done (when all tasks complete or fail)
```

**Implementation (Go goroutines)**:
```go
func (e *Executor) ExecuteParallel(tasks []Task) []TaskResult {
    var wg sync.WaitGroup
    results := make([]TaskResult, len(tasks))

    for i, task := range tasks {
        wg.Add(1)
        go func(idx int, t Task) {
            defer wg.Done()
            results[idx] = e.runTask(t)
        }(i, task)
    }
    wg.Wait()
    return results
}
```

### 2.2 Queued Events

**Mechanism**: NATS queue groups (load-balanced consumers).

**Usage**: Task assignment to module instances (one instance handles each task).

**Configuration**: All modules subscribed to `ethan.executor.task.assigned` with queue group `module-<capability>`.

**Properties**:
- Exactly one consumer per message (within queue group)
- Automatic load balancing across instance
- If instance crashes, message is re-delivered to another instance

**Example**:
```
NATS subject: ethan.executor.task.assigned
Queue group:  module-docker-build

Module A (subscribed) → receives message, starts task
Module B (subscribed) → idle (next message)

If Module A crashes → NATS redelivers to Module B
```

### 2.3 Cancellation

**Mechanism**: `task.cancel` event with correlation matching.

**Cancellation sources**:
- User request (interface sends cancel)
- Timeout (executor detects deadline exceeded)
- Dependency failure (upstream task failed)

**Flow**:
```
1. Executor receives cancellation request
2. Executor publishes ethan.executor.task.cancelled
3. Module receives cancel event, stops processing
4. Module publishes ethan.executor.task.completed with status "cancelled"
5. Executor marks plan as cancelled
```

**Implementation**:
```go
type CancellationToken struct {
    mu         sync.Mutex
    cancelled  bool
    onCancel   []func()
}

func (c *CancellationToken) Cancel() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.cancelled = true
    for _, f := range c.onCancel {
        f()
    }
}

func (e *Executor) ExecuteCancellable(task Task, ctx CancellationToken) TaskResult {
    select {
    case result := <-e.runTaskAsync(task):
        return result
    case <-ctx.Done():
        return TaskResult{TaskID: task.ID, Status: "cancelled"}
    }
}
```

### 2.4 Retry Mechanism

**Mechanism**: Exponential backoff with configurable max retries.

**Retry policy** (configured per task type):
```json
{
  "retry_policy": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "backoff_factor": 2.0,
    "max_delay_ms": 30000
  }
}
```

**Flow**:
```
Task fails (status=error)
    │
    ▼
Check retries < max_retries?
    │
    ├─ YES:
    │     ▼
    │   Wait = initial_delay * (backoff_factor ^ attempt)
    │   Wait = min(Wait, max_delay)
    │   Sleep(Wait)
    │   Publish ethan.executor.task.retrying
    │   Re-publish task
    │
    └─ NO:
          ▼
        Mark task as permanently failed
        Publish ethan.executor.task.failed
```

**Implementation**:
```go
func (e *Executor) runTaskWithRetry(task Task) TaskResult {
    attempt := 0
    for {
        result := e.runTask(task)
        if result.Status != "error" || attempt >= task.MaxRetries {
            return result
        }
        attempt++
        delay := time.Duration(float64(time.Second) * math.Pow(2, float64(attempt))) // 1s, 2s, 4s
        if delay > 30*time.Second {
            delay = 30 * time.Second
        }
        e.bus.Publish(SubjectExecutorTaskRetrying, mustMarshal(TaskResult{
            TaskID:   task.ID,
            Status:   "retrying",
            Duration: delay,
        }))
        time.Sleep(delay)
    }
}
```

---

## 3. Execution Pipeline

```
Request received
    │
    ▼
Planner decomposes into ExecutionPlan
    │
    ▼
Executor receives plan
    │
    ├─► Partition tasks by dependency
    │      │
    │      ├─ Level 0: tasks with no dependencies (parallel batch)
    │      ├─ Level 1: tasks depending on Level 0
    │      └─ Level N: tasks depending on Level N-1
    │
    ├─► For each level:
    │      │
    │      ├─► Execute tasks in parallel (goroutines)
    │      │      │
    │      │      ├─► Publish task.assigned → queue group
    │      │      ├─► Wait for completion with timeout
    │      │      ├─► Retry on failure (up to max_retries)
    │      │      └─► Collect results
    │      │
    │      └─► If any task fails → cancel remaining tasks in level
    │
    └─► Aggregate all results → plan.done
```

---

## 4. Event Subjects

### 4.1 Task Events

| Subject | Payload | When |
|---------|---------|------|
| `ethan.executor.task.assigned` | `{task_id, capability, params, retry_count}` | Task dispatched to module |
| `ethan.executor.task.running` | `{task_id}` | Module acknowledges start |
| `ethan.executor.task.completed` | `{task_id, result, duration_ms}` | Module returns success |
| `ethan.executor.task.failed` | `{task_id, error, attempt}` | Max retries exceeded |
| `ethan.executor.task.timeout` | `{task_id, timeout_ms}` | Deadline exceeded |
| `ethan.executor.task.retrying` | `{task_id, delay_ms}` | Retry attempt scheduled |
| `ethan.executor.task.cancelled` | `{task_id, reason}` | Task cancelled |
| `ethan.executor.plan.done` | `{plan_id, results[], total_duration}` | All tasks complete |

### 4.2 Queue Group Configuration

| Subject | Queue Group | Purpose |
|---------|------------|---------|
| `ethan.executor.task.assigned.docker.build` | `module-docker-build` | Load balance Docker build tasks |
| `ethan.executor.task.assigned.docker.publish` | `module-docker-publish` | Load balance Docker publish tasks |
| `ethan.executor.task.assigned.memory.store` | `module-memory` | Load balance memory stores |
| `ethan.executor.task.assigned.*` | `module-<capability>` | Dynamic per capability |

---

## 5. Timeouts

Each task has two timeout levels:

| Level | Duration | Action |
|-------|----------|--------|
| **Soft** | `task.timeout` (configurable, default 30s) | Log warning, continue waiting |
| **Hard** | `task.timeout * 1.5` | Emit `task.timeout`, cancel task |

**Hard timeout flow**:
```
1. Executor starts timer when task.assigned is published
2. If hard timeout expires → publish executor.task.timeout
3. Executor marks task as failed (status: timeout)
4. If module later completes → result is discarded
```

---

## 6. Task Dependency Resolution

The executor uses topological sort to determine task execution order.

**Algorithm**:
```go
func resolveDependencies(tasks []Task) [][]Task {
    // 1. Build in-degree map, adjacency list
    indegree := make(map[string]int)
    next := make(map[string][]string)
    taskMap := make(map[string]Task)

    for _, t := range tasks {
        taskMap[t.ID] = t
        if _, ok := indegree[t.ID]; !ok {
            indegree[t.ID] = 0
        }
        for _, dep := range t.DependsOn {
            next[dep] = append(next[dep], t.ID)
            indegree[t.ID]++
        }
    }

    // 2. Topological sort into levels
    var levels [][]Task
    queue := []string{}
    for id, deg := range indegree {
        if deg == 0 {
            queue = append(queue, id)
        }
    }

    for len(queue) > 0 {
        level := []Task{}
        var nextQueue []string
        for _, id := range queue {
            level = append(level, taskMap[id])
            for _, nid := range next[id] {
                indegree[nid]--
                if indegree[nid] == 0 {
                    nextQueue = append(nextQueue, nid)
                }
            }
        }
        levels = append(levels, level)
        queue = nextQueue
    }

    return levels
}
```

**Example**:
```
Tasks: [A, B, C, D]
Dependencies: C → A, D → B, D → C

Level 0: [A, B]       (parallel)
Level 1: [C]          (depends on A)
Level 2: [D]          (depends on B, C)
```

---

## 7. Cancellation Propagation

When a task is cancelled, all downstream tasks are also cancelled.

**Flow**:
```
Task A fails → Executor emits task.cancelled for A
    │
    ▼
Executor checks: which tasks depend on A?
    │
    ▼
Tasks B, C (depends on A) → cancelled (not assigned)
    │
    ▼
Tasks D, E (depends on B) → cancelled (never started)
    │
    ▼
Plan result: partially failed
```

---

## 8. Retry Configuration

Per-capability retry defaults (overridable by task params):

```json
{
  "docker.build": {
    "max_retries": 2,
    "initial_delay_ms": 2000,
    "backoff_factor": 2.0,
    "max_delay_ms": 30000
  },
  "web.fetch": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "backoff_factor": 1.5,
    "max_delay_ms": 15000
  },
  "memory.store": {
    "max_retries": 1,
    "initial_delay_ms": 500,
    "backoff_factor": 1.0,
    "max_delay_ms": 5000
  }
}
```

---

## 9. Concurrency Model Summary

| Feature | Mechanism | Scope |
|---------|-----------|-------|
| Parallel tasks | Go goroutines + `sync.WaitGroup` | Per-plan (Level 0 tasks execute together) |
| Queue groups | NATS queue groups | Load balance across module instances |
| Cancellation | `context.Context` + cancel events | Per-task, propagates to dependents |
| Retry | Exponential backoff loop | Per-task, configurable per capability |
| Timeouts | `time.After` + cancel | Per-task, hard timeout = soft * 1.5 |
| Ordering | Topological sort | Per-plan task DAG |