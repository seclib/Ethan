"""ETHAN HTTP client."""
import json
import os
import time
from urllib.request import Request, urlopen

BASE = os.environ.get("ETHAN_API", "http://localhost:8000")


def send(msg):
    t0 = time.time()
    data = json.dumps({"content": msg}).encode()
    req = Request(f"{BASE}/message", data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=10) as r:
        payload = json.loads(r.read())
    latency = int((time.time() - t0) * 1000)
    return payload.get("response", payload.get("error", "no response")), latency


def alive():
    try:
        with urlopen(f"{BASE}/state", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def get_state():
    try:
        with urlopen(f"{BASE}/state", timeout=3) as r:
            return json.loads(r.read())
    except Exception:
        return None