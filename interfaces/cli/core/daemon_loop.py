"""ETHAN daemon loop — extracted subprocess entrypoint for stable daemonisation."""
import json
import os
import signal
import sys
import time
from datetime import datetime
from urllib.request import urlopen, Request

API = os.environ.get("ETHAN_API", "http://localhost:8000")
CACHE_DIR = os.path.expanduser("~/.ethan")
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")
LOG_FILE = os.path.join(CACHE_DIR, "daemon.log")
MAX_CACHE_SIZE = 1024 * 1024  # 1MB max cache


def _log(msg):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _cache_write(state):
    """Atomic cache write with size limit."""
    payload = {"ts": datetime.now().isoformat(), "state": state}
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, prefix="cache_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f)
            f.flush()
            os.fsync(f.fileno())
        # Check size before replacing
        size = os.path.getsize(tmp) if os.path.exists(tmp) else 0
        if size > MAX_CACHE_SIZE:
            _log(f"cache too large ({size} bytes), truncating")
            os.remove(tmp)
            return
        os.replace(tmp, CACHE_FILE)
    except (OSError, ValueError) as e:
        _log(f"cache write error: {e}")
        try:
            os.remove(tmp)
        except OSError:
            pass


def _fetch_state():
    """Fetch state from API with validation."""
    try:
        req = Request(f"{API}/state", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as r:
            if r.status != 200:
                _log(f"API returned status {r.status}")
                return None
            raw = r.read()
            return json.loads(raw)
    except Exception as e:
        _log(f"fetch error: {e}")
        return None


def _heartbeat_write():
    """Write heartbeat timestamp."""
    hb_file = os.path.join(CACHE_DIR, "heartbeat")
    try:
        with open(hb_file, "w") as f:
            f.write(datetime.now().isoformat(timespec="seconds"))
    except OSError:
        pass


def daemon_loop(interval=5):
    """Main daemon loop — runs in subprocess."""
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *a: sys.exit(0))

    _log(f"daemon started (pid {os.getpid()})")
    _heartbeat_write()

    last_heartbeat = time.time()
    while True:
        state = _fetch_state()
        if state:
            _cache_write(state)
        # Heartbeat every 60 seconds
        now = time.time()
        if now - last_heartbeat >= 60:
            _heartbeat_write()
            last_heartbeat = now
        time.sleep(interval)


if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    daemon_loop(interval)