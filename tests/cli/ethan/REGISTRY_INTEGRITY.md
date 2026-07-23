# ETHAN CLI Registry Integrity Report

## Executive Summary

**9 out of 13 builtin commands are NOT registered due to broken imports.**

### Current registry state
- Registered: `chat`, `hello`, `run`, `think`, `weather`
- Total: **5 commands**
- Expected: **13 commands** (including plugins)

---

## Root Cause

`discover_commands()` in `cli/registry.py` loads `cli/commands/*.py` via `importlib.util.spec_from_file_location` with `name=path.stem`. When a file uses `from registry import register`, Python tries to import a top-level module named `registry` (not `cli.registry`). This fails with `No module named 'registry'`.

Files that use `from registry import ...` (WRONG):
- `cfg.py`
- `daemon.py`
- `logs.py`
- `memory.py`
- `plugin.py`
- `plugins.py`
- `service.py`
- `status.py`
- `suggest.py`

Files that use `from cli.registry import ...` (CORRECT):
- `chat.py`
- `run.py`
- `think.py`

Files that don't import registry:
- `help.py` (registered via `cli/ethan` entrypoint, not in current scan)

---

## Broken Links Matrix

| Command File | Command Name | Current Import | Status | Registration |
|---|---|---|---|---|
| `cfg.py` | `config` | `from registry import register` | ⚠️ BROKEN | ❌ NOT registered |
| `daemon.py` | `daemon` | `from registry import register` | ⚠️ BROKEN | ❌ NOT registered |
| `logs.py` | `logs` | `from registry import register` | ⚠️ BROKEN | ❌ NOT registered |
| `memory.py` | `memory` | `from registry import register` | ⚠️ BROKEN | ❌ NOT registered |
| `plugin.py` | `plugin` | `from registry import register` + `from plugin_manager import ...` | ⚠️ BROKEN | ❌ NOT registered |
| `plugins.py` | `plugins` | `from registry import register, discover_commands, COMMANDS` | ⚠️ BROKEN | ❌ NOT registered |
| `service.py` | `service` | `from registry import register` | ⚠️ BROKEN | ❌ NOT registered |
| `status.py` | `status` | `from registry import register` | ⚠️ BROKEN | ❌ NOT registered |
| `suggest.py` | `suggest` | `from registry import register` | ⚠️ BROKEN | ❌ NOT registered |
| `chat.py` | `chat` | `from cli.registry import register` | ✅ OK | ✅ registered |
| `run.py` | `run` | `from cli.registry import register` | ✅ OK | ✅ registered |
| `think.py` | `think` | `from cli.registry import register` | ✅ OK | ✅ registered |

---

## Plugin Compatibility

| Plugin Path | Registered Name | Status |
|---|---|---|
| `cli/plugins/hello-world/plugin.py` | `hello` | ✅ registered |
| `cli/plugins/weather/plugin.py` | `weather` | ✅ registered |

Plugin discovery works correctly for `ETHAN_PLUGIN` dict pattern.

---

## Missing Commands

```
config   (from cfg.py)
daemon   (from daemon.py)
logs     (from logs.py)
memory   (from memory.py)
plugin   (from plugin.py)
plugins  (from plugins.py)
service  (from service.py)
status   (from status.py)
suggest  (from suggest.py)
```

---

## Fixes Required

**Option A — Quick fix (patch all 9 files):**
Change `from registry import ...` → `from cli.registry import ...` in all broken files.

**Option B — Fix `discover_commands` (structural fix):**
Force Python's module search path to include `cli/` before loading, so `import registry` resolves to `cli.registry`:

```python
# In cli/registry.py, line 29-36:
spec = importlib.util.spec_from_file_location(entry.stem, entry)
if spec is None or spec.loader is None:
    return
try:
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # add: sys.path.insert(0, str(path.parent))
```

**Option C — Add `__init__.py` + use package imports:**
Ensure `cli/commands/__init__.py` exists (it does) and update `sys.path` during discovery.

### Recommended approach: Option A
Minimal, targeted, reversible. Each file gets a one-line import fix.

---

## Autocomplete Consistency

`cli/core/discovery.py` has a hardcoded `registry` with different commands than what's actually loadable:

```python
registry.register(Command("chat", ...))
registry.register(Command("run", ...))
registry.register(Command("status", ...))   # broken in real registry
registry.register(Command("logs", ...))     # broken in real registry
registry.register(Command("help", ...))
registry.register(Command("plugin", ...))   # broken in real registry
registry.register(Command("shell", ...))    # no such command!
registry.register(Command("config", ...))   # broken in real registry
registry.register(Command("daemon", ...))   # broken in real registry
```

`cli/core/discovery.py` also has `shell` command which doesn't exist in `cli/commands/`. This causes inconsistency between help/autocomplete and actual registration.

---

## Summary of Issues

| Issue | Severity | Count |
|---|---|---|
| Broken import (`registry` vs `cli.registry`) | HIGH | 9 files |
| Missing commands from real registry | HIGH | 9 commands |
| `discovery.py` has non-existent `shell` command | MEDIUM | 1 command |
| `plugin.py` also imports `plugin_manager` directly without `cli.` prefix | MEDIUM | 1 file |
| `plugins.py` imports `discover_commands` and `COMMANDS` with wrong prefix | MEDIUM | 1 file |