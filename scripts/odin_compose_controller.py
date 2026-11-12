"""Narrow Docker Compose controller for the independently maintained Odin app.

This process is the only ETHAN container given the Docker socket. It accepts
only fixed operations for one fixed Compose project and never evaluates shell
input or caller-supplied paths.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from core.plugins.odin_compose_config import (
    ODIN_COMPOSE_FILE,
    ODIN_PROJECT_NAME,
    ODIN_REPO_DIR,
)

logger = logging.getLogger("odin-compose-controller")
TAIL_RE = re.compile(r"^[1-9][0-9]{0,2}$")
PROBE_JS = (
    "fetch('http://127.0.0.1:4173/', {signal: AbortSignal.timeout(2000)})"
    ".then(r => process.exit(r.status < 500 ? 0 : 1))"
    ".catch(() => process.exit(1))"
)


def project_paths(repo_dir: str | Path) -> tuple[Path, Path]:
    repo = Path(repo_dir).resolve(strict=False)
    expected_repo = ODIN_REPO_DIR.resolve()
    if repo != expected_repo:
        raise ValueError(f"Odin Compose path is outside the fixed project: {repo}")
    compose = ODIN_COMPOSE_FILE.resolve()
    return repo, compose


def project_available(repo_dir: str | Path) -> bool:
    repo, compose = project_paths(repo_dir)
    return repo.is_dir() and compose.is_file()


def command_for(args: list[str], repo_dir: str | Path) -> list[str]:
    """Map an approved request to a fixed argv; reject everything else."""
    repo, compose = project_paths(repo_dir)
    if args == ["ps", "--all", "--format", "json"]:
        operation = ["ps", "--all", "--format", "json"]
    elif args == ["config"]:
        # Quiet mode avoids returning interpolated secrets from the Compose file.
        operation = ["config", "--quiet"]
    elif args == ["up", "-d"]:
        operation = ["up", "-d"]
    elif args == ["stop"]:
        operation = ["stop"]
    elif args == ["restart"]:
        operation = ["restart"]
    elif args == ["down"]:
        operation = ["down"]  # deliberately no -v / --rmi / --remove-orphans
    elif len(args) == 3 and args[0] == "logs" and args[2] == "--no-color":
        tail = args[1].removeprefix("--tail=")
        if not TAIL_RE.fullmatch(tail) or int(tail) > 500:
            raise ValueError("tail must be an integer between 1 and 500")
        operation = ["logs", f"--tail={tail}", "--no-color"]
    elif args == ["probe"]:
        operation = ["exec", "-T", "odin", "node", "-e", PROBE_JS]
    else:
        raise ValueError("Docker Compose operation is not allowed")

    return [
        os.getenv("DOCKER_CLI", "docker"),
        "compose",
        "--project-name",
        ODIN_PROJECT_NAME,
        "-f",
        str(compose),
        *operation,
    ]


def redact(text: str) -> str:
    text = re.sub(
        r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)\b\s*[:=]\s*([^\s,;]+)",
        r"\1=***",
        text or "",
    )
    return re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer ***", text)


class ControllerHandler(BaseHTTPRequestHandler):
    server_version = "OdinComposeController/1"
    repo_dir = Path(os.getenv("ETHAN_ODIN_REPO_DIR", str(ODIN_REPO_DIR)))
    token = os.getenv("ETHAN_ODIN_CONTROLLER_TOKEN", "")

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info("controller request: " + fmt, *args)

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send(404, {"error": "not found"})
            return
        self._send(200, {"ok": True, "project_available": project_available(self.repo_dir)})

    def do_POST(self) -> None:
        if self.path != "/run":
            self._send(404, {"error": "not found"})
            return
        if not self.token or not hmac.compare_digest(
            self.headers.get("Authorization", ""), f"Bearer {self.token}"
        ):
            self._send(401, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 8192:
                raise ValueError("invalid request size")
            body = json.loads(self.rfile.read(length))
            args = body.get("args") if isinstance(body, dict) else None
            if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
                raise ValueError("args must be a string array")
            if not project_available(self.repo_dir):
                self._send(409, {"ok": False, "output": "Odin Compose project is unavailable"})
                return
            argv = command_for(args, self.repo_dir)
            if args == ["probe"]:
                timeout = 15
            elif args == ["up", "-d"]:
                timeout = 900
            elif args == ["config"]:
                timeout = 30
            elif args == ["ps", "--all", "--format", "json"]:
                timeout = 10
            elif args and args[0] == "logs":
                timeout = 15
            else:
                timeout = 60
            result = subprocess.run(
                argv,
                cwd=str(self.repo_dir.resolve()),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
            output = redact(
                "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
            )
            self._send(200, {"ok": result.returncode == 0, "output": output[-8000:]})
        except ValueError as exc:
            self._send(422, {"error": str(exc)})
        except subprocess.TimeoutExpired:
            self._send(504, {"ok": False, "output": "Docker Compose operation timed out"})
        except Exception as exc:  # noqa: BLE001 - return a bounded operational error
            logger.exception("Odin operation failed")
            self._send(500, {"ok": False, "output": redact(str(exc))[:1000]})


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    if not ControllerHandler.token:
        raise RuntimeError("ETHAN_ODIN_CONTROLLER_TOKEN is required")
    if Path(ControllerHandler.repo_dir).resolve() != ODIN_REPO_DIR.resolve():
        raise RuntimeError("ETHAN_ODIN_REPO_DIR must point to the fixed Odin checkout")
    port = int(os.getenv("ETHAN_ODIN_CONTROLLER_PORT", "8765"))
    server = ThreadingHTTPServer(("0.0.0.0", port), ControllerHandler)
    logger.info("Odin Compose controller listening on internal port %s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
