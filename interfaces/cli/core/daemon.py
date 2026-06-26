"""ETHAN daemon — lightweight background state cache.

Uses subprocess.Popen for safe daemonisation (no os.fork() + threads).
Uses fcntl.flock() for atomic PID file locking.
Includes watchdog heartbeat and cache size limit.
"""
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

API = os.environ.get("ETHAN_API", "http://localhost:8000")
CACHE_DIR = os.path.expanduser("~/.ethan")
PID_FILE = os.path.join(CACHE_DIR, "ethan-daemon.pid")
PID_LOCK_FILE = os.path.join(CACHE_DIR, "ethan-daemon.lock")
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")
HEARTBEAT_FILE = os.path.join(CACHE_DIR, "heartbeat")
LOG_FILE = os.path.join(CACHE_DIR, "daemon.log")
DEFAULT_INTERVAL = 5


def _log(msg):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _cache_read():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def _pid_acquire():
    """Atomically acquire PID lock using fcntl.flock()."""
    try:
        import fcntl
        lock_fd = os.open(PID_LOCK_FILE, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o644)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(lock_fd, str(os.getpid()).encode())
        return lock_fd
    except (ImportError, BlockingIOError, OSError):
        return None


def _pid_release(lock_fd):
    """Release PID lock."""
    try:
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
        try:
            os.remove(PID_LOCK_FILE)
        except OSError:
            pass
    except Exception:
        pass


def _pid_read():
    """Read PID from file (best-effort, not atomic)."""
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _pid_write(pid):
    with open(PID_FILE, "w") as f:
        f.write(str(pid))


def _pid_remove():
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


def _is_running(pid):
    if pid is None or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _daemon_is_healthy():
    """Check if daemon is alive via heartbeat."""
    if not os.path.exists(HEARTBEAT_FILE):
        return False
    try:
        mtime = os.path.getmtime(HEARTBEAT_FILE)
        return (time.time() - mtime) < 300  # 5 minutes
    except OSError:
        return False


def cmd_start(args):
    """Start daemon as subprocess."""
    import argparse
    parser = argparse.ArgumentParser(prog="ethan daemon start")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    ns = parser.parse_args(args)

    # Check if already running
    pid = _pid_read()
    if _is_running(pid):
        print(f"daemon already running (pid {pid})")
        sys.exit(1)

    # Clean stale files
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Start daemon as subprocess with its own session
    daemon_entry = os.path.join(os.path.dirname(__file__), "daemon_loop.py")
    try:
        proc = subprocess.Popen(
            [sys.executable, daemon_entry, str(ns.interval)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=CACHE_DIR,
        )
    except OSError as e:
        print(f"daemon start failed: {e}")
        sys.exit(1)

    # Write PID
    _pid_write(proc.pid)

    # Wait briefly to verify it started
    time.sleep(0.5)
    if _is_running(proc.pid):
        print(f"daemon started (pid {proc.pid})")
    else:
        _pid_remove()
        print("daemon start failed — check " + LOG_FILE)
        sys.exit(1)


def cmd_stop(args):
    """Stop daemon."""
    pid = _pid_read()
    if not _is_running(pid):
        print("daemon not running")
        _pid_remove()
        return
    assert pid is not None
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait up to 5 seconds for graceful shutdown
        for _ in range(25):
            if not _is_running(pid):
                break
            time.sleep(0.2)
        if _is_running(pid):
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.2)
        print("daemon stopped")
        _pid_remove()
    except ProcessLookupError:
        print("daemon already dead")
        _pid_remove()


def cmd_status(args):
    """Show daemon status."""
    pid = _pid_read()
    if _is_running(pid):
        healthy = _daemon_is_healthy()
        if healthy:
            print(f"daemon: running (pid {pid})")
        else:
            print(f"daemon: running but unresponsive (pid {pid})")
    else:
        print("daemon: stopped")

    cache = _cache_read()
    if cache:
        ts = cache.get("ts", "?")
        s = cache.get("state", {})
        print(f"cache:   {ts}")
        print(f"mode:    {s.get('mode', '?')}")
        print(f"goal:    {s.get('active_goal', 'none')}")
        print(f"tasks:   {s.get('running_tasks', 0)}")
    else:
        print("cache:   none")