# ETHAN CLI Loading States System

## Philosophy

The CLI must feel **alive**. Every wait should communicate progress. No dead screens. No silent hangs. The user always knows what ETHAN is doing.

---

## 1. Core Concepts

### 1.1 Loading State Types

| Type | Use Case | Duration |
|------|----------|----------|
| **Spinner** | Indeterminate wait | < 5s |
| **Progress** | Known total (steps, bytes, %) | Variable |
| **Thinking** | LLM/planning wait | 2s – 30s |
| **Step-based** | Multi-phase pipeline | Long |
| **Streaming** | Token/chunk output | Variable |

### 1.2 Design Principles

- **Never block the UI** — always show something
- **Animate when idle** — spinner proves the process is alive
- **Show progress when possible** — percentage/step > spinner
- **Always cancellable** — CTRL+C works at any point
- **Graceful degradation** — no ANSI? still readable

---

## 2. Spinner Styles

### 2.1 Available Styles

| Style | Frames | Use |
|-------|--------|-----|
| `dots` | `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` | Default, gentle |
| `arrow` | `←↖↑↗→↘↓↙` | Directional movement |
| `bounce` | `⠁⠂⠄⠠⠐⠈` | Playful, short ops |
| `line` | `-\|/` | Classic, minimal |
| `pulse` | `●○○●○` | Heartbeat-like |
| `thinking` | `🤔🤔🤔` (fallback: `...`) | LLM calls only |

### 2.2 Usage

```python
spinner = Spinner("dots")
spinner.start("Querying registry...")
# ... do work ...
spinner.stop()
```

Output:
```
⠋ Querying registry...
```

### 2.3 Spinner Rules

- Frame interval: 80ms (12.5 FPS)
- 2-space indent
- Always show hint text after spinner
- On cancel: show `✗ Cancelled` on same line

---

## 3. Thinking Indicator

### 3.1 Visual

```
◆  ethan  ◇  thinking  ▸
  ■  Analyzing intent...
```

- Purple animated dot (`■`) rotates through spinner frames
- Static text: "Analyzing intent..." / "Decomposing goal..."
- Prompt shows `thinking` state badge

### 3.2 Thinking Phases

| Phase | Indicator | Example |
|-------|-----------|---------|
| Intent analysis | `■ Analyzing intent...` | Parsing user input |
| Planning | `■ Building task plan...` | Decomposing goal |
| Execution | `■ Executing tasks...` | Running modules |
| Response | `■ Composing response...` | Formatting output |

### 3.3 Rules

- Multiple phases: update text, keep spinner running
- Cancel at any phase: cleanup, show partial context
- Max thinking time: 30s (then fallback to static `...`)

---

## 4. Progress Bar (Step-based)

### 4.1 Visual

```
  [████████░░░░]  67%  (3/5 plugins installed)
```

or step-based:

```
  ◐ Planning...                           ← step indicator
  ├─ Querying capabilities...             ← sub-step
  ├─ Decomposing goal...                  ← sub-step
  └─ Assigning tasks...                   ← sub-step
```

### 4.2 step() Function

```python
loader = StepProgress()
loader.begin("Deploying", total=3)
loader.step("Building image...")
loader.step("Pushing registry...")
loader.step("Starting service...")
loader.complete("Deployed")
```

Output:
```
◆  Deploying
  ◐ Building image...                       (0.5s)
  ◐ Pushing registry...                    (1.2s)
  ◐ Starting service...                    (0.3s)
  ✓ Deployed                               (2.0s)
```

### 4.3 Rules

- Each step: spinner + hint + duration
- Steps run sequentially
- On failure: mark failed, continue to error block
- Max width: 12 blocks (`█░`)
- Percentage calculated: current/total

---

## 5. Cancellable Operations

### 5.1 Cancellation Flow

```
User presses CTRL+C
    │
    ▼
Operation detects KeyboardInterrupt
    │
    ▼
Cleanup:
  - Stop spinner
  - Clear line
  - Preserve partial output
  - Emit cancelled state
    │
    ▼
Display:
  ✗ Cancelled
  → Partial output preserved
  → Resume with: ethan run <same>
```

### 5.2 Implementation

```python
class CancellableTask:
    def __init__(self):
        self._cancelled = False

    def run(self):
        try:
            # long operation
            while not self.done:
                if self._cancelled:
                    self.on_cancel()
                    return
                self.tick()
        except KeyboardInterrupt:
            self._cancelled = True
            self.on_cancel()

    def cancel(self):
        self._cancelled = True
```

### 5.3 Cancellation Messages

| Context | Message |
|---------|---------|
| Spinner cancelled | `✗ Cancelled` |
| Step progress cancelled | `✗ Deploy cancelled — partial build preserved` |
| Streaming cancelled | `✗ Response cancelled` |

---

## 6. Complete State Machine

```
IDLE ──► SPINNER ──► DONE
  │        │
  │        ├──► PROGRESS ──► DONE
  │        │
  │        └──► THINKING ──► DONE
  │                             │
  └──► CANCELLED ◄──────────────┘
         │
         └──► RETRY? (optional)
```

| Transition | Trigger |
|------------|---------|
| IDLE → SPINNER | `spinner.start()` |
| SPINNER → PROGRESS | `spinner.stop()` + `progress.start()` |
| PROGRESS → THINKING | Phase change (e.g. planning → executing) |
| ANY → CANCELLED | CTRL+C |
| ANY → DONE | Operation completes |
| CANCELLED → IDLE | User enters new command |

---

## 7. Integration with Streamer

`Streamer` from `core/streaming.py` handles:
- In-place line updates
- Spinner integration
- Cancellation via `KeyboardInterrupt`
- Fallback mode

```python
with Streamer() as s:
    for chunk in api.stream(prompt):
        s.write(chunk)
    s.done()
```

If CTRL+C:
- Streamer catches `KeyboardInterrupt`
- Calls `self.cancel()`
- Prints `✗ Cancelled`
- Caller sees `None` result

---

## 8. API

```python
class Spinner:
    def __init__(self, style: str = "dots")
    def start(self, hint: str = "") -> None
    def stop(self) -> None
    def cancel(self) -> None

class StepProgress:
    def begin(self, title: str, total: int) -> None
    def step(self, hint: str) -> None
    def complete(self, title: str) -> None
    def fail(self, hint: str) -> None

class Thinker:
    def begin(self, phase: str) -> None
    def update(self, phase: str) -> None
    def done(self) -> None
    def cancel(self) -> None
```

---

## 9. Terminal Compatibility

| Feature | TTY | Pipe | CI |
|---------|-----|------|----|
| Spinner animation | ✅ | ❌ | ❌ |
| Colors | ✅ | ✅ (if -t) | ❌ |
| Unicode | ✅ | ✅ | ❌ |
| Progress bar | ✅ | ✅ | ✅ (text) |

Detection:
```python
def is_tty() -> bool:
    return sys.stdout.isatty()

if not is_tty():
    # fallback to text-only, no animation
```

---

## Appendix A: Spinner Reference

```
dots:    ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
arrow:   ←↖↑↗→↘↓↙
bounce:  ⠁⠂⠄⠠⠐⠈
line:    -\|/
pulse:   ●○○●○