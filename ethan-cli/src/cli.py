"""ETHAN CLI — native system command implementation.

Commands:
  ethan <message>   One-shot: send and print response
  ethan chat        Interactive REPL loop
  ethan status      System status overview
"""

import sys
import os
from client import send, state, alive
from memory import record, recent, frequent, stats


def get_apibase() -> str:
    return os.environ.get("ETHAN_API", "http://localhost:8000")


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def cmd_send(args: list) -> None:
    """ethan <message> — one-shot send."""
    if not args:
        die("usage: ethan <message>")
    text = " ".join(args)
    if not alive():
        die(f"ETHAN API unreachable at {get_apibase()}")
    data = send(text)
    resp = data.get("response", data.get("error", "no response"))
    print(resp)


def cmd_chat() -> None:
    """ethan chat — interactive REPL."""
    if not alive():
        die(f"ETHAN API unreachable at {get_apibase()}")

    cfg = os.path.expanduser("~/.ethan_history")
    print("ETHAN chat — Ctrl+D or 'exit' to quit")
    print("-" * 40)
    while True:
        try:
            msg = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not msg:
            continue
        if msg.lower() in ("exit", "quit", "q"):
            break
        data = send(msg)
        resp = data.get("response", data.get("error", "no response"))
        print(resp)
        with open(cfg, "a") as f:
            f.write(f">>> {msg}\n{resp}\n\n")


def cmd_status() -> None:
    """ethan status — print system state."""
    if not alive():
        die(f"ETHAN API unreachable at {get_apibase()}")

    s = state()
    print(f"Mode:       {s.get('mode', '?')}")
    print(f"Goal:       {s.get('active_goal', 'none')}")
    print(f"Tasks:      {s.get('running_tasks', 0)}")
    last = s.get("last_event")
    if last:
        print(f"Last event: [{last.get('type','?')}] {str(last.get('data',''))[:120]}")


def cmd_suggest(args: list) -> None:
    """ethan suggest — show frequent/recent commands."""
    limit = int(args[0]) if args else 5
    freq = frequent(limit)
    if not freq:
        print("No history yet.")
        return
    print("Frequent commands:")
    for i, entry in enumerate(freq, 1):
        print(f"  {i}. {entry['text']}  (x{entry['count']})")

    rec = recent(limit)
    print("\nRecent commands:")
    for i, entry in enumerate(rec, 1):
        print(f"  {i}. {entry['text']}  [{entry['type']}]")


def cmd_help() -> None:
    print(f"ETHAN CLI — {get_apibase()}")
    print()
    print("  ethan <message>     One-shot: send and print response")
    print("  ethan chat          Interactive REPL loop")
    print("  ethan status        System status overview")
    print("  ethan suggest [N]   Show frequent + recent commands")
    print("  ethan daemon <cmd>  Manage background cache daemon")
    print("             start   Start daemon")
    print("             stop    Stop daemon")
    print("             status  Daemon status + cached state")
    print("  ethan --help        This message")
    print()
    print("Environment:")
    print("  ETHAN_API           API base URL (default: http://localhost:8000)")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        cmd_help()
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "suggest":
        cmd_suggest(args)
    elif cmd == "daemon":
        from daemon import cmd_start as d_start, cmd_stop as d_stop, cmd_status as d_status
        if not args:
            print("usage: ethan daemon <start|stop|status>")
            sys.exit(1)
        sub = args[0]
        sub_args = args[1:]
        if sub == "start":
            d_start(sub_args)
        elif sub == "stop":
            d_stop(sub_args)
        elif sub == "status":
            d_status(sub_args)
        else:
            print(f"unknown daemon command: {sub}")
            sys.exit(1)
    elif cmd == "chat":
        cmd_chat()
    elif cmd == "status":
        cmd_status()
    elif cmd in ("-v", "--version"):
        print("ethan 1.0")
    else:
        # record one-shot command
        record("send", " ".join([cmd] + args))
        cmd_send([cmd] + args)
