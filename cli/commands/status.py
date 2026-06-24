"""ETHAN status — system state."""
from cli.registry import register
from cli.core.client import alive, get_state
from cli.core.ux import UX


@register("status")
def cmd_status(args):
    if alive():
        s = get_state() or {}
        print("ONLINE")
        print("Mode:       " + s.get("mode", "?"))
        print("Goal:       " + s.get("active_goal", "none"))
        print("Tasks:      " + str(s.get("running_tasks", 0)))
        last = s.get("last_event")
        if last:
            print("Last event: [" + last.get("type","?") + "] " + str(last.get("data",""))[:120])
    else:
        print("OFFLINE")
    return 0