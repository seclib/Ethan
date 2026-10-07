"""ETHAN HTTP client — single HTTP boundary between the CLI and Core API.

Règle d'architecture (AGENTS) : une interface ETHAN ne parle qu'à l'API
Core. Ce module centralise l'URL de base, le token d'authentification,
les retries et le disjoncteur ; les commandes ne réimplémentent pas
leurs propres appels HTTP.

Contrat stable : docs/specs/CLI_CONTRACT.md §5 (exit codes), §7 (auth),
§4.3 (codes d'erreur machine).
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Iterator
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from interfaces.cli.core.errors import (
    CLIError,
    connection_error,
    timeout_error,
)
from interfaces.cli.core.exit_codes import ExitCode, exit_code_for_status

BASE = os.environ.get("ETHAN_API") or os.environ.get("ETHAN_API_URL") or "http://localhost:8000"
MAX_RETRIES = 2
TIMEOUT = 5.0
MAX_PAYLOAD_SIZE = 10240  # 10KB


class APIError(CLIError):
    """HTTP error from Core API mapped to CLI contract exit codes (§5)."""

    def __init__(self, status: int, detail: str, hint: str = ""):
        self.status = status
        self.detail = detail
        if not hint and status == 401:
            hint = "ethan auth login"
        super().__init__(
            f"API {status}: {detail}",
            code=f"CLI-{status}",
            context="the Core API returned an error",
            hint=hint,
            exit_code=int(exit_code_for_status(status)),
            status=status,
        )


def get_base_url() -> str:
    """Resolve the active base API URL."""
    try:
        from interfaces.cli.core.context import get_context

        ctx = get_context()
        if ctx and ctx.api_url:
            return ctx.api_url.rstrip("/")
    except Exception:
        pass
    env_url = os.environ.get("ETHAN_API") or os.environ.get("ETHAN_API_URL")
    if env_url:
        return env_url.rstrip("/")
    try:
        from interfaces.cli.core import config as cli_config

        profile = cli_config.get_profile()
        return profile.get("api_url", "http://localhost:8000").rstrip("/")
    except Exception:
        return "http://localhost:8000"


def get_timeout(default: float = TIMEOUT) -> float:
    """Resolve the client timeout in seconds.

    Priority: explicit ``--timeout`` (context) > ``ETHAN_TIMEOUT`` >
    profile ``timeout`` > ``default``. Regular commands call this with the
    5 s contract deadline (§3.1); a command talking to a slow Core
    subsystem (LLM generation in `chat`) passes a larger ``default`` so a
    deliberate user/profile/env deadline is still honoured.
    """
    try:
        from interfaces.cli.core.context import get_context

        ctx = get_context()
        if ctx and getattr(ctx, "timeout_explicit", False) and ctx.timeout is not None:
            return float(ctx.timeout)
    except Exception:
        pass
    env_to = os.environ.get("ETHAN_TIMEOUT")
    if env_to:
        try:
            return float(env_to)
        except ValueError:
            pass
    try:
        from interfaces.cli.core import config as cli_config

        profile = cli_config.get_profile()
        val = profile.get("timeout")
        if val is not None:
            return float(val)
    except Exception:
        pass
    return default


def get_token() -> str | None:
    """Resolve the API token: Context > ETHAN_TOKEN > credentials.json.

    The credentials file is managed by `ethan auth login` (mode 0600).
    """
    try:
        from interfaces.cli.core.context import get_context

        ctx = get_context()
        if ctx and getattr(ctx, "cli_token_explicit", False) and ctx.token:
            return ctx.token
    except Exception:
        pass

    token = os.environ.get("ETHAN_TOKEN")
    if token:
        return token

    try:
        from interfaces.cli.core import config as cli_config

        stored = cli_config.get_token_from_credentials()
        if stored:
            return stored
    except Exception:
        pass

    try:
        from interfaces.cli import config as legacy_config

        with open(legacy_config.CONFIG_FILE) as f:
            return json.load(f).get("token") or None
    except Exception:
        return None


def request_json(
    method: str,
    path: str,
    payload: dict | None = None,
    *,
    token: str | None = None,
    timeout: float | None = None,
    params: dict[str, Any] | None = None,
) -> dict:
    """Perform an authenticated JSON request against the Core API.

    Args:
        params: Optional query-string parameters (values of None are dropped).

    Raises:
        CLIError / APIError: HTTP error (mapped to contract exit codes §5).
        CLIError (UNAVAILABLE): Core API unreachable (exit 5).
        CLIError (TIMEOUT): Timeout exceeded (exit 7).
    """
    resolved_timeout = timeout if timeout is not None else get_timeout()
    base_url = get_base_url()
    if params:
        query = urlencode({k: v for k, v in params.items() if v is not None})
        if query:
            path = f"{path}{'&' if '?' in path else '?'}{query}"
    headers = {"Accept": "application/json"}
    resolved_token = token if token is not None else get_token()
    if resolved_token:
        headers["Authorization"] = f"Bearer {resolved_token}"

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    # Verbose logging (contract §3.1: diagnostic on stderr)
    is_verbose = False
    try:
        from interfaces.cli.core.context import get_context

        ctx = get_context()
        is_verbose = bool(ctx and ctx.verbose > 0)
    except Exception:
        pass

    if is_verbose:
        from interfaces.cli.core import colors as clr

        print(f"{clr.C.DIM}> {method} {base_url}{path}{clr.C.RESET}", file=sys.stderr)

    req = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urlopen(req, timeout=resolved_timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="replace")
            latency = int((time.time() - t0) * 1000)
            if is_verbose:
                from interfaces.cli.core import colors as clr

                print(
                    f"{clr.C.DIM}< {resp.status} ({latency}ms){clr.C.RESET}",
                    file=sys.stderr,
                )
    except HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(raw)
            detail = parsed.get("detail", raw)
        except (json.JSONDecodeError, AttributeError):
            detail = raw

        # Core API HTTP status mapping to contract exit codes
        if exc.code in (502, 503, 504):
            raise connection_error(f"ETHAN API unavailable ({exc.code}): {detail}") from exc
        raise APIError(exc.code, str(detail)) from exc
    except (TimeoutError, URLError) as exc:
        reason_str = str(getattr(exc, "reason", exc))
        if "timed out" in reason_str.lower():
            raise timeout_error(resolved_timeout) from exc
        raise connection_error(f"ETHAN API unavailable: {reason_str}") from exc
    except Exception as exc:
        if "timed out" in str(exc).lower():
            raise timeout_error(resolved_timeout) from exc
        raise connection_error(f"ETHAN API unavailable: {exc}") from exc

    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise CLIError(
            f"Invalid JSON response from Core API at {path}",
            code="CLI-INVALID-RESPONSE",
            context=f"Raw body: {body[:200]}",
            exit_code=int(ExitCode.OPERATION_FAILED),
        ) from exc


def get_core_version(timeout: float = 2.0) -> str | None:
    """Best-effort Core version via GET /v1/version (never blocks a CLI call).

    Returns None when the Core is unreachable or unauthenticated —
    `version -o json` must stay usable offline to diagnose the API itself
    (contract §8.18).
    """
    try:
        body = request_json("GET", "/v1/version", timeout=timeout)
        version = body.get("version") if isinstance(body, dict) else None
        return str(version) if version else None
    except Exception:  # noqa: BLE001 — offline Core is a normal state here
        return None


def stream_sse(
    path: str,
    payload: dict,
    *,
    timeout: float | None = None,
) -> Iterator[dict]:
    """POST to a Core SSE route and yield the parsed ``data:`` events.

    Transport only — same base URL, Bearer token, deadline and HTTP →
    exit-code mapping as `request_json` (§5), so a command never
    re-implements the HTTP boundary. Each yielded value is the decoded
    JSON object of one Server-Sent Event (Core chat stream contract:
    ``content``, ``content_replace``, ``tool_call``, ``tool_result``,
    ``done``, ``error``).

    Malformed ``data:`` frames are skipped (a partial frame must never
    crash the CLI). `KeyboardInterrupt` propagates untouched so Ctrl-C
    during a generation maps to exit 130 (§5).

    Raises:
        CLIError: same families as `request_json` (APIError / UNAVAILABLE
        / TIMEOUT).
    """
    resolved_timeout = timeout if timeout is not None else get_timeout()
    base_url = get_base_url()
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    resolved_token = get_token()
    if resolved_token:
        headers["Authorization"] = f"Bearer {resolved_token}"

    is_verbose = False
    try:
        from interfaces.cli.core.context import get_context

        ctx = get_context()
        is_verbose = bool(ctx and ctx.verbose > 0)
    except Exception:
        pass
    if is_verbose:
        print(f"> STREAM POST {base_url}{path}", file=sys.stderr)

    req = Request(  # noqa: S310
        f"{base_url}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        resp = urlopen(req, timeout=resolved_timeout)  # noqa: S310
    except HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(raw)
            detail = parsed.get("detail", raw)
        except (json.JSONDecodeError, AttributeError):
            detail = raw
        if exc.code in (502, 503, 504):
            raise connection_error(f"ETHAN API unavailable ({exc.code}): {detail}") from exc
        raise APIError(exc.code, str(detail)) from exc
    except (TimeoutError, URLError) as exc:
        reason_str = str(getattr(exc, "reason", exc))
        if "timed out" in reason_str.lower():
            raise timeout_error(resolved_timeout) from exc
        raise connection_error(f"ETHAN API unavailable: {reason_str}") from exc

    try:
        with resp:
            for raw_line in resp:
                line = (
                    raw_line.decode("utf-8", errors="replace")
                    if isinstance(raw_line, (bytes, bytearray))
                    else str(raw_line)
                ).strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    continue
                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    yield event
    except HTTPError as exc:  # raised while reading the body
        raise APIError(exc.code, str(exc.reason)) from exc
    except (TimeoutError, URLError) as exc:
        reason_str = str(getattr(exc, "reason", exc))
        if "timed out" in reason_str.lower():
            raise timeout_error(resolved_timeout) from exc
        raise connection_error(f"ETHAN API unavailable: {reason_str}") from exc


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

    def reset(self) -> None:
        """Réarme explicitement le disjoncteur."""
        self.failures = 0
        self.last_failure = 0.0


_circuit_breaker = APICircuitBreaker()


def reset_circuit_breaker() -> None:
    """Réarme le disjoncteur global."""
    _circuit_breaker.reset()


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
    headers = {"Content-Type": "application/json"}
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(
        f"{get_base_url()}/v1/message",
        data=data,
        headers=headers,
        method="POST",
    )
    with urlopen(req, timeout=get_timeout()) as r:  # noqa: S310
        raw = r.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
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
            if attempt < MAX_RETRIES:
                should_retry = False
                if isinstance(e, URLError):
                    should_retry = "timed out" in str(e).lower()
                elif isinstance(e, HTTPError):
                    should_retry = 500 <= e.code < 600
                if should_retry:
                    time.sleep(2**attempt)
                    continue
            break
        except (ValueError, TypeError):
            raise
        except Exception:
            _circuit_breaker.record_failure()
            raise

    raise ConnectionError(f"Request failed after {MAX_RETRIES + 1} attempt(s): {last_exception}")


def alive() -> bool:
    try:
        with urlopen(_state_request(), timeout=2) as r:  # noqa: S310
            return r.status == 200
    except Exception:
        return False


def get_state():
    try:
        with urlopen(_state_request(), timeout=2) as r:  # noqa: S310
            return json.loads(r.read())
    except Exception:
        return None


def _state_request() -> Request:
    """GET /v1/state with Bearer token when available."""
    headers = {}
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return Request(f"{get_base_url()}/v1/state", headers=headers, method="GET")
