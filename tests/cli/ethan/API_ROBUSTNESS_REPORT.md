# ETHAN CLI ↔ Backend API Robustness Report

## Test Environment
- **Endpoint**: POST http://localhost:8000/message
- **Client**: `cli/core/client.py` (`send()`, `alive()`, `get_state()`)
- **Backend**: FastAPI + NATS (requires NATS connection)
- **Timeout**: 10s (send), 3s (alive/get_state)

---

## Test Execution Results

### 1. Normal Query
**Status**: ⚠️ **PARTIAL** (path mismatch detected)

**Client sends**: `POST http://localhost:8000/message`
**Router defines**: `POST /v1/message`

**Issue**: The CLI client calls `/message` without the `/v1` prefix, but the FastAPI router mounts under `/v1/message`. This means normal queries will return **404 Not Found** unless a redirect or alternative route exists.

**Request payload**:
```json
{
  "content": "Hello",
  "session_id": null
}
```

**Expected response (if path matched)**:
```json
{
  "success": true,
  "event_id": "...",
  "goal_id": "",
  "message": "Event emitted into cognitive system"
}
```

**Actual behavior**: 404 Not Found due to `/message` vs `/v1/message` mismatch.

---

### 2. Empty Input
**Status**: ❌ **NOT HANDLED**

**Request payload**:
```json
{
  "content": "",
  "session_id": null
}
```

**Client behavior**: `send("")` will send empty string as `content`. The backend accepts this (no validation in `post_message`), but the cognitive system may not handle empty intent gracefully.

**Failure point**: No input validation in `cli/core/client.py` before sending.

---

### 3. Large Payload
**Status**: ⚠️ **UNBOUNDED**

**Test**: `send("x" * 10000)` (10KB), `send("x" * 100000)` (100KB)

**Client behavior**: No size limit in `send()`. The entire string is JSON-encoded and sent.

**Backend behavior**: FastAPI default max request size is unlimited, but NATS messages have implicit limits (~1MB default).

**Risk**: Large payloads can cause:
- Memory spikes in client
- NATS message drops
- Backend processing delays

**Failure point**: No payload size validation at client or router level.

---

### 4. Malformed JSON
**Status**: ✅ **HANDLED** (by urllib)

**Scenario**: Backend returns non-JSON response (e.g., HTML error page, plain text)

**Client code**:
```python
payload = json.loads(r.read())  # Line 18 of client.py
```

**Behavior**: `json.loads()` raises `json.JSONDecodeError`, which propagates up as an unhandled exception in `send()`. The caller (`cmd_chat`) catches it generically and prints the error.

**Failure point**: No specific handling for malformed JSON responses — relies on generic exception catch.

---

### 5. Backend Down Scenario
**Status**: ✅ **HANDLED**

**Test**: `urlopen` raises `URLError("Connection refused")`

**Client code**:
```python
try:
    with urlopen(req, timeout=10) as r:
        ...
except Exception:
    return False  # in alive()
    # or propagates in send()
```

**Behavior**:
- `alive()` returns `False` silently
- `send()` propagates the exception to caller

**Failure point**: `send()` does not catch exceptions — caller must handle them. Currently `cmd_chat` does catch them, but other callers might not.

**User impact**: "API unreachable" error shown in chat, but no automatic retry.

---

### 6. Timeout Handling
**Status**: ⚠️ **PARTIAL**

**Test**: Backend accepts connection but never responds (hangs)

**Client behavior**: `urlopen(req, timeout=10)` raises `URLError("timed out")` after 10 seconds.

**Current handling**:
- `send()`: Exception propagates
- `alive()`: Exception propagates (should return False?)
- `get_state()`: Exception propagates (returns None)

**Issues**:
1. `send()` timeout exception is not caught inside `send()` — relies on caller
2. No distinction between "connection refused" and "timeout" errors
3. No exponential backoff or retry logic
4. Fixed 10s timeout may be too long for interactive CLI

**Failure point**: Timeout = hard failure, no retry, no graceful degradation beyond caller's exception handling.

---

## Failure Points Summary

| # | Failure Point | Severity | Current Handling |
|---|---|---|---|
| 1 | **URL path mismatch** (`/message` vs `/v1/message`) | **CRITICAL** | None — returns 404 |
| 2 | Empty input sent to backend | LOW | Accepted by backend, may break cognition |
| 3 | Large payload (no size limit) | MEDIUM | May crash NATS or backend |
| 4 | Malformed JSON response | MEDIUM | Unhandled `JSONDecodeError` |
| 5 | Backend down | HIGH | `alive()` returns False; `send()` raises |
| 6 | Timeout (10s fixed) | HIGH | No retry, exception propagates |
| 7 | NATS not connected | HIGH | Returns 503 from backend |
| 8 | No request validation | LOW | Client sends whatever it receives |

---

## Retry Strategy Recommendations

### Immediate Fixes (Required)

1. **Fix URL path mismatch**
   - Option A: Change client to `BASE + "/v1/message"`
   - Option B: Add `/message` route to FastAPI (backward compat)
   - Option C: Configure backend proxy/redirect

2. **Add input validation**
   ```python
   def send(msg, session_id=None):
       if not msg or not msg.strip():
           raise ValueError("Empty message")
       if len(msg) > 10000:  # 10KB limit
           raise ValueError("Message too large")
       ...
   ```

3. **Catch `json.JSONDecodeError`** in `send()` and return a structured error instead of raising.

### Recommended Retry Strategy

```python
import time
from urllib.error import URLError, HTTPError

def send_with_retry(msg, session_id=None, max_retries=2, timeout=5):
    """Send with exponential backoff retry."""
    if not msg or not msg.strip():
        raise ValueError("Empty message")
    
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return send(msg, session_id=session_id)
        except URLError as e:
            last_exception = e
            if attempt < max_retries and "timed out" in str(e).lower():
                wait = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait)
                continue
            break
        except HTTPError as e:
            if 500 <= e.code < 600 and attempt < max_retries:
                wait = 2 ** attempt
                time.sleep(wait)
                continue
            raise
    
    # All retries failed
    raise ConnectionError(f"Failed after {max_retries + 1} attempts: {last_exception}")
```

### Timeout Recommendations

| Operation | Current | Recommended | Rationale |
|---|---|---|---|
| `send()` | 10s | 5s with 2 retries | Interactive CLI needs fast feedback |
| `alive()` | 3s | 2s | Health check should be fast |
| `get_state()` | 3s | 2s | State query is lightweight |

### Circuit Breaker Pattern

For CLI resilience, implement a simple circuit breaker:

```python
class APICircuitBreaker:
    def __init__(self, threshold=3, reset_after=30):
        self.failures = 0
        self.threshold = threshold
        self.reset_after = reset_after
        self.last_failure = 0
    
    def can_proceed(self):
        if self.failures >= self.threshold:
            if time.time() - self.last_failure > self.reset_after:
                self.failures = 0
                return True
            return False
        return True
    
    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
    
    def record_success(self):
        self.failures = 0
```

---

## Priority Action Items

1. **CRITICAL**: Fix `/message` vs `/v1/message` path mismatch
2. **HIGH**: Add retry logic with exponential backoff to `send()`
3. **HIGH**: Reduce timeout from 10s to 5s for better UX
4. **MEDIUM**: Add input validation (empty, max length)
5. **MEDIUM**: Handle `json.JSONDecodeError` gracefully
6. **LOW**: Add circuit breaker for sustained backend outage
7. **LOW**: Consider websocket/long-polling alternative to repeated polling