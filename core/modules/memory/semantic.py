"""ETHAN Memory Module — semantic similarity store.

Stores text embeddings for similarity search.
"""
import json
import os
from datetime import datetime
from pathlib import Path

MEM_DIR = Path.home() / ".ethan" / "memory"
EMBEDDINGS_FILE = MEM_DIR / "embeddings.jsonl"
MAX_EMBEDDINGS = 5000


def _append(path, record):
    try:
        with open(path, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception:
        pass


def _read(path, limit=100):
    if not path.exists():
        return []
    try:
        lines = path.read_text(errors="ignore").splitlines()[-limit:]
        return [json.loads(l) for l in lines if l.strip()]
    except Exception:
        return []


def _rotate(path, max_lines):
    try:
        lines = path.read_text(errors="ignore").splitlines()
        if len(lines) > max_lines:
            path.write_text("\n".join(lines[-max_lines:]) + "\n")
    except Exception:
        pass


def store_embedding(source_type, source_id, content, metadata=None):
    """Store a text embedding record.

    In this minimal implementation, embedding is stored as a hash of content.
    For production, replace with real embedding model (OpenAI, Ollama, etc.).
    """
    record = {
        "ts": datetime.now().isoformat(timespec="milliseconds"),
        "source_type": source_type,
        "source_id": source_id,
        "content": content,
        "embedding_hash": _hash(content),
        "metadata": metadata or {},
    }
    _append(EMBEDDINGS_FILE, record)
    _rotate(EMBEDDINGS_FILE, MAX_EMBEDDINGS)
    return record


def _hash(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def query_similar(text, limit=5):
    """Return records with similar content based on embedding hash similarity.

    Minimal implementation: prefix match on hash.
    Production: use cosine similarity on real embeddings.
    """
    records = _read(EMBEDDINGS_FILE, MAX_EMBEDDINGS)
    target_hash = _hash(text)
    scored = []
    for r in records:
        # Simple similarity: count matching hash prefix chars
        score = sum(1 for a, b in zip(target_hash, r.get("embedding_hash", "")) if a == b)
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:limit]]


def recent_by_source(source_type, limit=20):
    records = _read(EMBEDDINGS_FILE, limit * 2)
    return [r for r in records if r.get("source_type") == source_type][:limit]