"""ETHAN daemon loop — extracted subprocess entrypoint for stable daemonisation.

Lancé par chemin de fichier (`sys.executable .../daemon_loop.py`), donc sans le
repo root dans `sys.path` : on l'ajoute explicitement pour réutiliser
l'implémentation canonique `cli.core.daemon._fetch_state` (pas de duplication).
"""

import os
import sys

_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import json  # noqa: E402
import signal  # noqa: E402
import time  # noqa: E402
from datetime import datetime  # noqa: E402

from interfaces.cli.core.daemon import _fetch_state  # noqa: E402

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
