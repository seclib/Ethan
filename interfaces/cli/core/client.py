"""ETHAN HTTP client."""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.environ.get("ETHAN_API", "http://localhost:8000")
MAX_RETRIES = 2
TIMEOUT = 5
MAX_PAYLOAD_SIZE = 10240  # 10KB


class APICircuitBreaker:
    """Simple circuit breaker for sustained backend outages."""

    def __init__(self, threshold: int = 3, reset_after: int = 30):
        self.failures = 0
        self.threshold = threshold
        self.reset_after = reset_after
        self.last_failure = 0.0

    def can_proceed(self) -> bool:
        if self.failures >= self.threshold:
            if time.time() - self.last_failure > self.reset_after:
                self.failures = 0
                return True
            return False
        return True

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure = time.time()

    def record_success(self) -> None:
        self.failures = 0


_circuit_breaker = APICircuitBreaker()


def _validate_input(msg: str) -> None:
    """Validate input before sending."""
    if not msg or not msg.strip():
        raise ValueError("Empty message")
    if len(msg) > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Message too large ({len(msg)} bytes, max {MAX_PAYLOAD_SIZE})")


def _do_send(msg, session_id=None) -> tuple[str, int]:
    """Single HTTP request."""
    _validate_input(msg)
    t0 = time.time()
    body = {"content": msg}
    if session_id:
        body["session_id"] = session_id
    data = json.dumps(body).encode()
    req = Request(
        f"{BASE}/v1/message",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=TIMEOUT) as r:
        raw = r.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed JSON response
        return ("error: malformed response from server", int((time.time() - t0) * 1000))
    latency = int((time.time() - t0) * 1000)
    return payload.get("response", payload.get("error", "no response")), latency


def send(msg, session_id=None) -> tuple[str, int]:
    """Send with retry and circuit breaker."""
    if not _circuit_breaker.can_proceed():
        raise ConnectionError("API circuit breaker open — backend may be down")

    last_exception = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response, latency = _do_send(msg, session_id=session_id)
            _circuit_breaker.record_success()
            return response, latency
        except (URLError, HTTPError, ConnectionError) as e:
            last_exception = e
            _circuit_breaker.record_failure()
            # Retry on timeout or transient server errors
            if attempt < MAX_RETRIES:
                should_retry = False
                if isinstance(e, URLError):
                    should_retry = "timed out" in str(e).lower()
                elif isinstance(e, HTTPError):
                    should_retry = 500 <= e.code < 600
                if should_retry:
                    time.sleep(2**attempt)  # exponential backoff: 1s, 2s
                    continue
            break
        except Exception:
            _circuit_breaker.record_failure()
            raise

    raise ConnectionError(f"Request failed after {MAX_RETRIES + 1} attempt(s): {last_exception}")


def alive() -> bool:
    try:
        with urlopen(f"{BASE}/v1/state", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def get_state():
    try:
        with urlopen(f"{BASE}/v1/state", timeout=2) as r:
            return json.loads(r.read())
    except Exception:
        return None
