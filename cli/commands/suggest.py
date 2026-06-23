"""ETHAN suggest — smart suggestions."""
from registry import register
from core import memory as mem


@register("suggest")
def cmd_suggest(args):
    if not args:
        print("Recent:")
        for e in mem.recent(8):
            print("  " + e["text"])
        print("\nFrequent:")
        for e in mem.frequent(5):
            print("  " + e["text"] + "  x" + str(e["count"]))
    else:
        matches = mem.suggest_prefix(args[0], 8)
        for m in matches:
            print(m)
    return 0