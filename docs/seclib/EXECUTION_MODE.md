# ETHAN Execution Mode

## Philosophy

`ethan run` transforms the CLI from a command runner into an **agent executor**. Tasks are decomposed into phases, capabilities are surfaced, progress is visible, and the user stays in control. Not a script — a cognitive runtime.

---

## 1. Command

```
ethan run <task> [flags]
```

Examples:
```
ethan run docker build
ethan run deploy api --verbose
ethan run tests --timeout 60
```

---

## 2. Phases

Every execution follows these phases:

| Phase | Icon | Description |
|-------|------|-------------|
| **Plan** | `▪` | Decompose task into steps |
| **Execute** | `◐` | Run steps sequentially or parallel |
| **Verify** | `◉` | Validate results |
| **Report** | `◆` | Summarize outcome |

### 2.1 Plan Phase

```
◆  Plan  ◇  docker build

  Goal:    Build Docker image
  Strategy: Sequential (3 steps)

  1.  Build image
  2.  Tag image
  3.  Push to registry
```

### 2.2 Execute Phase

```
◆  Executing  ◇  1/3

  ◐  Build image                   docker.build
      Context: myapp:latest

  ─  Tag image                     (pending)
  ─  Push to registry              (pending)
```

### 2.3 Verify Phase

```
◆  Verifying  ◇  1/1

  ◉  Checking image integrity...
```

### 2.4 Report Phase

```
◆  Complete  ◇  docker build

  ✓  Image built successfully
  ✓  Tagged: myapp:latest
  ✓  Pushed: registry.example.com/myapp:latest

  Capabilities used:
    → docker.build
    → docker.tag
    → registry.push

  ⏱  45.2s

  Next:
  → deploy myapp
  → run tests
```

---

## 3. Visibility Levels

### 3.1 Default (`ethan run <task>`)

Shows:
- Phase headers
- Step names + status icons
- Final result
- Next actions

Hides:
- Capability names (shows human-readable step names)
- Raw parameters
- Internal IDs

### 3.2 Verbose (`ethan run <task> --verbose`)

Shows everything from default, plus:
- Capability names (`docker.build`, `k8s.deploy`)
- Step parameters
- Timing per step

### 3.3 Quiet (`ethan run <task> --quiet`)

Shows only:
- Final result (success or error)

---

## 4. Progress Display

### 4.1 Step Status Icons

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| Pending | `─` | Dim | Waiting |
| Running | `◐` | Purple | In progress |
| Success | `✓` | Green | Done |
| Failed | `✗` | Red | Error |
| Skipped | `○` | Dim | Not run |

### 4.2 Progress Bar

For multi-step tasks:

```
  ▓▓▓▓▓▓▓▓▓░░░░░░  50%  (3/6 steps)
```

- Filled: `▓` (purple on TTY, `#` otherwise)
- Empty: `░` (dim)
- Percentage on the right

### 4.3 Timing

- Per-step: show duration after completion `(12.3s)`
- Total: `⏱ 2m 14s`
- Estimate: shown in plan phase `est. 2m 30s`

---

## 5. Interruption

### 5.1 CTRL+C Behavior

```
User: ethan run deploy api
  │
  ▼
◐  Building image...
  [CTRL+C]
  │
  ▼
✗  Interrupted
  → Partial progress preserved
  → Resume: ethan run deploy api --continue
```

### 5.2 Resume

```
ethan run deploy api --continue
```

- Continues from last completed step
- Shows resumed state:
```
◆  Resumed  ◇  step 2/3
  ✓  Build image (already complete)
  ◐  Tag image (resuming...)
```

### 5.3 Cleanup

On interrupt:
- Stop current capability
- Preserve completed work
- Save state for resume
- Show partial results if available

---

## 6. Capability Display

### 6.1 Human-Readable Names

Default mode uses friendly names:

```
  ◐  Building Docker image
```

### 6.2 Capability Names (verbose)

```
  ◐  Building Docker image          [docker.build]
      Params: image=myapp, tag=latest
```

### 6.3 Context

When relevant, show execution context:

```
  ◐  Deploying to staging
      Cluster: production-us
      Namespace: api
```

---

## 7. Output Structure

### 7.1 Success

```
◆  Complete  ◇  docker build

  ✓  Image built: myapp:latest
  ✓  Pushed to registry

  Capabilities:
    → docker.build
    → registry.push

  ⏱  45.2s

  Next:
  → deploy myapp
```

### 7.2 Failure

```
◆  Failed  ◇  docker build

  ✗  Push to registry
    → exit code 1
    → auth token expired

  Partial: 2/3 steps completed
  Resume:  ethan run docker build --continue

  What next?
  → check registry status
  → renew credentials
```

### 7.3 Partial Failure

```
◆  Partial  ◇  deploy api

  ✓  Build image
  ✗  Run tests (exit code 1)
  ─  Deploy (skipped)

  Stopped: test failure
  Resume: ethan run deploy api --continue
```

---

## 8. Implementation

### 8.1 Command Handler

File: `cli/commands/run.py`

```python
@register("run")
def cmd_run(args):
    task = " ".join(args)
    Executor(task).run()
```

### 8.2 Executor

```python
class Executor:
    def __init__(self, task: str, verbose: bool = False, resume: bool = False):
        self.task = task
        self.verbose = verbose
        self.resume = resume

    def run(self):
        plan = self.plan(self.task)
        self.show_plan(plan)
        result = self.execute(plan)
        self.show_result(result)
```

### 8.3 Phases

```
1. Plan    → Decompose task, show summary
2. Execute → Run steps with StepProgress
3. Verify  → Validate (optional)
4. Report  → Show results + next actions
```

---

## 9. Integration

| Component | Use |
|-----------|-----|
| `cli/core/loading.py` | `StepProgress` for step execution |
| `cli/core/colors.py` | Status icons, sections, timing |
| `cli/core/errors.py` | `execution_failed()`, `timeout()` |
| `cli/core/intent.py` | Suggest next actions |
| `cli/core/client.py` | API calls for capabilities |
| `kernel/bus/nats_bus.py` | Event publishing (step started/completed) |

---

## 10. UX Patterns

### 10.1 Long-Running Task

```
◆  Run  ◇  deploy api

  Planning...
  ✓  Plan ready (3 steps, est. 2m)

  Executing  ◇  1/3
  ◐  Build image...
```

### 10.2 Parallel Steps

```
  Executing  ◇  2/4
  ✓  Step 1 (12s)
  ◐  Step 2 (running...)
  ◐  Step 3 (running...)
  ─  Step 4 (pending)
```

### 10.3 Cancelled

```
  Executing  ◇  1/3
  ✓  Step 1 (5s)

  ✗  Interrupted
  → Partial: 1/3 steps
  → Resume: ethan run <task> --continue
```

---

## Appendix: Design Rules

- Never expose raw internal state (task IDs, event payloads)
- Always show at least one next action on completion
- Capability names only in `--verbose`
- Max 10 steps shown (collapse additional as "... and N more")
- Always preserve partial results on interruption