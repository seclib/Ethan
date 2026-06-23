"""ETHAN memory — history management."""
from registry import register
from core import memory as mem


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
        print("usage: ethan memory [recent|frequent] [N]")
    return 0