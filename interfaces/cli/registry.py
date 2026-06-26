"""ETHAN command registry — fully automatic discovery.

Uses cli.core.discovery.CommandRegistry as the single source of truth.
@register() delegates to the global registry instance.
dispatch() resolves commands via registry.get().
"""
import importlib.util
import signal
import sys
from collections.abc import Callable
from pathlib import Path

from interfaces.cli.core import colors as clr
from interfaces.cli.core.discovery import registry, Command

_COMMAND_TIMEOUT = 300  # 5 minutes default


class TimeoutError(Exception):
    """Raised when a command exceeds the timeout."""


def _timeout_handler(signum, frame):
    raise TimeoutError(f"Command timed out after {_COMMAND_TIMEOUT}s")


def register(name: str, group: str = "core", description: str = "", usage: str = ""):
    """Register a CLI command handler.

    Registers the command in the global CommandRegistry (via @register decorator)
    and stores the handler in a lookup dict for dispatch.

    Usage:
        @register("status")
        def cmd_status(args):
            ...
    """
    def decorator(fn):
        # Register in discovery registry for help/suggest
        existing = registry.get(name)
        if not existing:
            registry.register(Command(
                name=name,
                group=group,
                description=description or fn.__doc__ or name,
                usage=usage or f"ethan {name}",
            ))
        # Store handler for dispatch in the function itself
        fn._ethan_cmd_name = name
        COMMAND_HANDLERS[name] = fn
        return fn
    return decorator


# Handler lookup (separate from CommandRegistry metadata)
COMMAND_HANDLERS: dict[str, Callable] = {}


def _get_handler(name: str) -> Callable | None:
    """Resolve a command handler by name."""
    return COMMAND_HANDLERS.get(name)


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
    
    # Auto-detect functions named cmd_* as command handlers
    for attr_name in dir(mod):
        if attr_name.startswith("cmd_") and not attr_name.startswith("cmd__"):
            fn = getattr(mod, attr_name)
            if callable(fn):
                cmd_name = attr_name[4:]  # remove "cmd_" prefix
                if cmd_name not in COMMAND_HANDLERS:
                    COMMAND_HANDLERS[cmd_name] = fn
                    # Also register in discovery registry if not already there
                    if registry.get(cmd_name) is None:
                        registry.register(Command(
                            name=cmd_name,
                            group="core",
                            description=fn.__doc__ or cmd_name,
                            usage=f"ethan {cmd_name}",
                        ))
    
    # Plugins may also register via ETHAN_PLUGIN dict
    if hasattr(mod, "ETHAN_PLUGIN"):
        for name, cmd in mod.ETHAN_PLUGIN.get("commands", {}).items():
            if isinstance(cmd, dict) and "handler" in cmd:
                COMMAND_HANDLERS[name] = cmd["handler"]


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


def dispatch(argv, _debug=False, timeout=_COMMAND_TIMEOUT):
    """Dispatch argv[0] as a command name, argv[1:] as args.

    Args:
        argv: Command arguments list.
        _debug: Enable debug/self-healing mode.
        timeout: Command timeout in seconds (0 = no timeout).
                 Only applies on Linux (SIGALRM).
    """
    from interfaces.cli.core.errors import format_error, unknown_command

    if not argv:
        print("ETHAN toolchain")
        print("Commands:", " ".join(sorted(c.name for c in registry.list_commands())))
        return 0
    cmd = argv[0]
    args = argv[1:]
    fn = _get_handler(cmd)
    if not fn:
        from interfaces.cli.core.ux import UX
        suggestion = UX.suggest_command(cmd, [c.name for c in registry.list_commands()])
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
            from interfaces.cli.core.errors import EthanError
            print(format_error(EthanError("SYS-002", "Timeout",
                                          f"command '{cmd}' exceeded {timeout}s")))
            return 1
        except SystemExit:
            raise
        except Exception as e:
            from interfaces.cli.core.errors import EthanError
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
    from interfaces.cli.core.debug_trap import DebugTrap
    from interfaces.cli.core.error_classifier import ErrorClassifier
    from interfaces.cli.core.fix_map import FixMap
    from interfaces.cli.core.self_heal import SelfHealer
    from interfaces.cli.core.retest_runner import RetestRunner
    from interfaces.cli.core.debug_ui import DebugUI

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