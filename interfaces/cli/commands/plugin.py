"""ETHAN plugin — install, remove, list, discover external plugins."""
from interfaces.cli.registry import register
from interfaces.cli.core.ux import UX
from interfaces.cli.plugin_manager import install, remove, list_installed, discover


KNOWN_PLUGIN_SUBS = ["install", "remove", "list"]


@register("plugin")
def cmd_plugin(args):
    if not args:
        print("usage: ethan plugin <install|remove|list> [args]")
        return 1
    sub = args[0]
    sub_args = args[1:]
    if sub == "list":
        plugins = list_installed()
        if not plugins:
            print("No user-installed plugins.")
        else:
            print("Installed plugins:")
            for p in plugins:
                print(f"  {p.get('name','?')} v{p.get('version','?')} — {p.get('description','')}")
    elif sub == "install":
        if not sub_args:
            print("usage: ethan plugin install <path|git-url>")
            return 1
        install(sub_args[0])
    elif sub == "remove":
        if not sub_args:
            print("usage: ethan plugin remove <name>")
            return 1
        remove(sub_args[0])
    else:
        suggestion = UX.suggest_command(sub, KNOWN_PLUGIN_SUBS)
        msg = f"Did you mean? {suggestion}" if suggestion else "try: ethan plugin <install|remove|list>"
        print(f"Unknown subcommand: {sub}\n  {msg}")
        return 1
    return 0