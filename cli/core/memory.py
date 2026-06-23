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


SESSION_FILE = os.path.join(MEM_DIR, "session.txt")


def record(cmd_type, text, session_id=None):
    entries = _load()
    entry = {
        "text": text[:MAX_TEXT],
        "ts": datetime.now().isoformat(timespec="seconds"),
        "type": cmd_type,
    }
    if session_id:
        entry["session"] = session_id
    entries.append(entry)
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


# ── Session Management ────────────────────────────────

def new_session() -> str:
    """Create a new session ID and save it."""
    import uuid
    session_id = str(uuid.uuid4())
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        f.write(session_id)
    return session_id


def resume_session() -> str:
    """Resume the last session ID, or create a new one if missing."""
    if os.path.exists(SESSION_FILE):
        sid = open(SESSION_FILE).read().strip()
        if sid:
            return sid
    return new_session()


def save_session(session_id: str) -> None:
    """Save the current session ID for resume."""
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        f.write(session_id)


def get_history(session_id: str, limit=20) -> list[dict]:
    """Get history entries for a specific session."""
    entries = _load()
    session_entries = [e for e in entries if e.get("session") == session_id]
    return session_entries[-limit:]


# ── Session Information ────────────────────────────────

def get_session_info(session_id: str) -> dict:
    """Return session metadata."""
    history = get_history(session_id, limit=1000)
    now = datetime.now()
    return {
        "id": session_id,
        "short_id": session_id[:8],
        "created_at": history[0]["ts"] if history else now.isoformat(timespec="seconds"),
        "last_activity": history[-1]["ts"] if history else now.isoformat(timespec="seconds"),
        "message_count": len(history),
        "context_items": len(history),
        "context_tokens": len(history) * 50,  # rough estimate: 50 tokens per message
        "context_max": 8192,
        "context_pct": min(100, int(len(history) * 50 / 8192 * 100)),
    }


def get_context_usage(session_id: str) -> tuple[int, int]:
    """Return (used_tokens, max_tokens)."""
    info = get_session_info(session_id)
    return (info["context_tokens"], info["context_max"])


def reset_context(session_id: str) -> None:
    """Clear memory context for a session (keep session ID)."""
    # Remove session entries from history
    entries = _load()
    entries = [e for e in entries if e.get("session") != session_id]
    _save(entries)
