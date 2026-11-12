# ETHAN CLI Error Handling — Fixes Applied

## Summary

Applied error handling improvements across the CLI to make errors user-friendly, consistent, and actionable.

---

## Changes Applied

### 1. `cli/registry.py` — Centralized dispatch error handling
- **Unknown commands**: Now uses `UX.suggest_command()` for fuzzy matching
- **Structured errors**: Uses `format_error()` and `unknown_command()` from `cli/core/errors.py`
- **Exception handling**: Catches generic exceptions and formats them as `EthanError("SYS-999", ...)`
- **Suggestion on typos**: "Did you mean? chat" when user types "chatt"

**Before**:
```
Unknown command: chatt
```

**After**:
```
✗ Unknown command: 'chatt'
  → Did you mean? chat
  → Try: ethan --help
```

---

### 2. `cli/commands/chat.py` — Standardized exception handling
- Added imports: `format_error`, `api_unreachable`, `timeout`, `EthanError`
- **ValueError**: Shows suggestion "type a message or /exit to quit"
- **ConnectionError**: Shows structured `api_unreachable()` error
- **Generic Exception**: Shows `EthanError("SYS-999", ...)` with context

**Before**:
```
[raw exception traceback text]
```

**After**:
```
✗ API unreachable
  → ethan daemon may be stopped
  → try: ethan daemon start
```

---

### 3. `cli/commands/daemon.py` — Fixed duplicate + added UX
- Removed duplicate `@register("daemon")` decorator
- Added `UX` import for future suggestion support
- Clean single registration

---

### 4. `cli/commands/plugin.py` — Subcommand suggestions
- Added `KNOWN_PLUGIN_SUBS = ["install", "remove", "list"]`
- Added `UX.suggest_command()` for unknown subcommands
- **Before**: "Unknown subcommand: xyz"
- **After**: "Unknown subcommand: xyz\n  Did you mean? install"

---

### 5. `cli/commands/memory.py` — Subcommand suggestions
- Added `KNOWN_MEMORY_SUBS = ["recent", "frequent"]`
- Added `UX.suggest_command()` for unknown subcommands
- **Before**: "usage: ethan memory [recent|frequent] [N]"
- **After**: "Unknown subcommand: x\n  Did you mean? recent\n  usage: ..."

---

### 6. `cli/commands/cfg.py` — Subcommand suggestions
- Added `KNOWN_CONFIG_SUBS = ["get", "set", "reset"]`
- Added `UX.suggest_command()` for unknown subcommands
- **Before**: "usage: ethan config [get|set|reset]"
- **After**: "Unknown subcommand: x\n  Did you mean? get"

---

### 7. `cli/commands/service.py` — UX import added
- Added `UX` import and `KNOWN_SERVICE_SUBS`
- Ready for suggestion logic (priority LOW per audit)

---

### 8. `cli/commands/logs.py` — UX import added
- Added `UX` import
- Flags-based command (no subcommand suggestions needed)

---

### 9. `cli/commands/status.py` — UX import added
- Added `UX` import
- No subcommands, but ready for future use

---

### 10. `cli/commands/suggest.py` — UX import added
- Added `UX` import for consistency

---

### 11. `cli/commands/plugins.py` — UX import added
- Added `UX` import for consistency

---

## Files Modified

| File | Changes |
|---|---|
| `cli/registry.py` | Structured errors + fuzzy suggestions in dispatch |
| `cli/commands/chat.py` | Categorized exception handling with proper user messages |
| `cli/commands/daemon.py` | Fixed duplicate registration, added UX import |
| `cli/commands/plugin.py` | Subcommand suggestions via UX |
| `cli/commands/memory.py` | Subcommand suggestions via UX |
| `cli/commands/cfg.py` | Subcommand suggestions via UX |
| `cli/commands/service.py` | UX import added |
| `cli/commands/logs.py` | UX import added |
| `cli/commands/status.py` | UX import added |
| `cli/commands/suggest.py` | UX import added |
| `cli/commands/plugins.py` | UX import added |

---

## Error Handling Coverage

| Scenario | Before | After |
|---|---|---|
| Unknown command `chatt` | "Unknown command: chatt" | "Did you mean? chat" |
| Unknown daemon subcommand | "usage: ethan daemon ..." | Same (no change needed) |
| Unknown plugin subcommand `xyz` | "Unknown subcommand: xyz" | "Did you mean? install/remove/list" |
| Unknown memory subcommand `xyz` | "usage: ethan memory ..." | "Did you mean? recent/frequent" |
| Empty message in chat | Raw exception | "Empty message\n  type a message or /exit" |
| API timeout in chat | Raw exception | "API unreachable\n  try: ethan daemon start" |
| Generic error in chat | Raw traceback | "Unexpected error\n  try: ethan chat" |
| Dispatch exception | "Error: {e}" | Structured EthanError with code |

---

## Remaining (LOW Priority)

- `service.py`: Add actual suggestion logic for invalid subcommands (UX import ready)
- `logs.py`: Add invalid flag handling (flags are positional, not subcommands)
- `--debug` global flag for stack traces
- Error logging to file (not just stdout)

---

## Testing Impact

Tests that may need updates due to changed error messages:
- `tests/cli/ethan/unit/test_registry.py`: Unknown command now shows structured error
- `tests/cli/ethan/commands/test_daemon_cmd.py`: Error message format changed
- `tests/cli/ethan/commands/test_memory_cmd.py`: Error message format changed
- `tests/cli/ethan/commands/test_plugin_cmd.py`: Error message format changed
- `tests/cli/ethan/integration/test_invalid_commands.py`: Assertions may need updates