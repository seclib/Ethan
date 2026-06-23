"""HTTP client for ETHAN API — stdlib only."""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

API = os.environ.get("ETHAN_API", "http://localhost:8000")
TIMEOUT = 15


def send(text: str) -> dict:
    """POST /message, return parsed JSON."""
    payload = json.dumps({"content": text}).encode()
    req = Request(
        f"{API}/message",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def state() -> dict:
    """GET /state, return parsed JSON."""
    with urlopen(f"{API}/state", timeout=5) as r:
        return json.loads(r.read())


def alive() -> bool:
    """Check if ETHAN API is reachable."""
    try:
        with urlopen(f"{API}/state", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False