"""ETHAN command registry — fully automatic discovery.

No hardcoded imports. Commands register themselves via @register().
"""
import importlib.util
import sys
from pathlib import Path

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


def dispatch(argv):
    """Dispatch argv[0] as a command name, argv[1:] as args."""
    if not argv:
        print("ETHAN toolchain")
        print("Commands:", " ".join(sorted(COMMANDS)))
        return 0
    cmd = argv[0]
    args = argv[1:]
    fn = COMMANDS.get(cmd)
    if not fn:
        print(f"Unknown command: {cmd}")
        return 1
    try:
        return fn(args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}")
        return 1
