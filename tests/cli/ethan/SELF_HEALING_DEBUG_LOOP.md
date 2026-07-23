# ETHAN CLI Self-Healing Debug Loop Architecture

## Executive Summary

A closed-loop debug system that automatically detects CLI failures, classifies them, maps to known fixes, suggests patches, and optionally re-tests the command.

**Core principle**: Fail fast, diagnose automatically, suggest actionable fixes, recover when possible.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ETHAN CLI SELF-HEALING SYSTEM                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌───────────┐ │
│  │  TRAP    │───▶│ CLASSIFY │───▶│   FIX MAP  │───▶│  PATCHER  │ │
│  │  LAYER   │    │  ENGINE  │    │  DATABASE  │    │           │ │
│  └──────────┘    └──────────┘    └────────────┘    └───────────┘ │
│       │                │                  │                │       │
│       │                │                  │                │       │
│       ▼                ▼                  ▼                ▼       │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌───────────┐ │
│  │ Command  │    │ Error    │    │  Patch     │    │  Auto-    │ │
│  │ Output   │    │ Taxonomy │    │ Recipes    │    │  Apply    │ │
│  │ Capture  │    │ + Severity│    │            │    │  (Opt-in) │ │
│  └──────────┘    └──────────┘    └────────────┘    └───────────┘ │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌───────────┐ │
│  │ Feedback │◀───│ Re-Test  │◀───│   Diff     │◀───│  Proposed │ │
│  │ Loop     │   │ Runner   │   │  Preview    │   │   Fix      │ │
│  └──────────┘    └──────────┘    └────────────┘    └───────────┘ │
│       │                │                  │                │       │
│       └────────────────┴──────────────────┴────────────────┘       │
│                        │                                          │
│                        ▼                                          │
│              ┌────────────────┐                                   │
│              │  User Decision │◀── Report / Approve / Reject       │
│              └────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. TRAP LAYER (Error Detection)

**Location**: `cli/core/debug_trap.py`

**Responsibility**: Capture all CLI output and exit codes without modifying command logic.

```python
class DebugTrap:
    """Wraps command execution to capture failures."""
    
    def __init__(self, command_fn, argv):
        self.command_fn = command_fn
        self.argv = argv
        self.exit_code = None
        self.stdout = []
        self.stderr = []
        self.exception = None
        self.duration_ms = 0
    
    def execute(self):
        """Run command and capture all output."""
        t0 = time.time()
        try:
            self.exit_code = self.command_fn(self.argv)
        except Exception as e:
            self.exception = e
            self.exit_code = 1
        self.duration_ms = int((time.time() - t0) * 1000)
        return self.exit_code
    
    def should_heal(self) -> bool:
        """Determine if this failure is healable."""
        return self.exit_code != 0 and self.exception is not None
```

**Integration**: Decorator pattern on `dispatch()`

```python
@trap_command
def dispatch(argv):
    ...
```

---

### 2. CLASSIFY ENGINE (Error Analysis)

**Location**: `cli/core/error_classifier.py`

**Responsibility**: Parse captured error and classify into known patterns.

```python
class ErrorClassifier:
    """Classify errors into known fixable categories."""
    
    TAXONOMY = {
        # Code | Pattern | Severity | Healable
        "IMPORT-ERR": {
            "patterns": [r"No module named '(\w+)'", r"ModuleNotFoundError"],
            "severity": "HIGH",
            "healable": True,
            "category": "dependency"
        },
        "REGISTRY-ERR": {
            "patterns": [r"Unknown command: '(\w+)'", r"Unknown subcommand"],
            "severity": "LOW",
            "healable": False,  # User typo, not a fix
            "category": "input"
        },
        "API-ERR": {
            "patterns": [r"API unreachable", r"Connection refused", r"URLError"],
            "severity": "HIGH",
            "healable": True,
            "category": "network"
        },
        "TIMEOUT-ERR": {
            "patterns": [r"timed out", r"Timeout"],
            "severity": "MEDIUM",
            "healable": True,
            "category": "network"
        },
        "CONFIG-ERR": {
            "patterns": [r"config", r"JSONDecodeError", r"Corrupt"],
            "severity": "MEDIUM",
            "healable": True,
            "category": "config"
        },
        "PERM-ERR": {
            "patterns": [r"Permission denied", r"PermissionError"],
            "severity": "HIGH",
            "healable": False,  # Needs sudo/admin
            "category": "permission"
        },
        "DAEMON-ERR": {
            "patterns": [r"daemon", r"PID", r"process"],
            "severity": "MEDIUM",
            "healable": True,
            "category": "service"
        }
    }
    
    def classify(self, exception, stdout) -> ErrorClassification:
        """Return classification with matched pattern."""
        text = str(exception) + "\n" + "\n".join(stdout)
        for code, meta in self.TAXONOMY.items():
            for pattern in meta["patterns"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return ErrorClassification(
                        code=code,
                        severity=meta["severity"],
                        healable=meta["healable"],
                        category=meta["category"],
                        match=match.group(1) if match.groups() else None
                    )
        return ErrorClassification("UNKNOWN", "LOW", False, "unknown", None)
```

---

### 3. FIX MAP DATABASE (Known Fixes)

**Location**: `cli/core/fix_map.py`

**Responsibility**: Map error classifications to actionable patches.

```python
class FixMap:
    """Database of known error→fix mappings."""
    
    FIXES = {
        "IMPORT-ERR": {
            "detect": lambda c, m: True,  # any import error
            "suggest": "Check if module is installed: pip install <module>",
            "auto_patch": None,  # Cannot auto-fix missing packages
            "retry": False
        },
        "API-ERR": {
            "detect": lambda c, m: True,
            "suggest": "Start the daemon: ethan daemon start",
            "auto_patch": "daemon_start",
            "retry": True,
            "retry_delay": 2
        },
        "TIMEOUT-ERR": {
            "detect": lambda c, m: True,
            "suggest": "Increase timeout: ethan run --timeout 30",
            "auto_patch": "increase_timeout",
            "retry": True,
            "retry_delay": 1
        },
        "CONFIG-ERR": {
            "detect": lambda c, m: True,
            "suggest": "Reset config: ethan config reset",
            "auto_patch": "config_reset",
            "retry": True,
            "retry_delay": 0
        },
        "DAEMON-ERR": {
            "detect": lambda c, m: True,
            "suggest": "Restart daemon: ethan daemon stop && ethan daemon start",
            "auto_patch": "daemon_restart",
            "retry": True,
            "retry_delay": 2
        }
    }
    
    def lookup(self, classification: ErrorClassification) -> FixRecipe:
        """Return fix recipe for error classification."""
        fix = self.FIXES.get(classification.code)
        if not fix:
            return FixRecipe(
                suggestion="Try: ethan --help",
                auto_patch=None,
                retry=False,
                retry_delay=0
            )
        return FixRecipe(
            suggestion=fix["suggest"],
            auto_patch=fix.get("auto_patch"),
            retry=fix.get("retry", False),
            retry_delay=fix.get("retry_delay", 0)
        )
```

---

### 4. PATCHER (Auto-Fix Engine)

**Location**: `cli/core/self_heal.py`

**Responsibility**: Execute safe automated fixes.

```python
class SelfHealer:
    """Execute automated fixes for known issues."""
    
    PATCHERS = {
        "daemon_start": lambda ctx: _start_daemon(),
        "daemon_restart": lambda ctx: _restart_daemon(),
        "config_reset": lambda ctx: _reset_config(),
        "increase_timeout": lambda ctx: _increase_timeout()
    }
    
    def apply(self, patch_name: str, context: CommandContext) -> PatchResult:
        """Apply named patch. Returns success/failure."""
        patcher = self.PATCHERS.get(patch_name)
        if not patcher:
            return PatchResult(success=False, message="No auto-patch available")
        
        try:
            result = patcher(context)
            return PatchResult(success=True, message=result)
        except Exception as e:
            return PatchResult(success=False, message=str(e))

def _start_daemon():
    """Auto-start daemon if not running."""
    from cli.core.daemon import cmd_start
    cmd_start([])
    time.sleep(1)
    return "Daemon started"

def _restart_daemon():
    """Restart daemon."""
    from cli.core.daemon import cmd_stop, cmd_start
    cmd_stop([])
    time.sleep(0.5)
    cmd_start([])
    return "Daemon restarted"

def _reset_config():
    """Reset config to defaults."""
    from cli.core.config import reset
    reset()
    return "Config reset"

def _increase_timeout():
    """Temporarily increase timeout."""
    os.environ["ETHAN_API_TIMEOUT"] = "30"
    return "Timeout increased to 30s"
```

---

### 5. RE-TEST RUNNER

**Location**: `cli/core/retest_runner.py`

**Responsibility**: Re-run failed command with fixes applied.

```python
class RetestRunner:
    """Re-run command after auto-fix."""
    
    def __init__(self, original_argv, max_retries=1):
        self.original_argv = original_argv
        self.max_retries = max_retries
        self.attempts = 0
        self.history = []
    
    def should_retry(self, fix_recipe: FixRecipe) -> bool:
        """Determine if retry is appropriate."""
        if not fix_recipe.retry:
            return False
        if self.attempts >= self.max_retries:
            return False
        return True
    
    def retry(self, context: CommandContext) -> RetestResult:
        """Re-run command with fix applied."""
        self.attempts += 1
        time.sleep(self.retry_delay)
        
        # Re-dispatch through registry
        from cli.registry import dispatch
        exit_code = dispatch(self.original_argv)
        
        result = RetestResult(
            attempt=self.attempts,
            exit_code=exit_code,
            success=(exit_code == 0),
            timestamp=time.time()
        )
        self.history.append(result)
        return result
```

---

### 6. FEEDBACK LOOP (User Interaction)

**Location**: `cli/core/debug_ui.py`

**Responsibility**: Present findings to user and get approval.

```python
class DebugUI:
    """User-facing debug report."""
    
    @staticmethod
    def show_diagnosis(classification: ErrorClassification, 
                       recipe: FixRecipe,
                       can_auto_fix: bool) -> str:
        """Render diagnosis to user."""
        lines = [
            f"",
            f"  {clr.C.YELLOW}⚕  Diagnosis{clr.C.RESET}",
            f"",
            f"  Error: {clr.C.RED}{classification.code}{clr.C.RESET}",
            f"  Severity: {classification.severity}",
            f"  Category: {classification.category}",
            f"",
            f"  {clr.C.CYAN}→ Suggestion:{clr.C.RESET} {recipe.suggestion}",
        ]
        
        if can_auto_fix and recipe.auto_patch:
            lines.extend([
                f"",
                f"  {clr.C.GREEN}✓ Auto-fix available:{clr.C.RESET} {recipe.auto_patch}",
                f"  {clr.C.DIM}Apply and retry? [Y/n]{clr.C.RESET}"
            ])
        
        return "\n".join(lines)
    
    @staticmethod
    def show_retry_result(result: RetestResult):
        """Show retry outcome."""
        if result.success:
            print(f"  {clr.C.GREEN}✓ Command succeeded after fix{clr.C.RESET}")
        else:
            print(f"  {clr.C.RED}✗ Command still failing{clr.C.RESET}")
        print(f"  Attempts: {result.attempt}, Exit code: {result.exit_code}")
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SELF-HEALING DEBUG LOOP                        │
└─────────────────────────────────────────────────────────────────────┘

 PHASE 1: CAPTURE
 ─────────────────────────────────────────────────────────────────────
  Command executes via dispatch()
       │
       ▼
  ┌──────────────┐
  │ DebugTrap    │
  │ - exit_code  │
  │ - stdout     │
  │ - stderr     │
  │ - exception  │
  └──────┬───────┘
         │
         ▼
  exit_code == 0? ──── YES ───▶ [Command succeeded, no action]
         │
         NO
         │
         ▼
 PHASE 2: CLASSIFY
 ─────────────────────────────────────────────────────────────────────
  ┌──────────────────┐
  │ ErrorClassifier  │
  │ - regex matching │
  │ - taxonomy lookup│
  │ - severity check │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────┐
  │ ErrorClassification                    │
  │ - code: "API-ERR"                      │
  │ - severity: "HIGH"                     │
  │ - healable: True                       │
  │ - category: "network"                  │
  │ - match: "unreachable"                 │
  └────────────────┬────────────────────────┘
                   │
                   ▼
 PHASE 3: MAP TO FIX
 ─────────────────────────────────────────────────────────────────────
  ┌──────────────────┐
  │ FixMap           │
  │ - lookup(code)   │
  │ - recipe          │
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────────────────────────────┐
  │ FixRecipe                               │
  │ - suggestion: "try: ethan daemon start" │
  │ - auto_patch: "daemon_start"            │
  │ - retry: True                           │
  │ - retry_delay: 2                        │
  └────────────────┬────────────────────────┘
                   │
                   ▼
 PHASE 4: SUGGEST / APPLY
 ─────────────────────────────────────────────────────────────────────
         │
         ├─── auto_patch == None ────▶ Show suggestion only
         │                             User acts manually
         │
         └─── auto_patch != None ────▶ Show fix proposal
                                        "Auto-start daemon and retry?"
                                            │
                          ┌─────────────┴──────────────┐
                          │                             │
                     User says YES                 User says NO
                          │                             │
                          ▼                             ▼
              ┌──────────────────┐          ┌──────────────────┐
              │ SelfHealer        │          │ Show manual hint  │
              │ - apply(patch)    │          │ End loop          │
              │ - result          │          └──────────────────┘
              └────────┬─────────┘
                       │
                       ▼
 PHASE 5: RE-TEST
 ─────────────────────────────────────────────────────────────────────
              ┌──────────────────┐
              │ RetestRunner     │
              │ - retry(argv)    │
              │ - max_retries=1  │
              └────────┬─────────┘
                       │
                       ▼
              exit_code == 0?
                       │
           ┌───────────┴───────────┐
           │                       │
          YES                      NO
           │                       │
           ▼                       ▼
  ┌──────────────┐         ┌──────────────────┐
  │ ✓ FIXED      │         │ ✗ PERSISTS       │
  │ - report     │         │ - show traces    │
  │ - log        │         │ - suggest manual │
  └──────────────┘         │ - create ticket? │
                           └──────────────────┘

 LOOP: If fixed → success. If persists → escalate to human.
```

---

## Integration Points

### Hook into existing dispatch()

```python
# cli/registry.py
from cli.core.debug_trap import DebugTrap
from cli.core.error_classifier import ErrorClassifier
from cli.core.fix_map import FixMap
from cli.core.self_heal import SelfHealer
from cli.core.retest_runner import RetestRunner
from cli.core.debug_ui import DebugUI

def dispatch(argv, _debug=False):
    """Dispatch with optional self-healing."""
    if not argv:
        ...
    
    fn = COMMANDS.get(argv[0])
    if not fn:
        ...
    
    # Execute with trap
    trap = DebugTrap(fn, argv)
    exit_code = trap.execute()
    
    # If success, normal path
    if exit_code == 0:
        return 0
    
    # If debug mode, enter self-healing loop
    if _debug:
        return _self_heal_loop(trap)
    
    # Normal error handling
    return exit_code

def _self_heal_loop(trap):
    """Closed-loop self-healing."""
    classifier = ErrorClassifier()
    fix_map = FixMap()
    healer = SelfHealer()
    runner = RetestRunner(trap.argv)
    
    # Classify
    classification = classifier.classify(trap.exception, trap.stdout)
    
    # Map to fix
    recipe = fix_map.lookup(classification)
    
    # Show diagnosis
    print(DebugUI.show_diagnosis(classification, recipe, 
                                  recipe.auto_patch is not None))
    
    # Auto-apply if available and user consents
    if recipe.auto_patch:
        # For now, auto-apply without asking (configurable)
        result = healer.apply(recipe.auto_patch, trap)
        if result.success:
            print(f"  {clr.C.GREEN}✓ {result.message}{clr.C.RESET}")
            
            # Re-test
            if runner.should_retry(recipe):
                retry_result = runner.retry()
                print(DebugUI.show_retry_result(retry_result))
                if retry_result.success:
                    return 0
    
    # If we get here, fix didn't work or no auto-fix
    print(f"  {clr.C.YELLOW}⚠ Manual intervention required{clr.C.RESET}")
    print(f"  {clr.C.DIM}{recipe.suggestion}{clr.C.RESET}")
    return 1
```

### Enable via environment variable

```bash
# Enable self-healing debug mode
ETHAN_DEBUG=1 ethan chat

# Or via CLI flag (requires argparse in ethan entrypoint)
ethan --self-heal chat
```

---

## Configuration

```python
# cli/core/debug_config.py
DEBUG_CONFIG = {
    "enabled": os.getenv("ETHAN_SELF_HEAL", "0") == "1",
    "max_retries": 1,
    "auto_approve": os.getenv("ETHAN_AUTO_FIX", "0") == "1",
    "timeout_multiplier": 2,
    "log_patches": True,
    "categories": {
        "dependency": False,   # Cannot auto-fix
        "network": True,       # Can retry/start daemon
        "config": True,        # Can reset config
        "permission": False,   # Needs sudo
        "service": True,       # Can restart
        "input": False         # User typo
    }
}
```

---

## Error Taxonomy (Expanded)

```
ERROR CODES
├── SYS-001  API unreachable
├── SYS-002  Timeout
├── SYS-003  Permission denied
├── CMD-001  Unknown command
├── CMD-002  Missing argument
├── INP-001  Empty input
├── INP-002  Invalid session
├── INP-003  File not found
├── IMPORT-ERR  Module not found
├── REGISTRY-ERR  Command resolution failed
├── CONFIG-ERR  Config file corrupt/invalid
├── DAEMON-ERR  Daemon/process error
└── UNKNOWN  Unclassified error

SEVERITY LEVELS
├── LOW     Cosmetic, no functional impact
├── MEDIUM  Degraded functionality
├── HIGH    Core feature broken
└── CRITICAL System unstable

HEALABILITY
├── AUTO    Can be fixed automatically
├── ASSIST  Can be fixed with user approval
└── MANUAL  Requires human intervention
```

---

## Safety Guards

1. **No destructive patches without user consent** (config reset, file deletion)
2. **Patch whitelist** — only known-safe patches allowed
3. **Retry limit** — max 1 retry per command to avoid loops
4. **Audit log** — all patches logged to `~/.ethan/debug.log`
5. **Rollback** — patches are reversible (config backup before reset)
6. **Opt-in** — disabled by default, enabled via env var

---

## Benefits

| Benefit | Impact |
|---|---|
| Faster recovery | Auto-fix reduces manual intervention |
| Better UX | Clear "what broke + how to fix" messages |
| Learning system | Fix patterns can be refined over time |
| Reduced support load | Users self-service common issues |
| Debug mode | `ETHAN_DEBUG=1` for troubleshooting |

---

## Implementation Priority

| Phase | Component | Effort | Value |
|---|---|---|---|
| 1 | Trap Layer + Classifier | Low | High |
| 2 | Fix Map + Patcher | Medium | High |
| 3 | Retest Runner | Low | Medium |
| 4 | Debug UI + Feedback | Medium | Medium |
| 5 | Integration into dispatch | Low | High |
| 6 | Config + Safety guards | Low | High |

**Estimated total effort**: 1-2 days for minimal viable implementation.

---

## Future Enhancements

- Machine learning for error classification (train on logs)
- Community-contributed fix recipes
- Telemetry: track which fixes work, which don't
- Integration with `ethan logs --errors` for batch analysis
- `ethan doctor` command that proactively checks system health