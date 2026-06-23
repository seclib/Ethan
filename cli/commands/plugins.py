"""ETHAN plugins — list/manage extensions."""
from registry import register, discover_commands, COMMANDS


@register("plugins")
def cmd_plugins(args):
    discover_commands()
    builtin = ["chat", "status", "logs", "memory", "suggest", "daemon", "run", "help", "plugins", "version"]
    extra = sorted(c for c in COMMANDS if c not in builtin)
    if not extra:
        print("No external plugins loaded.")
    else:
        print("Plugins:")
        for name in extra:
            print("  " + name)
    return 0