# ETHAN CLI Error System

## Philosophy

Errors are not failures — they are **conversation opportunities**. Every error must:
- Be human-readable (no jargon)
- Suggest a fix
- Include a next action
- Avoid stack traces (unless `--debug`)

Claude Code style: helpful, concise, never SHOUT.

---

## 1. Error Anatomy

```
✗ <title>                        <- red, bold, one line
  → <context>                     <- dim, optional
  → <suggestion>                  <- cyan, actionable
```

**Rules**:
- Max 1 title line
- Max 2 suggestion lines
- No stack traces in default mode
- Always include at least one suggestion

---

## 2. Error Categories

### 2.1 System Errors

| Code | Title | Context | Suggestion |
|------|-------|---------|------------|
| `SYS-001` | API unreachable | ethan daemon may be stopped | try: ethan daemon start |
| `SYS-002` | Timeout | request exceeded 10s | try: ethan status --verbose |
| `SYS-003` | Permission denied | plugin requires admin | run as: sudo ethan ... |

### 2.2 Command Errors

| Code | Title | Context | Suggestion |
|------|-------|---------|------------|
| `CMD-001` | Unknown command | 'strat' | Did you mean? ethan status |
| `CMD-002` | Missing argument | <cmd> | Usage: ethan run <cmd> |
| `CMD-003` | Invalid flag | --unknown | try: ethan --help |

### 2.3 Capability Errors

| Code | Title | Context | Suggestion |
|------|-------|---------|------------|
| `CAP-001` | Capability not found | docker.build | try: ethan plugin list |
| `CAP-002` | Execution failed | exit code 1 | try: ethan logs --follow |
| `CAP-003` | Capability timeout | 30s elapsed | try: ethan run --timeout 60 |

### 2.4 Input Errors

| Code | Title | Context | Suggestion |
|------|-------|---------|------------|
| `INP-001` | Empty input | no text provided | type a command or message |
| `INP-002` | Invalid session | session expired | try: ethan chat --resume |
| `INP-003` | File not found | /path/to/file | check the path and try again |

---

## 3. Error Rendering

### 3.1 Basic Error

```python
error("API unreachable", "ethan daemon may be stopped", "try: ethan daemon start")
```

Output:
```
✗ API unreachable
  → ethan daemon may be stopped
  → try: ethan daemon start
```

### 3.2 Error with Code

```python
error("SYS-001", "API unreachable", ...)
```

Output:
```
✗ SYS-001: API unreachable
```

### 3.3 Multi-line Context

```python
error("Deploy failed",
      "service: api-gateway\n  exit code: 1",
      "check logs: ethan logs --follow")
```

Output:
```
✗ Deploy failed
  → service: api-gateway
    exit code: 1
  → check logs: ethan logs --follow
```

---

## 4. Next Action Suggestion

Every error MUST end with a next action. Patterns:

| Pattern | Example |
|---------|---------|
| `try: <command>` | `try: ethan daemon start` |
| `run: <command>` | `run: ethan logs --follow` |
| `check: <thing>` | `check: docker is running` |
| `see: <doc>` | `see: docs/errors.md` |
| `Did you mean? <cmd>` | `Did you mean? ethan status` |

---

## 5. Stack Trace Policy

### 5.1 Default (no stack trace)

```
✗ Connection refused
  → host: localhost:4222
  → try: ethan daemon start
```

### 5.2 Debug mode (`--debug`)

```
✗ Connection refused
  → host: localhost:4222
  → try: ethan daemon start

  Traceback (most recent call last):
    File ".../client.py", line 42, in send
      urlopen(req, timeout=10)
  ConnectionRefusedError: [Errno 111] Connection refused
```

### 5.3 Rules

- Stack traces ONLY with `--debug` flag
- Always truncate to last 3 frames
- Never log secrets in traces
- Sanitize paths (replace home dir with `~`)

---

## 6. Error Recovery

### 6.1 Retry Suggestion

```
✗ Network timeout
  → request to localhost:8000 timed out
  → Retry in 2s... (attempt 2/3)
```

### 6.2 Fallback Suggestion

```
✗ Streaming failed
  → Connection lost
  → Falling back to batch result
```

### 6.3 Recovery Actions

| Error | Auto-fix | Manual |
|-------|----------|--------|
| API unreachable | retry 3x | start daemon |
| Capability missing | suggest install | ethan plugin install |
| File not found | - | check path |
| Permission denied | - | sudo / chmod |

---

## 7. Implementation

### 7.1 Error Class

```python
class EthanError(Exception):
    def __init__(self, code, title, context="", suggestion=""):
        self.code = code
        self.title = title
        self.context = context
        self.suggestion = suggestion
```

### 7.2 Renderer

```python
def format_error(err: EthanError, debug: bool = False) -> str:
    ...
```

### 7.3 Integration

```python
try:
    ...
except EthanError as e:
    print(format_error(e))
except Exception as e:
    print(format_error(EthanError("UNKNOWN", str(e))))
```

---

## 8. UX Guidelines

| Do | Don't |
|----|-------|
| Say what happened | Say "Error" |
| Say why it happened | Blame the user |
| Say how to fix it | Say "invalid input" |
| Be specific | Be vague |
| Be calm | SHOUT IN CAPS |
| Show code, not traces | Expose internals |

---

## Appendix A: Error Codes

```
SYS-001  API unreachable
SYS-002  Timeout
SYS-003  Permission denied

CMD-001  Unknown command
CMD-002  Missing argument
CMD-003  Invalid flag

CAP-001  Capability not found
CAP-002  Execution failed
CAP-003  Capability timeout

INP-001  Empty input
INP-002  Invalid session
INP-003  File not found
```

---

## Appendix B: Tone Examples

Bad:
```
Error: Invalid input
Usage: ethan <cmd> [args]
```

Good:
```
✗ Unknown command: 'strat'
  → Did you mean? ethan status
  → Try: ethan --help
```

Bad:
```
Connection refused
```

Good:
```
✗ API unreachable
  → ethan daemon may be stopped
  → try: ethan daemon start