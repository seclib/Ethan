"""ETHAN Daemon — lightweight background state cache.

Behavior:
- start: forks to background, polls /state every interval, caches to ~/.ethan/cache.json
- stop: SIGTERM daemon via PID file
- status: prints daemon status + cached state summary
"""

import json
import os
import signal
import sys
import time
from datetime import datetime
from urllib.request import urlopen

API = os.environ.get("ETHAN_API", "http://localhost:8000")
CACHE_DIR = os.path.expanduser("~/.ethan")
PID_FILE = os.path.join(CACHE_DIR, "ethan-daemon.pid")
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")
LOG_FILE = os.path.join(CACHE_DIR, "daemon.log")

DEFAULT_INTERVAL = 5  # seconds


def _log(msg: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def _cache_write(state: dict) -> None:
    payload = {
        "ts": datetime.now().isoformat(),
        "state": state,
    }
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
    os.replace(tmp, CACHE_FILE)


def _cache_read() -> dict | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def _pid_write() -> None:
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def _pid_read() -> int | None:
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _pid_remove() -> None:
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


def _is_running(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return False


def _fetch_state() -> dict | None:
    try:
        with urlopen(f"{API}/state", timeout=3) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _daemon_loop(interval: int) -> None:
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *a: sys.exit(0))
    _pid_write()
    _log("daemon started")

    while True:
        state = _fetch_state()
        if state:
            _cache_write(state)
        time.sleep(interval)


def cmd_start(args: list) -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="ethan daemon start")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Poll interval (seconds)")
    ns = parser.parse_args(args)

    pid = _pid_read()
    if _is_running(pid):
        print(f"daemon already running (pid {pid})")
        sys.exit(1)

    os.makedirs(CACHE_DIR, exist_ok=True)
    pid = os.fork()
    if pid > 0:
        time.sleep(0.3)
        if _is_running(pid):
            print(f"daemon started (pid {pid})")
        else:
            print("daemon start failed — check " + LOG_FILE)
            sys.exit(1)
        return

    if pid == 0:
        os.setsid()
        _daemon_loop(ns.interval)


def cmd_stop(args: list) -> None:
    pid = _pid_read()
    if not _is_running(pid):
        print("daemon not running")
        _pid_remove()
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.3)
        if _is_running(pid):
            print("daemon stop failed")
            sys.exit(1)
        print("daemon stopped")
        _pid_remove()
    except ProcessLookupError:
        print("daemon already dead")
        _pid_remove()


def cmd_status(args: list) -> None:
    pid = _pid_read()
    if _is_running(pid):
        print(f"daemon: running (pid {pid})")
    else:
        print("daemon: stopped")

    cache = _cache_read()
    if cache:
        ts = cache.get("ts", "?")
        s = cache.get("state", {})
        age = datetime.now().isoformat()
        print(f"cache:   {ts}")
        print(f"mode:    {s.get('mode','?')}")
        print(f"goal:    {s.get('active_goal','none')}")
        print(f"tasks:   {s.get('running_tasks',0)}")
    else:
        print("cache:   none")