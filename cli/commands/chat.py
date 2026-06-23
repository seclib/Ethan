"""ETHAN chat — interactive REPL."""
from registry import register
from core.client import send, alive
from core import memory as mem
from core import logging as logs


@register("chat")
def cmd_chat(args):
    if not alive():
        print("ERR: unreachable")
        return 1
    print("ETHAN chat — Ctrl+D to quit")
    print("-" * 40)
    while True:
        try:
            msg = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg:
            continue
        mem.record("chat", msg)
        try:
            resp, latency = send(msg)
            logs.log("chat:" + msg[:60], "ok", latency)
            print(resp)
        except Exception as e:
            logs.log("chat:" + msg[:60], "error", 0, str(e))
            print("ERR:", e)
    return 0