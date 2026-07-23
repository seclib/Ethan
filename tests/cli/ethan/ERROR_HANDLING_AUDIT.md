# ETHAN CLI Error Handling Audit

## Executive Summary

The CLI has a **good structured error foundation** (`cli/core/errors.py`) but **inconsistent adoption** across commands. Most commands use ad-hoc `print()` error messages instead of the structured system, leading to:

- Inconsistent UX across commands
- Missing fallback suggestions in many places
- Generic exception catching that hides root causes
- No centralized error logging/reporting

---

## Error Taxonomy

### Structured Errors (cli/core/errors.py)

| Code | Type | Title | Has Suggestion? | Used Where? |
|---|---|---|---|---|
| SYS-001 | API | API unreachable | ✅ | errors.py only |
| CAP-001 | Capability | Capability not found | ✅ | errors.py only |
| CAP-002 | Execution | Command failed | ✅ | errors.py only |
| SYS-002 | Timeout | Timeout | ✅ | errors.py only |
| SYS-003 | Permission | Permission denied | ✅ | errors.py only |
| CMD-001 | Command | Unknown command | ✅ | errors.py only |
| CMD-002 | Input | Missing argument | ✅ | errors.py only |
| INP-002 | Input | Invalid session | ✅ | errors.py only |
| INP-003 | Input | File not found | ✅ | errors.py only |
| INP-001 | Input | Empty input | ✅ | errors.py only |

**Total structured errors**: 10 constructors defined, **0 used in actual commands**.

### Ad-hoc Errors (actual command code)

| Command | Error Pattern | User Message | Suggestion? |
|---|---|---|---|
| `cfg.py` | `print("usage: ...")` | usage string | ❌ No |
| `chat.py` | `print(clr.error(str(e)))` | Exception string | ❌ No |
| `daemon.py` | `print("usage: ...")` | usage string | ❌ No |
| `logs.py` | Silent (empty output) | (none) | ❌ No |
| `memory.py` | `print("usage: ...")` | usage string | ❌ No |
| `plugin.py` | `print("usage: ...")` | usage string | ❌ No |
| `service.py` | `print("usage: ...")` | usage string | ❌ No |
| `status.py` | Silent fallback | (none — just "OFFLINE") | ❌ No |
| `suggest.py` | Silent (empty output) | (none) | ❌ No |
| `registry.py` | `print(f"Unknown command: {cmd}")` | raw cmd name | ❌ No |
| `client.py` | Exception propagate | None (caller handles) | ❌ No |

---

## UX Issues

### 1. No stack traces exposed (✅ GOOD)
- `format_error()` has `debug=False` by default
- `_format_traceback()` only called when explicitly enabled
- Generic exceptions in `dispatch()` caught and printed as `"Error: {e}"`

### 2. Meaningful error messages (⚠️ PARTIAL)
**Good**: Structured errors have codes, titles, context, suggestions
**Bad**: Actual commands don't use them — they print raw strings

**Example - daemon.py**:
```python
if not args or args[0] not in ("start", "stop", "status"):
    print("usage: ethan daemon <start|stop|status>")  # Bare minimum
    return 1
```

**Example - registry.py dispatch()**:
```python
if not fn:
    print(f"Unknown command: {cmd}")  # No suggestion
    return 1
```

**Example - chat.py**:
```python
except Exception as e:
    print(clr.error(str(e)))  # Raw exception text
    continue
```

### 3. Fallback suggestions (⚠️ PARTIAL)
- `cli/core/ux.py` has `UX.suggest_command()` for typos
- `cli/core/discovery.py` has `registry.suggest()` for command suggestions
- **But these are never called** from actual error paths

**Current flow for unknown command**:
1. `dispatch(["noneawesome"])`
2. `print("Unknown command: awesome")`
3. Return 1

**Expected flow**:
1. `dispatch(["noneawesome"])`
2. `UX.suggest_command("noneawesome", list(COMMANDS))` → "chat"
3. `print(error("Unknown command", suggestion="Did you mean? chat"))`
4. Return 1

### 4. Network errors handled (✅ GOOD)
- `alive()` returns `False` on any exception
- `get_state()` returns `None` on any exception
- `send()` now has retry + circuit breaker (after recent fix)
- `cmd_chat` shows "API unreachable" when `alive()` is False

### 5. Invalid command suggestions (❌ MISSING)
- `cmd_daemon` shows usage but no suggestion for typos
- `cmd_memory` shows usage but no suggestion
- `cmd_plugin` shows "Unknown subcommand" but no suggestion
- `registry.dispatch` shows "Unknown command" but no suggestion

---

## Missing Handlers

### Critical Missing Error Paths

| Scenario | Expected | Actual | Gap |
|---|---|---|---|
| Unknown command `chatt` | "Did you mean? chat" | "Unknown command: chatt" | No fuzzy match |
| Missing daemon subcommand | "Usage: ethan daemon <start\|stop\|status>" | Same | OK but no suggestion |
| Invalid plugin subcommand | "Did you mean? install/remove/list" | "Unknown subcommand: xyz" | No suggestion |
| Memory invalid subcommand | "Usage: ethan memory [recent\|frequent]" | Same | OK but no suggestion |
| Timeout in chat | "Timeout: request exceeded 5s — try: ethan run --timeout 10" | Raw exception text | Not using `timeout()` |
| Connection refused in chat | Structured error with suggestion | Raw `URLError` text | Not using `api_unreachable()` |
| Config file corrupt | Fallback to defaults silently | Same | OK but no user feedback |

### Command-Level Error Gaps

**`cli/commands/chat.py`**:
```python
except Exception as e:
    print(clr.error(str(e)))  # ❌ Raw exception
    continue
```
**Should be**:
```python
except ValueError as e:
    print(error(str(e), suggestion="type a message or /exit to quit"))
except URLError as e:
    print(api_unreachable())
except Exception as e:
    print(format_error(EthanError("SYS-999", "Unexpected error", str(e))))
```

**`cli/commands/daemon.py`**:
```python
if not args or args[0] not in ("start", "stop", "status"):
    print("usage: ethan daemon <start|stop|status>")  # ❌ No suggestion
    return 1
```
**Should use**: `missing_argument()` or structured error with suggestion

**`cli/commands/plugin.py`**:
```python
else:
    print(f"Unknown subcommand: {sub}")  # ❌ No suggestion
    return 1
```
**Should use**: `UX.suggest_command(sub, ["install", "remove", "list"])`

**`cli/registry.py` dispatch()**:
```python
if not fn:
    print(f"Unknown command: {cmd}")  # ❌ No suggestion
    return 1
```
**Should use**: `unknown_command()` with fuzzy match

---

## Error Flow in Current Commands

### chat.py
```
send() raises URLError
  → cmd_chat catches Exception
    → print(clr.error(str(e)))
      → Raw traceback text shown to user
```

### status.py
```
alive() returns False
  → print("OFFLINE")
    → Silent, no suggestion
```

### daemon.py
```
args[0] not in ("start", "stop", "status")
  → print("usage: ...")
    → Bare minimum, no help
```

### registry.py dispatch()
```
cmd not in COMMANDS
  → print(f"Unknown command: {cmd}")
    → No fuzzy match, no suggestion
```

---

## Fixes Required

### 1. [HIGH] Use structured errors in all commands

**Pattern to follow**:
```python
from cli.core.errors import EthanError, format_error, unknown_command, missing_argument
from cli.core.ux import UX

# Instead of: print("usage: ...")
# Use:
if not args:
    print(format_error(missing_argument("subcommand", "ethan <cmd> <sub>", "ethan daemon start")))
    return 1
```

### 2. [HIGH] Add fuzzy suggestions for unknown commands

**In `cli/registry.py`**:
```python
if not fn:
    from cli.core.ux import UX
    suggestion = UX.suggest_command(cmd, list(COMMANDS.keys()))
    if suggestion:
        print(format_error(unknown_command(cmd, f"Did you mean? {suggestion}")))
    else:
        print(format_error(unknown_command(cmd)))
    return 1
```

### 3. [MEDIUM] Standardize exception handling in chat

**In `cli/commands/chat.py`**:
```python
from cli.core.errors import api_unreachable, timeout, format_error

try:
    response_text = send_with_typing(msg, session_id)
except ValueError as e:
    print(error(str(e), suggestion="type a message or /exit to quit"))
    continue
except URLError as e:
    if "timed out" in str(e).lower():
        print(format_error(timeout(5)))
    else:
        print(format_error(api_unreachable()))
    continue
except Exception as e:
    print(format_error(EthanError("SYS-999", "Unexpected error", str(e))))
    continue
```

### 4. [MEDIUM] Add suggestions for invalid subcommands

**Pattern for all commands with subcommands**:
```python
KNOWN_SUBS = ["start", "stop", "status"]
if args[0] not in KNOWN_SUBS:
    from cli.core.ux import UX
    suggestion = UX.suggest_command(args[0], KNOWN_SUBS)
    msg = f"Did you mean? {suggestion}" if suggestion else f"try: ethan {cmd_name} <{'|'.join(KNOWN_SUBS)}>"
    print(format_error(EthanError("CMD-001", f"Unknown subcommand: '{args[0]}'", "", msg)))
    return 1
```

### 5. [LOW] Centralized error handler in dispatch

**In `cli/registry.py`**:
```python
def dispatch(argv):
    ...
    try:
        return fn(args)
    except SystemExit:
        raise
    except EthanError as e:
        print(format_error(e))
        return e.code if hasattr(e, 'code') else 1
    except Exception as e:
        print(format_error(EthanError("SYS-999", "Unexpected error", str(e))))
        return 1
```

### 6. [LOW] Add `--debug` flag for stack traces

The infrastructure exists (`format_error(err, debug=True)`) but there's no way to enable it. Add a global debug flag or `--debug` CLI flag.

---

## Priority Action Items

| Priority | Action | Impact |
|---|---|---|
| **HIGH** | Replace ad-hoc `print()` errors with `format_error()` in all commands | UX consistency |
| **HIGH** | Add fuzzy suggestions in `dispatch()` for unknown commands | Discoverability |
| **MEDIUM** | Standardize exception hierarchy in `chat.py` | Better error context |
| **MEDIUM** | Add `UX.suggest_command()` to all subcommand parsers | Confused users |
| **LOW** | Global `--debug` flag for stack traces | Developer UX |
| **LOW** | Error logging to file (not just stdout) | Debugging |

## Current Error System Rating

| Criterion | Rating | Notes |
|---|---|---|
| Stack traces hidden | ✅ 10/10 | `debug=False` default, truncation |
| Meaningful messages | ⚠️ 4/10 | Good structured errors exist but not used |
| Fallback suggestions | ⚠️ 3/10 | Infrastructure exists, never called |
| Network errors handled | ✅ 8/10 | Good retry/circuit breaker now |
| Invalid command suggestions | ❌ 2/10 | No fuzzy matching in error paths |

**Overall**: The error *system* is well-designed, but the error *adoption* across commands is poor. Most commands use bare `print()` instead of the structured error framework.