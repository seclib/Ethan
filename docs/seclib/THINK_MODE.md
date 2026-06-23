# ETHAN Think Mode

## Philosophy

`ethan think` exposes ETHAN's reasoning in a **structured, digestible way**. Users see the plan and phases without raw internals. It's a window into the cognitive process — not a debug dump.

---

## 1. Command

```
ethan think <task>
```

Example:
```
◆  ethan  ◇  idle  ▸ think deploy api to staging
```

---

## 2. Output Structure

### 2.1 Plan Generation (always shown)

```
◆  Plan generated
  Goal:     Deploy api to staging
  Steps:    5
  Duration: est. 2m 30s

  1.  Build Docker image
  2.  Push to registry
  3.  Update Kubernetes manifest
  4.  Roll out deployment
  5.  Run health checks
```

### 2.2 Execution Phases (always shown)

During execution, phases update in place:

```
◆  Executing  ◇  2/5 steps
  ✓  Build Docker image               (12.3s)
  ✓  Push to registry                (8.1s)
  ◐  Update Kubernetes manifest     (running...)
  ─  Roll out deployment             (pending)
  ─  Run health checks               (pending)
```

### 2.3 Completion

```
◆  Complete  ◇  deploy api to staging
  ✓  All steps executed successfully
  ⏱  2m 14s

  Next:
  → check staging health
  → run integration tests
```

---

## 3. Visibility Levels

### 3.1 Default (`ethan think <task>`)

Shows:
- Plan summary (goal, steps, estimate)
- Step execution status (spinner + checkmarks)
- Final result + next actions

Hides:
- Internal task IDs
- Raw capability names
- Low-level parameters
- Registry lookups

### 3.2 Verbose (`ethan think <task> --verbose`)

Shows everything from default, plus:
- Capability names (`docker.build`, `k8s.deploy`)
- Task IDs
- Timing per phase

### 3.3 Quiet (`ethan think <task> --quiet`)

Shows only:
- Final result (success or error)

---

## 4. UX Patterns

### 4.1 Spinner States

| State | Icon | Color |
|-------|------|-------|
| Pending | `─` | Dim |
| Running | `◐` | Purple |
| Success | `✓` | Green |
| Failed | `✗` | Red |

### 4.2 Timing Display

- Show per-step duration after completion: `(12.3s)`
- Show total duration at end: `⏱ 2m 14s`
- Estimate upfront: `est. 2m 30s`

### 4.3 Error Handling

```
◆  Failed  ◇  deploy api to staging
  ✗  Push to registry
    → exit code 1
    → try: ethan logs --follow
```

Partial progress preserved. User can resume or retry.

---

## 5. Implementation

### 5.1 Command Handler

File: `cli/commands/think.py`

```python
@register("think")
def cmd_think(args):
    task = " ".join(args)
    ThinkRunner(task).run()
```

### 5.2 Runner

```python
class ThinkRunner:
    def __init__(self, task: str, verbose: bool = False):
        self.task = task
        self.verbose = verbose

    def run(self):
        plan = self.plan(self.task)
        self.show_plan(plan)
        result = self.execute(plan)
        self.show_result(result)
```

### 5.3 Phases

```
1. Plan    → Query registry, decompose goal
2. Execute → Run steps sequentially with status
3. Report → Aggregate results, suggest next actions
```

---

## 6. Integration

- Uses `cli/core/loading.py` (`StepProgress`, `Thinker`)
- Uses `cli/core/output.py` (section headers, timing, tables)
- Uses `cli/core/intent.py` (suggest next actions)
- Emits `planner.plan.created` and `executor.plan.done` events
- Respects `--verbose` and `--quiet` flags

---

## 7. Examples

### 7.1 Simple Task

```
◆  ethan  ◇  idle  ▸ think check docker health

◆  Plan generated
  Goal:     Check docker health
  Steps:    2
  Duration: est. 10s

  1.  Run docker diagnostics
  2.  Report status

◆  Executing  ◇  1/2
  ✓  Run docker diagnostics           (3.2s)
  ◐  Report status                   (running...)

◆  Complete  ◇  check docker health
  ✓  Docker is healthy
  ⏱  3.5s
```

### 7.2 Complex Task (verbose)

```
◆  ethan  ◇  idle  ▸ think deploy api --verbose

◆  Plan generated
  Goal:     Deploy api to staging
  Steps:    5
  Duration: est. 2m 30s

  1.  [docker.build] Build Docker image
  2.  [registry.push] Push to registry
  3.  [k8s.manifest] Update Kubernetes manifest
  4.  [k8s.rollout] Roll out deployment
  5.  [http.health] Run health checks

◆  Executing  ◇  3/5
  ✓  [docker.build] Build Docker image        (12.3s)
  ✓  [registry.push] Push to registry         (8.1s)
  ◐  [k8s.manifest] Update manifest          (running...)
  ─  [k8s.rollout] Roll out deployment        (pending)
  ─  [http.health] Run health checks          (pending)
```

---

## Appendix: Design Rules

- Never show raw stack traces
- Never show raw event payloads
- Capability names only in `--verbose`
- Always show at least one next action on completion
- Partial failures: show what succeeded, then error
- Keep plan summary under 10 steps (collapse if more)