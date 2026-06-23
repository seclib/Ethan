# ETHAN First-Run Experience

## Philosophy

First run must be **instant clarity**. No walls of text. No tutorials. Just enough to say "you're ready" and give the first command.

---

## 1. Welcome Screen

### 1.1 Minimal Welcome

```
◆  ETHAN is ready

  Your cognitive runtime is online.
  /help for commands
```

### 1.2 Expanded Welcome (first time only)

```
◆  ETHAN is ready

  Your cognitive runtime is online.

  Quick start:
    ethan chat            Start AI conversation
    ethan run <task>      Execute a task
    ethan status          Show system state

  /help for commands
```

Rules:
- Max 10 lines total
- No ASCII art
- No feature lists
- One quick-start section only

---

## 2. System Check (optional, --check)

```
◆  Checking system...

  ✓  API reachable          localhost:8000
  ✓  Event bus connected    nats://localhost:4222
  ✓  Memory ready           ~/.ethan
  ○  Plugins                none installed

  All systems operational.
```

Skip if:
- `--no-check` flag passed
- Subsequent runs (not first run)

---

## 3. First Command Suggestion

### 3.1 Trigger

After welcome, if user doesn't type anything for 3 seconds:

```
◆  ethan  ◇  idle  ▸

  Try: ethan chat
```

### 3.2 On first real input

If user types something unrecognizable:

```
◆  ethan  ◇  idle  ▸ helo

✗ Unknown command: 'helo'
  → Did you mean? ethan help
  → Quick start: ethan chat
```

---

## 4. Flow

### 4.1 First Run

```
1. ethan
   │
   ▼
2. Show welcome (minimal)
   │
   ▼
3. Optionally run system check (--check)
   │
   ▼
4. Show quick command examples
   │
   ▼
5. Prompt ready: ◆ ethan ◇ idle ▸
```

### 4.2 Subsequent Runs

```
1. ethan
   │
   ▼
2. Prompt ready immediately (no welcome)
```

### 4.3 With Flags

| Flag | Behavior |
|------|----------|
| `--check` | Run system check |
| `--no-welcome` | Skip welcome |
| `--help` | Show help, exit |
| `--version` | Show version, exit |

---

## 5. Detection

### 5.1 First Run Detection

```python
FIRST_RUN_MARKER = "~/.ethan/.installed"

def is_first_run() -> bool:
    return not os.path.exists(FIRST_RUN_MARKER)

def mark_installed():
    with open(FIRST_RUN_MARKER, "w") as f:
        f.write("installed")
```

### 5.2 Show Welcome

```python
if is_first_run() and not args.no_welcome:
    show_welcome()
    if args.check:
        show_system_check()
    mark_installed()
```

---

## 6. UX Patterns

### 6.1 On Empty Input (with timeout)

```
◆  ethan  ◇  idle  ▸

  Try: ethan chat
```

### 6.2 On Help Request

```
◆  ethan  ◇  idle  ▸ --help

  ETHAN — Cognitive Runtime CLI

  Commands:
    chat       Interactive AI chat
    run        Execute via capabilities
    status     Show system state
    logs       Tail system logs
    help       Show help
```

### 6.3 On Version Request

```
◆  ethan  ◇  idle  ▸ --version

  ethan 0.1.0
```

---

## 7. Anti-Patterns

| Avoid | Why |
|-------|-----|
| Long ASCII banner | Clutters terminal |
| Feature list | Users don't read on first run |
| Tutorial mode | Interrupts workflow |
| "Welcome to ETHAN!" | Too verbose |
| Multiple screens | One screen max |
| Forcing system check | Adds friction |

---

## Appendix: Welcome Screen Variations

### Minimal (default)

```
◆  ETHAN is ready

  /help for commands
```

### With Quick Start

```
◆  ETHAN is ready

  Quick start:
    ethan chat            Start AI conversation
    ethan run <task>      Execute a task
    ethan status          Show system state

  /help for commands
```

### With System Check

```
◆  ETHAN is ready

  ✓  API reachable
  ✓  Event bus connected
  ✓  Memory ready

  /help for commands