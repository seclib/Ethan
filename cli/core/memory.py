"""ETHAN local memory — command history + suggestions."""
import json
import os
from collections import Counter
from datetime import datetime

MEM_DIR = os.path.expanduser("~/.ethan")
MEM_FILE = os.path.join(MEM_DIR, "history.json")
MAX_ENTRIES = 100
MAX_TEXT = 120


def _ensure():
    os.makedirs(MEM_DIR, exist_ok=True)
    if not os.path.exists(MEM_FILE):
        with open(MEM_FILE, "w") as f:
            json.dump([], f)


def _load():
    _ensure()
    try:
        with open(MEM_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save(entries):
    while len(entries) > MAX_ENTRIES:
        entries.pop(0)
    tmp = MEM_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(entries, f, indent=1)
    os.replace(tmp, MEM_FILE)


def record(cmd_type, text):
    entries = _load()
    entries.append({
        "text": text[:MAX_TEXT],
        "ts": datetime.now().isoformat(timespec="seconds"),
        "type": cmd_type,
    })
    _save(entries)


def recent(n=10):
    return _load()[-n:]


def frequent(n=5):
    entries = _load()
    counts = Counter(e["text"] for e in entries)
    return [{"text": k, "count": v} for k, v in counts.most_common(n)]


def suggest_prefix(prefix, n=5):
    entries = _load()
    seen = []
    p = prefix.lower()
    for e in entries:
        t = e["text"]
        if t.lower().startswith(p) and t not in seen:
            seen.append(t)
        if len(seen) >= n:
            break
    return seen