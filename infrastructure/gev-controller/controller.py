#!/usr/bin/env python3
"""GEV Controller Sidecar — minimal HTTP bridge for Docker Compose lifecycle.

This sidecar runs alongside ethan-api and provides a restricted HTTP API
that proxies a fixed set of Docker Compose commands.  The ethan-api
container does NOT have the Docker socket mounted; it delegates lifecycle
operations to this controller over the internal Docker network.

Security model:
- Bearer token authentication on every request (fail-closed).
- Fixed command allowlist — no arbitrary Docker commands.
- No shell=True, no string interpolation in subprocess argv.
- Secrets redacted from all output before returning.

Endpoints:
  GET  /health              → TCP probe to GEV_TARGET_HOST:GEV_TARGET_PORT
  GET  /status              → docker compose ps --format json
  POST /start               → docker compose up -d
  POST /stop                → docker compose stop
  POST /restart             → docker compose restart
  GET  /logs?tail=100       → docker compose logs --tail=N --no-color
"""

from __future__ import annotations

import http.server
import json
import logging
import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# ── Configuration ────────────────────────────────────────────────────────────

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 9400

COMPOSE_FILE = Path("/project/compose.yaml")

# Bearer token — fail-closed: empty / unset ⇒ ALL requests denied.
AUTH_TOKEN: str = os.environ.get("GEV_CONTROLLER_TOKEN", "").strip()

# Health-check target (the actual Odin / GEV app)
TARGET_HOST: str = os.environ.get("GEV_TARGET_HOST", "127.0.0.1")
TARGET_PORT: int = int(os.environ.get("GEV_TARGET_PORT", "4173"))

# Timeouts per operation (seconds)
TIMEOUTS: dict[str, int] = {
    "start": 120,
    "stop": 60,
    "restart": 60,
    "status": 15,
    "logs": 15,
}

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [gev-controller] %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("gev-controller")

# ── Secret redaction ─────────────────────────────────────────────────────────

_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)\b\s*[:=]\s*([^\s,;]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")


def _redact(text: str) -> str:
    """Redact API keys, tokens, passwords and Bearer tokens from output."""
    if not text:
        return ""
    redacted = _SECRET_PATTERN.sub(r"\1=***", text)
    redacted = _BEARER_PATTERN.sub("Bearer ***", redacted)
    return redacted


# ── Docker helpers ───────────────────────────────────────────────────────────

def _compose_base() -> list[str]:
    """Return the base docker compose argv."""
    return ["docker", "compose", "-f", str(COMPOSE_FILE)]


def _run_compose(args: list[str], timeout: int) -> tuple[bool, str]:
    """Run a docker compose command with fixed argv — never shell=True."""
    argv = _compose_base() + args
    logger.info("exec: %s (timeout=%ds)", " ".join(argv), timeout)
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            timeout=timeout,
            cwd="/project",
        )
        stdout = result.stdout.decode(errors="replace").strip()
        stderr = result.stderr.decode(errors="replace").strip()
        combined = f"{stdout}\n{stderr}".strip()
        return result.returncode == 0, _redact(combined)
    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout}s) exceeded"
    except Exception as exc:
        return False, _redact(f"Execution error: {exc}")


# ── TCP health probe ────────────────────────────────────────────────────────

def _tcp_probe(host: str, port: int, timeout: float = 2.0) -> bool:
    """Return True if a TCP connection to host:port succeeds."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


# ── HTTP Handler ─────────────────────────────────────────────────────────────

class ControllerHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP handler for GEV lifecycle operations."""

    # Suppress default stderr logging from BaseHTTPRequestHandler
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        logger.info(format, *args)

    # ── Auth ─────────────────────────────────────────────────────────────

    def _check_auth(self) -> bool:
        """Validate Bearer token.  Fail-closed if no token configured."""
        if not AUTH_TOKEN:
            self._json_response(403, {"ok": False, "error": "No controller token configured (fail-closed)"})
            return False

        auth_header = self.headers.get("Authorization", "")
        expected = f"Bearer {AUTH_TOKEN}"
        if auth_header != expected:
            logger.warning("auth failure from %s", self.client_address[0])
            self._json_response(401, {"ok": False, "error": "Unauthorized"})
            return False
        return True

    # ── Response helpers ─────────────────────────────────────────────────

    def _json_response(self, status: int, body: dict) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _not_found(self) -> None:
        self._json_response(404, {"ok": False, "error": "Not found"})

    def _method_not_allowed(self) -> None:
        self._json_response(405, {"ok": False, "error": "Method not allowed"})

    # ── GET routes ───────────────────────────────────────────────────────

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/health":
            self._handle_health()
        elif path == "/status":
            if not self._check_auth():
                return
            self._handle_status()
        elif path == "/logs":
            if not self._check_auth():
                return
            self._handle_logs(parsed.query)
        else:
            self._not_found()

    # ── POST routes ──────────────────────────────────────────────────────

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if not self._check_auth():
            return

        if path == "/start":
            self._handle_start()
        elif path == "/stop":
            self._handle_stop()
        elif path == "/restart":
            self._handle_restart()
        else:
            self._not_found()

    # ── Catch-all for unsupported methods ────────────────────────────────

    def do_PUT(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802
        self._method_not_allowed()

    # ── Handlers ─────────────────────────────────────────────────────────

    def _handle_health(self) -> None:
        reachable = _tcp_probe(TARGET_HOST, TARGET_PORT)
        status_code = 200 if reachable else 503
        self._json_response(status_code, {
            "ok": reachable,
            "target_host": TARGET_HOST,
            "target_port": TARGET_PORT,
            "reachable": reachable,
        })

    def _handle_status(self) -> None:
        ok, output = _run_compose(["ps", "--format", "json"], TIMEOUTS["status"])
        self._json_response(200, {"ok": ok, "output": output})

    def _handle_start(self) -> None:
        ok, output = _run_compose(["up", "-d"], TIMEOUTS["start"])
        status_code = 200 if ok else 500
        self._json_response(status_code, {"ok": ok, "output": output})

    def _handle_stop(self) -> None:
        ok, output = _run_compose(["stop"], TIMEOUTS["stop"])
        status_code = 200 if ok else 500
        self._json_response(status_code, {"ok": ok, "output": output})

    def _handle_restart(self) -> None:
        ok, output = _run_compose(["restart"], TIMEOUTS["restart"])
        status_code = 200 if ok else 500
        self._json_response(status_code, {"ok": ok, "output": output})

    def _handle_logs(self, query_string: str) -> None:
        params = parse_qs(query_string)
        tail_raw = params.get("tail", ["100"])[0]
        try:
            tail = int(tail_raw)
        except (ValueError, TypeError):
            tail = 100
        # Clamp 1-500
        tail = max(1, min(tail, 500))

        ok, output = _run_compose(
            ["logs", f"--tail={tail}", "--no-color"],
            TIMEOUTS["logs"],
        )
        self._json_response(200, {"ok": ok, "output": output})


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    # Startup validation
    if not AUTH_TOKEN:
        logger.critical(
            "GEV_CONTROLLER_TOKEN is not set — ALL requests will be denied (fail-closed)"
        )

    if not COMPOSE_FILE.is_file():
        logger.warning("compose file not found at %s — commands will fail", COMPOSE_FILE)
    else:
        logger.info("compose file: %s", COMPOSE_FILE)

    logger.info(
        "health target: %s:%d", TARGET_HOST, TARGET_PORT
    )

    server = http.server.HTTPServer(
        (LISTEN_HOST, LISTEN_PORT), ControllerHandler
    )
    logger.info("listening on %s:%d", LISTEN_HOST, LISTEN_PORT)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
