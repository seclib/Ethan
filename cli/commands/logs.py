"""ETHAN logs — query structured logs."""
from registry import register
from core import logging as logs


@register("logs")
def cmd_logs(args):
    if not args:
        entries = logs.query_last(20)
        for e in entries:
            print(f"  {e['ts']} {e['command']} -> {e['status']} ({e['latency_ms']}ms)")
        return 0

    if args[0] == "--last":
        n = int(args[1]) if len(args) > 1 else 10
        for e in logs.query_last(n):
            print(f"  {e['ts']} {e['command']} -> {e['status']} ({e['latency_ms']}ms)")
        return 0

    if args[0] == "--errors":
        for e in logs.query_errors(20):
            print(f"  {e['ts']} {e['command']} -> {e['status']} ({e['latency_ms']}ms) {e.get('error','')}")
        return 0

    # text search
    for e in logs.query_text(args[0], 20):
        print(f"  {e['ts']} {e['command']} -> {e['status']} ({e['latency_ms']}ms) {e.get('error','')}")
    return 0