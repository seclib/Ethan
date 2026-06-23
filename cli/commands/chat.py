"""ETHAN chat — interactive REPL with reminders and memory hints."""

import sys
import time
from datetime import datetime

from cli.core import colors as clr
from cli.core import memory as mem
from cli.core.logging import log as logs_log
from cli.core.client import send, alive
from cli.core.intent import PromptIntelligence

try:
    from cli.registry import register

    @register("chat")
    def cmd_chat(args):
        show_chat(args)
except ImportError:
    def cmd_chat(args):
        show_chat(args)


def show_chat(args):
    resume = "--resume" in args or "-r" in args
    if resume:
        session_id = mem.resume_session()
    else:
        session_id = mem.new_session()
    if not alive():
        print()
        print(clr.error("API unreachable", "ethan daemon may be stopped", "try: ethan daemon start"))
        return 1

    info = mem.get_session_info(session_id)
    history = mem.get_history(session_id, limit=10) if resume else []

    # ── Welcome ────────────────────────────────────────
    print()
    print(clr.section(f"ETHAN Chat  ◇  session {info['short_id']}"))
    print(clr.info("Ctrl+D or /exit to quit  •  /help for commands"))
    print(clr.info("/reset to clear context  •  /new for fresh session"))
    print()

    if resume and history:
        print(clr.info(f"{len(history)} previous interactions restored"))
        print()
        for entry in history:
            role = entry.get("role", "user")
            text = entry.get("text", "")
            ts = entry.get("ts", "")
            if role == "user":
                print_user(text, ts)
            else:
                print_assistant(text, ts)
        print()

    # Track whether we've shown the memory hint this session
    showed_memory_hint = False

    # ── Main loop ──────────────────────────────────────
    while True:
        try:
            print(clr.prompt("chat"), end="", flush=True)
            msg = sys.stdin.readline().strip()
            if not msg:
                if sys.stdin.isatty():
                    continue
                else:
                    break
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not msg:
            continue

        # Built-in commands
        if msg == "/exit" or msg == "/q":
            break
        if msg == "/resume":
            mem.save_session(session_id)
            print(clr.metadata(f"Session saved: {mem.resume_session()[:8]}"))
            continue
        if msg == "/history":
            show_history(session_id)
            continue
        if msg == "/reset":
            mem.reset_context(session_id)
            print()
            print(clr.section("Context cleared"))
            print(clr.success("Session reset — fresh start"))
            showed_memory_hint = False
            continue
        if msg == "/new":
            mem.save_session(session_id)
            session_id = mem.new_session()
            print()
            print(clr.section(f"New session  ◇  {mem.get_session_info(session_id)['short_id']}"))
            print(clr.success("New session started"))
            showed_memory_hint = False
            continue
        if msg == "/session":
            show_session_info(session_id)
            continue
        if msg == "/ctx":
            show_context_info(session_id)
            continue
        if msg.startswith("/"):
            print(clr.warn(f"Unknown command: {msg}"))
            continue

        # Store user message
        mem.record(session_id, "user", msg)
        print_user(msg)

        # Send to API with typing indicator
        try:
            start = time.time()
            response_text = send_with_typing(msg, session_id)
            latency = int((time.time() - start) * 1000)
            logs_log("chat:" + msg[:60], "ok", latency)
        except Exception as e:
            logs_log("chat:" + msg[:60], "error", 0, str(e))
            print(clr.error(str(e)))
            continue

        # Show memory hint once per session when context is loaded
        if not showed_memory_hint:
            ctx_count = mem.get_context_usage(session_id)[0]
            if ctx_count > 0:
                print()
                print(clr.info(f"Using {ctx_count} previous interactions for context"))
                showed_memory_hint = True

        # Proactive suggestions
        suggestions = PromptIntelligence.suggest_next(history=[], current=PromptIntelligence.classify(msg))
        if suggestions:
            print()
            print(clr.section("What next?"))
            for s in suggestions:
                print(clr.item(s))

    # ── Farewell ───────────────────────────────────────
    mem.save_session(session_id)
    print()
    print(clr.metadata(f"Session saved ({session_id[:8]})"))
    print(clr.info("See you next time."))
    return 0


# ---- Display helpers ----


def print_user(text: str, ts: str | None = None):
    print()
    print(f"  {clr.C.CYAN}{clr.I.ARROW} you{clr.C.RESET}", end="")
    if ts:
        print(f"  {clr.C.DIM}{ts}{clr.C.RESET}", end="")
    print()
    print(f"    {text}")


def print_assistant(text: str, ts: str | None = None):
    print()
    print(f"  {clr.C.BLUE}{clr.I.SECTION} ethan{clr.C.RESET}", end="")
    if ts:
        print(f"  {clr.C.DIM}{ts}{clr.C.RESET}", end="")
    print()
    for line in text.split("\n"):
        print(f"    {line}")
    print()


def show_history(session_id: str):
    history = mem.get_history(session_id, limit=20)
    if not history:
        print(clr.info("No history for this session."))
        return
    print(clr.section(f"History ({len(history)} entries)"))
    for entry in history:
        role = entry.get("role", "?")
        text = entry.get("text", "")[:80]
        ts = entry.get("ts", "")[:16]
        icon = clr.I.ARROW if role == "user" else clr.I.SECTION
        color = clr.C.CYAN if role == "user" else clr.C.BLUE
        print(f"  {color}{icon}{clr.C.RESET} {clr.C.DIM}{ts}{clr.C.RESET} {text}")
    print()


def show_session_info(session_id: str):
    info = mem.get_session_info(session_id)
    print()
    print(clr.section(f"Session  ◇  {info['short_id']}"))
    print(clr.definition_list({
        "Created": info["created_at"],
        "Last active": info["last_activity"],
        "Messages": str(info["message_count"]),
        "Context": f"{info['context_tokens']} / {info['context_max']} tokens ({info['context_pct']}%)",
    }))
    print()


def show_context_info(session_id: str):
    used, max_tokens = mem.get_context_usage(session_id)
    pct = int(used / max_tokens * 100) if max_tokens > 0 else 0
    status = "● healthy" if pct < 80 else "◐ high" if pct < 95 else "✗ full"
    print()
    print(clr.section(f"Context  ◇  {session_id[:8]}"))
    mem_count = len(mem.get_history(session_id, limit=1000))
    print(clr.definition_list({
        "Memory": f"{mem_count} previous interactions",
        "Tokens": f"{used} used / {max_tokens} max",
        "Status": status,
        "Reset": "/reset",
    }))
    print()


def send_with_typing(msg: str, session_id: str):
    sys.stdout.write(f"  {clr.C.PURPLE}{clr.I.INFO} ethan{clr.C.RESET}")
    sys.stdout.flush()

    try:
        response_text, _ = send(msg, session_id=session_id)
    except Exception as e:
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()
        raise e

    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

    mem.record(session_id, "assistant", response_text)
    print_assistant(response_text, f"{time.time():.1f}s")
    return response_text