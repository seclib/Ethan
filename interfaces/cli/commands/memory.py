"""ETHAN memory — history management."""
from interfaces.cli.registry import register
from interfaces.cli.core import memory as mem
from interfaces.cli.core.ux import UX


KNOWN_MEMORY_SUBS = ["recent", "frequent"]


@register("memory")
def cmd_memory(args):
    if not args or args[0] == "recent":
        n = int(args[1]) if len(args) > 1 else 8
        for e in mem.recent(n):
            print("  " + e["text"])
    elif args[0] == "frequent":
        n = int(args[1]) if len(args) > 1 else 5
        for e in mem.frequent(n):
            print("  " + e["text"] + "  x" + str(e["count"]))
    else:
        suggestion = UX.suggest_command(args[0], KNOWN_MEMORY_SUBS)
        msg = f"Did you mean? {suggestion}" if suggestion else "usage: ethan memory [recent|frequent] [N]"
        print(f"Unknown subcommand: {args[0]}\n  {msg}")
    return 0