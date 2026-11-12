"""ETHAN Memory Module — persistent storage implementation."""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

MEM_DIR = Path.home() / ".ethan" / "memory"
MEM_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = MEM_DIR / "events.jsonl"
HISTORY_FILE = MEM_DIR / "history.jsonl"
MAX_EVENTS = 10000


def _append_jsonl(path, record):
    try:
        with open(path, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception:
        pass


def _read_jsonl(path, limit=100):
    if not path.exists():
        return []
    try:
        lines = path.read_text(errors="ignore").splitlines()[-limit:]
        return [json.loads(l) for l in lines if l.strip()]
    except Exception:
        return []


def store_event(source, event_type, payload, session_id=None, parent_id=None):
    record = {
        "ts": datetime.now().isoformat(timespec="milliseconds"),
        "source": source,
        "type": event_type,
        "payload": payload,
        "parent_id": parent_id,
        "session_id": session_id,
    }
    _append_jsonl(EVENTS_FILE, record)
    _rotate(EVENTS_FILE, MAX_EVENTS)
    return record


def store_command(interface, command, args, status, latency_ms, session_id=None):
    record = {
        "ts": datetime.now().isoformat(timespec="milliseconds"),
        "interface": interface,
        "command": command,
        "args": args,
        "status": status,
        "latency_ms": latency_ms,
        "session_id": session_id,
    }
    _append_jsonl(HISTORY_FILE, record)
    _rotate(HISTORY_FILE, MAX_EVENTS)
    return record


def query_events(source=None, event_type=None, limit=20, since=None):
    events = _read_jsonl(EVENTS_FILE, limit * 3)
    out = []
    for e in events:
        if source and e.get("source") != source:
            continue
        if event_type and e.get("type") != event_type:
            continue
        if since and e.get("ts", "") < since:
            continue
        out.append(e)
        if len(out) >= limit:
            break
    return out


def query_history(interface=None, limit=20, status=None):
    history = _read_jsonl(HISTORY_FILE, limit * 3)
    out = []
    for h in history:
        if interface and h.get("interface") != interface:
            continue
        if status and h.get("status") != status:
            continue
        out.append(h)
        if len(out) >= limit:
            break
    return out


def _rotate(path, max_lines):
    try:
        lines = path.read_text(errors="ignore").splitlines()
        if len(lines) > max_lines:
            path.write_text("\n".join(lines[-max_lines:]) + "\n")
    except Exception:
        pass


def recent_embeddings(limit=10):
    """Return recent events with generated text for semantic similarity."""
    events = _read_jsonl(EVENTS_FILE, limit)
    out = []
    for e in events:
        text = json.dumps(e.get("payload", {}), default=str)
        out.append({
            "id": e.get("ts"),
            "text": text,
            "source": e.get("source"),
            "type": e.get("type"),
        })
    return out