"""ETHAN config — view & manage configuration."""
from registry import register
from core import config as cfg


@register("config")
def cmd_config(args):
    if not args:
        cfg.show()
        return 0

    if args[0] == "get":
        if len(args) < 2:
            print("usage: ethan config get <key>")
            return 1
        val = cfg.get(args[1])
        print(val if val is not None else "(not set)")
        return 0

    if args[0] == "set":
        if len(args) < 3:
            print("usage: ethan config set <key> <value>")
            return 1
        cfg.set_value(args[1], args[2])
        print(f"config {args[1]} = {args[2]}")
        return 0

    if args[0] == "reset":
        cfg.reset()
        print("config reset to defaults")
        return 0

    print("usage: ethan config [get <key>|set <key> <value>|reset]")
    return 1