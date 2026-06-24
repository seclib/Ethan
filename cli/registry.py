"""ETHAN command registry — fully automatic discovery.

No hardcoded imports. Commands register themselves via @register().
"""
import importlib.util
import signal
import sys
from pathlib import Path

from cli.core import colors as clr

COMMANDS = {}


def register(name):
    def decorator(fn):
        COMMANDS[name] = fn
        return fn
    return decorator


def _load_module(path):
    """Dynamically import a single Python file as a module.

    Handles both standalone .py files and directories with plugin.py.
    """
    entry = path
    if path.is_dir():
        entry = path / "plugin.py"
    if not entry.exists():
        return
    spec = importlib.util.spec_from_file_location(entry.stem, entry)
    if spec is None or spec.loader is None:
        return
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:
        return
    # Plugins may also register via ETHAN_PLUGIN dict
    if hasattr(mod, "ETHAN_PLUGIN"):
        for name, cmd in mod.ETHAN_PLUGIN.get("commands", {}).items():
            COMMANDS[name] = cmd["handler"]


def discover_commands():
    """Automatically discover and register all builtin commands.

    Scans cli/commands/*.py and cli/plugins/*.py / plugins/*/plugin.py.
    User plugins at ~/.local/share/ethan/plugins/*/plugin.py.
    """
    base = Path(__file__).parent

    # 1. Builtin commands: cli/commands/*.py
    commands_dir = base / "commands"
    if commands_dir.exists():
        for path in sorted(commands_dir.iterdir()):
            if path.suffix == ".py" and not path.name.startswith("_"):
                _load_module(path)

    # 2. Builtin plugins: cli/plugins/*.py or cli/plugins/*/plugin.py
    plugins_dir = base / "plugins"
    if plugins_dir.exists():
        for path in sorted(plugins_dir.iterdir()):
            _load_module(path)

    # 3. User plugins: ~/.local/share/ethan/plugins/*/plugin.py
    user_dir = Path.home() / ".local" / "share" / "ethan" / "plugins"
    if user_dir.exists():
        for path in sorted(user_dir.iterdir()):
            _load_module(path)



_COMMAND_TIMEOUT = 300  # 5 minutes default


class TimeoutError(Exception):
    """Raised when a command exceeds the timeout."""


def _timeout_handler(signum, frame):
    raise TimeoutError(f"Command timed out after {_COMMAND_TIMEOUT}s")


def dispatch(argv, _debug=False, timeout=_COMMAND_TIMEOUT):
    """Dispatch argv[0] as a command name, argv[1:] as args.

    Args:
        argv: Command arguments list.
        _debug: Enable debug/self-healing mode.
        timeout: Command timeout in seconds (0 = no timeout).
                 Only applies on Linux (SIGALRM).
    """
    from cli.core.errors import format_error, unknown_command
    
    if not argv:
        print("ETHAN toolchain")
        print("Commands:", " ".join(sorted(COMMANDS)))
        return 0
    cmd = argv[0]
    args = argv[1:]
    fn = COMMANDS.get(cmd)
    if not fn:
        from cli.core.ux import UX
        suggestion = UX.suggest_command(cmd, list(COMMANDS.keys()))
        if suggestion:
            print(format_error(unknown_command(cmd, f"Did you mean? {suggestion}")))
        else:
            print(format_error(unknown_command(cmd)))
        return 1
    
    # Normal execution (no debug trap)
    if not _debug:
        # Set timeout via SIGALRM (Unix only)
        old_handler = None
        if timeout > 0 and hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout)
        try:
            result = fn(args)
            return result
        except TimeoutError:
            from cli.core.errors import EthanError
            print(format_error(EthanError("SYS-002", "Timeout",
                                          f"command '{cmd}' exceeded {timeout}s")))
            return 1
        except SystemExit:
            raise
        except Exception as e:
            from cli.core.errors import EthanError
            if isinstance(e, EthanError):
                print(format_error(e))
                return getattr(e, 'code', 1)
            print(format_error(EthanError("SYS-999", "Unexpected error", str(e))))
            return 1
        finally:
            if timeout > 0 and hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                if old_handler:
                    signal.signal(signal.SIGALRM, old_handler)
    
    # Debug mode: self-healing loop
    from cli.core.debug_trap import DebugTrap
    from cli.core.error_classifier import ErrorClassifier
    from cli.core.fix_map import FixMap
    from cli.core.self_heal import SelfHealer
    from cli.core.retest_runner import RetestRunner
    from cli.core.debug_ui import DebugUI
    
    trap = DebugTrap(fn, args)
    exit_code = trap.execute()
    
    if exit_code == 0:
        return 0
    
    if not trap.should_heal():
        return exit_code
    
    # Classify error
    classifier = ErrorClassifier()
    classification = classifier.classify(trap.exception, trap.stdout)
    
    # Map to fix
    fix_map = FixMap()
    recipe = fix_map.lookup(classification)
    
    # Show diagnosis
    print(DebugUI.show_diagnosis(classification, recipe, recipe.auto_patch is not None))
    
    # Try auto-fix if available
    if recipe.auto_patch:
        healer = SelfHealer()
        patch_result = healer.apply(recipe.auto_patch, trap.get_context())
        
        if patch_result.success:
            print(f"  {clr.C.GREEN}✓ {patch_result.message}{clr.C.RESET}")
            
            # Re-test
            runner = RetestRunner([cmd] + args, max_retries=1)
            runner.set_recipe(recipe)
            
            if runner.should_retry(recipe):
                retry_result = runner.retry()
                print(DebugUI.show_retry_result(retry_result))
                if retry_result.success:
                    return 0
        else:
            print(f"  {clr.C.RED}✗ Auto-fix failed: {patch_result.message}{clr.C.RESET}")
    
    # Manual escalation
    print(DebugUI.show_manual_escalation(recipe))
    return exit_code
