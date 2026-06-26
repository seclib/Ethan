"""ETHAN structured logging."""
import json
import os
from datetime import datetime

LOG_DIR = os.path.expanduser("~/.ethan")
LOG_FILE = os.path.join(LOG_DIR, "logs.json")
MAX_ENTRIES = 500


def _ensure():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)


def _load():
    _ensure()
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save(entries):
    while len(entries) > MAX_ENTRIES:
        entries.pop(0)
    tmp = LOG_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(entries, f, indent=1)
    os.replace(tmp, LOG_FILE)


def log(command, status, latency_ms, error=None):
    entries = _load()
    entries.append({
        "ts": datetime.now().isoformat(timespec="milliseconds"),
        "command": command[:160],
        "status": status,
        "latency_ms": latency_ms,
        "error": (error or "")[:200],
    })
    _save(entries)


def query_last(n=20):
    return _load()[-n:]


def query_errors(n=50):
    return [e for e in _load() if e.get("status") != "ok"][-n:]


def query_text(q, n=20):
    q = q.lower()
    out = []
    for e in _load():
        hay = (e.get("command", "") + " " + e.get("error", "")).lower()
        if q in hay:
            out.append(e)
        if len(out) >= n:
            break
    return out