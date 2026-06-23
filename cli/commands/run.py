"""ETHAN run — one-shot send."""
from registry import register
from core.client import send, alive
from core import memory as mem
from core import logging as logs


@register("run")
def cmd_run(args):
    if not args:
        print("usage: ethan run <message>")
        return 1
    text = " ".join(args)
    if not alive():
        print("ERR: unreachable")
        return 1
    mem.record("run", text)
    resp, latency = send(text)
    logs.log("run:" + text[:60], "ok", latency)
    print(resp)
    return 0