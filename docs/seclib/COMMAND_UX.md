# ETHAN Command UX Layer

## Philosophy

The CLI should feel like a **smart pair programmer**, not a manual. Zero friction. Every error teaches. Every hint guides.

---

## 1. Command Grammar

### 1.1 Structure

```
ethan <command> [args...] [flags...]
```

Minimal verbs, maximum clarity.

### 1.2 Core Commands

| Command | Purpose | Examples |
|---------|---------|---------|
| `ethan chat` | Interactive AI chat | `ethan chat`, `ethan chat --resume` |
| `ethan run <cmd>` | Execute a command in a capability | `ethan run docker build`, `ethan run pytest` |
| `ethan status` | Show kernel/system state | `ethan status`, `ethan status --verbose` |
| `ethan logs` | Tail system logs | `ethan logs --follow`, `ethan logs --lines 50` |
| `ethan plugin <sub>` | Manage plugins | `ethan plugin list`, `ethan plugin install <path>` |
| `ethan shell` | Drop into ethan-shell | `ethan shell` |
| `ethan help` | Show help | `ethan help`, `ethan help chat` |

---

## 2. Autocomplete Hints

### 2.1 Inline Suggestions (TAB)

```
◆  ethan  ◇  idle  ▸ ru<TAB>
                                └─► autocomplete to "run"
```

**Behavior**:
- Single TAB: complete to longest common prefix
- Double TAB: show all matches
- No match: bell (BEL char `\a`)

### 2.2 Context Suggestions

```
◆  ethan  ◇  idle  ▸ run
   Did you mean?               ← shown when no exact match
   → ethan run
   → ethan shell
   → ethan status
```

Triggered when:
- Command not found
- User pauses (200ms silence after typing)

### 2.3 Argument Suggestions

```
◆  ethan  ◇  idle  ▸ plugin <TAB>
   Commands: install  list  remove  info
```

---

## 3. Inline Help (--help)

### 3.1 Minimal Help (default)

```
◆  ethan  ◇  idle  ▸ chat --help

  ethan chat — interactive AI chat

  Usage:
    ethan chat              Start new session
    ethan chat --resume     Resume last session

  Flags:
    -r, --resume            Resume previous session
    -h, --help              Show this help
```

### 3.2 Top-level Help

```
◆  ethan  ◇  idle  ▸ --help

  ETHAN — Cognitive Runtime CLI

  Commands:
    chat       Interactive AI chat
    run        Execute a command via capabilities
    status     Show system state
    logs       Tail system logs
    plugin     Manage plugins
    shell      Open ethan-shell
    help        Show help

  Flags:
    -v, --version    Show version
    -h, --help       Show this help
```

### 3.3 Rules

- Max 4 lines per command description
-Flags indented under "Flags:"
- Examples shown only for complex commands
- Never show full man page by default

---

## 4. Typo Suggestions

### 4.1 Levenshtein Distance

```
Input:  ethan staatus
Suggestion: Did you mean?
  → ethan status (distance 2)
```

**Algorithm**:
1. Load all command names into a list
2. Calculate Levenshtein distance between input and each command
3. If distance <= 2 (for short) or <= 3 (for long), suggest it
4. Show best match first

### 4.2 Substring Match

```
Input:  ethan pla
Suggestion: Did you mean?
  → ethan plugin list
  → ethan plugin install
```

If input is a prefix of multiple commands, show all matches.

### 4.3 Phonetic Match (Soundex)

Future: handle phonetic typos (`ethan shel` → `ethan shell`).

---

## 5. Smart Error Messages

### 5.1 Unknown Command

```
◆  ethan  ◇  idle  ▸ strat

✗ Unknown command: 'strat'
  → Did you mean? ethan status
  → Try: ethan --help
```

### 5.2 Missing Argument

```
◆  ethan  ◇  idle  ▸ run

✗ Missing argument: <command>
  → Usage: ethan run <cmd>
  → Example: ethan run docker build
```

### 5.3 Failed Command

```
◆  ethan  ◇  idle  ▸ run docker build

✗ Command failed: docker build
  → Exit code 1
  → Context: /app
  → Try: ethan logs --follow
```

### 5.4 API Unreachable

```
◆  ethan  ◇  error  ▸ status

✗ API unreachable
  → ethan daemon may be stopped
  → try: ethan daemon start
```

### 5.5 Permission Denied

```
✗ Permission denied
  → plugin "danger" requires admin level
  → Run as: sudo ethan plugin install danger
```

---

## 6. Implementation

### 6.1 UX Module

File: `cli/core/ux.py`

```python
class UX:
    @staticmethod
    def suggest_command(input_str: str, commands: list[str]) -> str | None:
        """Return best matching command or None."""

    @staticmethod
    def levenshtein(a: str, b: str) -> int:
        """Calculate edit distance."""

    @staticmethod
    def show_help(topic: str | None = None) -> None:
        """Display minimal help."""

    @staticmethod
    def smart_error(kind: str, **context) -> str:
        """Generate actionable error block."""
```

### 6.2 Integration

Every command handler should:
1. Validate args
2. On failure: call `UX.smart_error()`
3. On unknown command: call `UX.suggest_command()`

---

## 7. UX Patterns Reference

| Situation | Response |
|-----------|----------|
| Unknown command | Suggest closest match + `--help` |
| Missing required arg | Show usage + example |
| Flag not recognized | Show valid flags |
| Command not available | Show install command (for plugins) |
| API error | Show actionable recovery message |
| KeyboardInterrupt | Graceful exit with "Cancelled" |
| Empty input | No feedback (silent) |
| Long output | Paginate or offer `--less` flag |

---

## 8. Anti-Patterns

| Pattern | Why |
|---------|-----|
| "Error: invalid input" | Not actionable — tell user what's valid |
| Stack traces by default | Use structured errors; show trace with `--debug` |
| "Usage: ethan <cmd> [args]" | Too vague — show specific command usage |
| Multiple errors at once | User can't parse; show first error, stop |
| CAPS LOCK emphasis | Only bold + color; never SHOUT |
| Silent failures | Always print something (error or hint) |

---

## Appendix A: UX Copy Guidelines

- **Tone**: helpful colleague, not robot
- **Length**: 1-2 lines max for errors
- **Action**: every error ends with a suggestion or next step
- **Humor**: minimal, never at user's frustration
- **Consistency**: same wording for same concepts (`try:`, `Usage:`, `Example:`)

---

## Appendix B: Minimal Help Format

```
<verb> — <one-line description>

Usage:
  ethan <verb> <required> [optional]

Flags:
  -x, --flag    Description
  -h, --help    Show help