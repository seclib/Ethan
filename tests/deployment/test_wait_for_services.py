"""Tests pour ``scripts/cmd-wait-for-services.sh`` (Phase 2.1 du plan Boot).

Régression couverte : l'ancien parsing ``entry%%:*``/``entry##*:`` cassait
les checks HTTP (``http://...`` était silencieusement ignoré, ``CHECK`` valant
``http``) et perdait le port des checks ``tcp:PORT``. Le check Docker utilisait
``docker compose ps --filter health=healthy`` — filtre inexistant (« unknown
filter health ») qui rendait ``make bootstrap`` systématiquement en timeout.

Les tests purs (sans stack) utilisent un serveur HTTP / une socket locale
éphémère. Le test Docker d'intégration est ignoré si la stack n'est pas prête.
"""

from __future__ import annotations

import http.server
import socket
import subprocess
import threading
from contextlib import closing, contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "cmd-wait-for-services.sh"


# ── Helpers ────────────────────────────────────────────────────────────────


def _run_wait(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Exécute le script wait-for-services et capture sa sortie."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _free_port() -> int:
    """Retourne un port TCP local libre (fermé immédiatement après)."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def _http_server():
    """Mini serveur HTTP répondant 200 sur toutes les routes."""

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 — API http.server
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):  # silencieux dans les tests
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextmanager
def _tcp_listener():
    """Socket TCP en écoute (accept en arrière-plan, jamais fermé)."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)
    try:
        yield listener.getsockname()[1]
    finally:
        listener.close()


# ── Contrat du script ──────────────────────────────────────────────────────


class TestScriptContract:
    """Contrat de base : présence, syntaxe et exit codes documentés."""

    def test_script_exists_and_executable(self):
        assert SCRIPT.is_file(), f"{SCRIPT} manquant"
        assert SCRIPT.stat().st_mode & 0o111, "le script doit être exécutable"

    def test_bash_syntax_valid(self):
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, result.stderr

    def test_help_exits_0(self):
        result = _run_wait("--help")
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_unknown_check_alone_exits_2(self):
        """Un check non reconnu seul → exit 2 (aucun faux « tout est prêt »)."""
        result = _run_wait("foo-bar-baz")
        assert result.returncode == 2
        combined = result.stdout + result.stderr
        assert "Aucun check valide" in combined

    def test_unknown_check_ignored_when_valid_present(self):
        """Un check inconnu est ignoré (warn) si un check valide réussit."""
        with _tcp_listener() as port:
            result = _run_wait("--timeout", "10", "ghost:xyz", f"tcp:{port}")
        assert result.returncode == 0
        assert "non reconnu" in result.stdout or "non reconnu" in result.stderr


# ── Checks HTTP ────────────────────────────────────────────────────────────


class TestHttpCheck:
    """Le check ``http://URL`` (auparavant silencieusement ignoré)."""

    def test_http_check_success(self):
        with _http_server() as port:
            result = _run_wait("--timeout", "10", f"http://127.0.0.1:{port}/health")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "ready" in result.stdout

    def test_http_check_timeout_on_closed_port(self):
        port = _free_port()
        result = _run_wait("--timeout", "3", "--interval", "1", f"http://127.0.0.1:{port}/")
        assert result.returncode == 1
        assert "Timeout" in result.stdout + result.stderr


# ── Checks TCP ─────────────────────────────────────────────────────────────


class TestTcpCheck:
    """Le check ``tcp:PORT`` (port auparavant perdu par le parsing)."""

    def test_tcp_check_success(self):
        with _tcp_listener() as port:
            result = _run_wait("--timeout", "10", f"tcp:{port}")
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"tcp:{port} ready" in result.stdout

    def test_tcp_check_timeout_on_closed_port(self):
        port = _free_port()
        result = _run_wait("--timeout", "3", "--interval", "1", f"tcp:{port}")
        assert result.returncode == 1
        assert f"tcp:{port}" in result.stdout


# ── Check Docker (intégration, ignoré sans stack) ─────────────────────────


def _docker_stack_ready() -> bool:
    """True si le conteneur Compose ``nats`` tourne (stack ETHAN démarrée)."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "nats", "--format", "json"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return '"State":"running"' in result.stdout


requires_docker_stack = pytest.mark.skipif(
    not _docker_stack_ready(),
    reason="Stack Docker ETHAN non démarrée (docker compose ps nats vide)",
)


class TestDockerCheck:
    """Le check ``docker:SERVICE`` (filtre ``health=healthy`` inexistant avant)."""

    @requires_docker_stack
    def test_docker_check_success_on_running_service(self):
        result = _run_wait("--timeout", "15", "docker:nats")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "docker:nats ready" in result.stdout

    @requires_docker_stack
    def test_docker_check_timeout_on_ghost_service(self):
        """Un service inexistant ne doit jamais être considéré prêt."""
        result = _run_wait("--timeout", "3", "--interval", "1", "docker:ghost-service-xyz")
        assert result.returncode == 1
        assert "docker:ghost-service-xyz" in result.stdout
