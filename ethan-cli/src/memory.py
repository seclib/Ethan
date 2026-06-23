"""ETHAN Local Memory — command history + smart suggestions.

Storage: ~/.ethan/history.json
Format: [{text, ts, type}, ...]
Limit: 50 entries, FIFO prune.
Privacy: text truncated to 80 chars, no secrets.
"""

import json
import os
from collections import Counter
from datetime import datetime

MEM_DIR = os.path.expanduser("~/.ethan")
HIST_FILE = os.path.join(MEM_DIR, "history.json")
MAX_ENTRIES = 50
MAX_TEXT = 80


def _ensure() -> None:
    os.makedirs(MEM_DIR, exist_ok=True)
    if not os.path.exists(HIST_FILE):
        with open(HIST_FILE, "w") as f:
            json.dump([], f)


def _load() -> list:
    _ensure()
    try:
        with open(HIST_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save(entries: list) -> None:
    tmp = HIST_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(entries, f, indent=1)
    os.replace(tmp, HIST_FILE)


def record(cmd_type: str, text: str) -> None:
    """Append one command to history."""
    entries = _load()
    truncated = text[:MAX_TEXT]
    entries.append({
        "text": truncated,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "type": cmd_type,
    })
    # prune FIFO
    while len(entries) > MAX_ENTRIES:
        entries.pop(0)
    _save(entries)


def recent(n: int = 10) -> list:
    """Return last n entries."""
    return _load()[-n:]


def frequent(n: int = 5) -> list:
    """Return n most frequent commands by normalized text."""
    entries = _load()
    counts = Counter(e["text"] for e in entries)
    return [{"text": k, "count": v} for k, v in counts.most_common(n)]


def stats() -> dict:
    entries = _load()
    types = Counter(e["type"] for e in entries)
    return {
        "total": len(entries),
        "types": dict(types),
        "last_ts": entries[-1]["ts"] if entries else None,
    }