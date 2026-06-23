"""ETHAN daemon — background cache control."""
from registry import register
from core import daemon as daemon_core


@register("daemon")
def cmd_daemon(args):
    if not args or args[0] not in ("start", "stop", "status"):
        print("usage: ethan daemon <start|stop|status>")
        return 1
    sub = args[0]
    sub_args = args[1:]
    if sub == "start":
        daemon_core.cmd_start(sub_args)
    elif sub == "stop":
        daemon_core.cmd_stop(sub_args)
    elif sub == "status":
        daemon_core.cmd_status(sub_args)
    return 0