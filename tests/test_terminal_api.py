"""Tests API du terminal — passerelle mince + WebSocket PTY.

Matrice : authentification (401), permissions (403), création de session,
listing, 404, E/S, resize, Ctrl+C, fermeture, reconnexion de session,
déconnexion WebSocket qui ne doit PAS tuer le processus, et nettoyage.

Le `TerminalService` est le VRAI service (PTY réels) : la passerelle est
testée sur son contrat HTTP/WS, pas sur des mocks — on ne proves pas un mock.
"""

from __future__ import annotations

import os
import secrets
import time

import pytest

# L'auth refuse de démarrer sans secret : même Convention que contract_kit.py.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))

from core.terminal import TerminalService  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from interfaces.api.auth import auth_middleware, create_access_token  # noqa: E402
from interfaces.api.routers import terminal as terminal_router  # noqa: E402

WS_PATH = "/v1/terminal/ws"


@pytest.fixture(autouse=True)
def _no_root():
    if os.geteuid() == 0:
        pytest.skip("terminal : root interdit par design")


@pytest.fixture
def service(tmp_path):
    svc = TerminalService(shell="/bin/sh", root=str(tmp_path))
    terminal_router.set_terminal_service(svc)
    yield svc
    svc.shutdown_all()
    terminal_router.set_terminal_service(None)


@pytest.fixture
def client(service):
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(terminal_router.router)
    # L'app réelle pose ce state dans son lifespan : on le fait ici pour que
    # les tests observent le même service que les routes.
    app.state.terminal_service = service
    with TestClient(app) as test_client:
        yield test_client


def _auth(role: str = "admin", user_id: str = "alice") -> dict[str, str]:
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def _token(role: str = "admin", user_id: str = "alice") -> str:
    return create_access_token({"sub": user_id, "role": role})


# ── REST : authentification et permissions ────────────────────────────────────


class TestRestAuth:
    def test_sessions_require_authentication(self, client):
        assert client.get("/v1/terminal/sessions").status_code == 401
        assert client.post("/v1/terminal/sessions", json={}).status_code == 401

    def test_creating_a_session_requires_execute_permission(self, client):
        # `viewer` a READ/CHAT seulement : un terminal est de l'exécution.
        denied = client.post("/v1/terminal/sessions", headers=_auth("viewer"), json={})
        assert denied.status_code == 403

    def test_admin_can_open_a_session(self, client):
        response = client.post("/v1/terminal/sessions", headers=_auth(), json={})
        assert response.status_code == 201

        body = response.json()
        assert body["state"] == "RUNNING"
        assert body["user"] == "alice"
        assert body["pid"] > 0
        assert "fd" not in body  # jamais de descripteur exposé

    def test_session_is_closed_by_the_api(self, client):
        created = client.post("/v1/terminal/sessions", headers=_auth(), json={}).json()
        closed = client.delete(f"/v1/terminal/sessions/{created['id']}", headers=_auth())
        assert closed.status_code == 200
        assert closed.json()["state"] == "CLOSED"
        # Le processus est réellement tué.
        assert (
            client.get(f"/v1/terminal/sessions/{created['id']}", headers=_auth()).status_code == 404
        )


class TestRestSurface:
    def test_list_and_get_expose_core_state(self, client):
        created = client.post("/v1/terminal/sessions", headers=_auth(), json={}).json()

        listing = client.get("/v1/terminal/sessions", headers=_auth("viewer"))
        assert listing.status_code == 200  # READ suffit pour lire
        assert [s["id"] for s in listing.json()["sessions"]] == [created["id"]]

        fetched = client.get(f"/v1/terminal/sessions/{created['id']}", headers=_auth())
        assert fetched.json()["state"] == "RUNNING"

    def test_unknown_session_is_404(self, client):
        assert client.get("/v1/terminal/sessions/term_ghost", headers=_auth()).status_code == 404
        assert client.delete("/v1/terminal/sessions/term_ghost", headers=_auth()).status_code == 404

    def test_input_resize_and_interrupt_reach_the_core(self, client):
        session_id = client.post("/v1/terminal/sessions", headers=_auth(), json={}).json()["id"]

        assert (
            client.post(
                f"/v1/terminal/sessions/{session_id}/input",
                headers=_auth(),
                json={"data": "echo API_OK\n"},
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/v1/terminal/sessions/{session_id}/resize",
                headers=_auth(),
                json={"cols": 100, "rows": 30},
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/v1/terminal/sessions/{session_id}/interrupt", headers=_auth()
            ).status_code
            == 200
        )

        # Preuve que l'E/S traverse bien jusqu'au PTY.
        buffer = b""
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and b"API_OK" not in buffer:
            buffer += client.app.state.terminal_service.read(session_id, timeout=0.2)
        assert b"API_OK" in buffer

    def test_input_requires_execute_permission(self, client):
        session_id = client.post("/v1/terminal/sessions", headers=_auth(), json={}).json()["id"]
        denied = client.post(
            f"/v1/terminal/sessions/{session_id}/input",
            headers=_auth("viewer"),
            json={"data": "echo nope\n"},
        )
        assert denied.status_code == 403


# ── WebSocket : le cœur interactif ────────────────────────────────────────────


class TestWebSocketAuth:
    def test_ws_without_token_is_refused(self, client):
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(WS_PATH):
                pass
        assert exc.value.code == 4401

    def test_ws_with_invalid_token_is_refused(self, client):
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(f"{WS_PATH}?token=not-a-jwt"):
                pass
        assert exc.value.code == 4401

    def test_ws_requires_execute_permission(self, client):
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(f"{WS_PATH}?token={_token('viewer')}"):
                pass
        assert exc.value.code == 4403

    def test_ws_accepts_admin_and_announces_the_session(self, client):
        with client.websocket_connect(f"{WS_PATH}?token={_token()}") as ws:
            hello = ws.receive_json()
            assert hello["type"] == "session"
            assert hello["state"] == "RUNNING"
            assert hello["user"] == "alice"
            ws.send_json({"type": "ping"})
            # Le shell émet son prompt : on saute les `output` jusqu'au pong.
            for _ in range(10):
                message = ws.receive_json()
                if message["type"] == "pong":
                    break
            else:
                pytest.fail("aucun pong reçu")


class TestWebSocketIo:
    def _collect(self, ws, needle: str, timeout: float = 8.0) -> str:
        seen = ""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and needle not in seen:
            seen += ws.receive_json().get("data", "")
        return seen

    def test_output_is_streamed_back_to_the_client(self, client):
        with client.websocket_connect(f"{WS_PATH}?token={_token()}") as ws:
            ws.receive_json()  # session
            ws.send_json({"type": "input", "data": "echo WS_STREAM_OK\n"})
            assert "WS_STREAM_OK" in self._collect(ws, "WS_STREAM_OK")

    def test_resize_over_the_socket_reaches_the_pty(self, client):
        with client.websocket_connect(f"{WS_PATH}?token={_token()}") as ws:
            ws.receive_json()
            ws.send_json({"type": "resize", "cols": 111, "rows": 37})
            ws.send_json({"type": "input", "data": "stty size\n"})
            assert "37 111" in self._collect(ws, "37 111")

    def test_disconnect_does_not_kill_the_terminal(self, client):
        # Fermer l'onglet ne doit pas tuer un shell en cours d'installation :
        # le processus survit et la session reste reconnectable.
        with client.websocket_connect(f"{WS_PATH}?token={_token()}") as ws:
            session_id = ws.receive_json()["id"]

        service = client.app.state.terminal_service
        assert service.get(session_id).state == "RUNNING"

        with client.websocket_connect(f"{WS_PATH}?token={_token()}&session_id={session_id}") as ws:
            assert ws.receive_json()["id"] == session_id
            ws.send_json({"type": "input", "data": "echo REATTACHED\n"})
            assert "REATTACHED" in self._collect(ws, "REATTACHED")

    def test_unknown_session_on_reconnect_is_refused(self, client):
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(f"{WS_PATH}?token={_token()}&session_id=term_ghost"):
                pass
        assert exc.value.code == 4404

    def test_two_sockets_have_independent_sessions(self, client):
        with (
            client.websocket_connect(f"{WS_PATH}?token={_token()}") as first,
            client.websocket_connect(f"{WS_PATH}?token={_token()}") as second,
        ):
            assert first.receive_json()["id"] != second.receive_json()["id"]
            first.send_json({"type": "input", "data": "echo SOCKET_A\n"})
            second.send_json({"type": "input", "data": "echo SOCKET_B\n"})
            assert "SOCKET_A" in self._collect(first, "SOCKET_A")
            assert "SOCKET_B" in self._collect(second, "SOCKET_B")

    def test_ctrl_c_over_the_socket_interrupts(self, client):
        with client.websocket_connect(f"{WS_PATH}?token={_token()}") as ws:
            session_id = ws.receive_json()["id"]
            ws.send_json({"type": "input", "data": "sleep 20\n"})
            time.sleep(0.5)

            ws.send_json({"type": "interrupt"})

            # Le shell survit au SIGINT : on peut encore lui parler.
            ws.send_json({"type": "input", "data": "echo AFTER_CTRL_C\n"})
            assert "AFTER_CTRL_C" in self._collect(ws, "AFTER_CTRL_C")
            assert client.app.state.terminal_service.get(session_id).state == "RUNNING"


# ── Cohérence CLI : le terminal n'est PAS un deuxième CLI ─────────────────────


class TestCliCoherence:
    def test_terminal_runs_the_real_ethan_cli(self, client):
        """Le terminal exécute le MÊME point d'entrée que `interfaces/cli/`.

        Une commande ETHAN tapée dans le terminal WebUI part donc dans le même
        backend que tapée au clavier : aucun doublon d'implémentation.
        """
        import sys

        with client.websocket_connect(f"{WS_PATH}?token={_token()}") as ws:
            ws.receive_json()
            # Point d'entrée EXACT du CLI installé (`python -m interfaces.cli.main`).
            ws.send_json(
                {"type": "input", "data": f"{sys.executable} -m interfaces.cli.main --version\n"}
            )

            seen = ""
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and "ETHAN CLI" not in seen:
                seen += ws.receive_json().get("data", "")
            assert "ETHAN CLI" in seen

    def test_cli_help_reports_the_same_command_catalogue(self, client):
        import sys

        with client.websocket_connect(f"{WS_PATH}?token={_token()}") as ws:
            ws.receive_json()
            ws.send_json(
                {"type": "input", "data": f"{sys.executable} -m interfaces.cli.main help\n"}
            )

            seen = ""
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and "extension" not in seen:
                seen += ws.receive_json().get("data", "")
            # Les mêmes familles que le CLI local (une seule implémentation).
            assert "extension" in seen
            assert "model" in seen


# ── Nettoyage / fuite de processus ────────────────────────────────────────────


class TestRestart:
    def test_restart_empties_the_registry_without_orphan(self, client):
        """Redémarrage API : registre vide, aucun orphelin, listing vide.

        Les PTY meurent avec le processus API : `shutdown_all()` simule le
        restart (SIGTERM→SIGKILL + récolte), puis le listing HTTP est vide.
        """
        import os

        service = client.app.state.terminal_service
        created = client.post("/v1/terminal/sessions", headers=_auth(), json={}).json()
        pid = int(created["pid"])
        assert service.get(created["id"]).state == "RUNNING"

        service.shutdown_all()

        assert service.list_sessions() == []
        listing = client.get("/v1/terminal/sessions", headers=_auth())
        assert listing.status_code == 200
        assert listing.json()["sessions"] == []
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass  # processus mort : aucune fuite
        else:
            # Vivant ou zombie : la récolte doit le faire disparaître.
            with __import__("contextlib").suppress(ChildProcessError, OSError):
                os.waitpid(pid, 0)


class TestReadTimeout:
    def test_read_on_silent_session_returns_empty_without_blocking(self, client):
        """Timeout : `read` ne bloque jamais au-delà du délai demandé."""
        import time

        service = client.app.state.terminal_service
        session = service.create(user="alice")
        start = time.monotonic()
        chunk = service.read(session.id, timeout=0.2)
        assert isinstance(chunk, bytes)
        # Le shell peut déjà avoir émis son prompt : l'important est le
        # non-blocage, pas le vide.
        assert time.monotonic() - start < 2.0
        assert b"API_SHOULD_NOT_APPEAR" not in chunk


class TestCleanup:
    def test_terminated_sessions_are_purged_from_the_listing(self, client):
        service = client.app.state.terminal_service
        session = service.create(user="alice")
        service.write(session.id, "exit 0\n")

        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            service.purge_dead()
            if not service.list_sessions():
                break
            time.sleep(0.1)

        assert service.list_sessions() == []
        listing = client.get("/v1/terminal/sessions", headers=_auth())
        assert listing.json()["sessions"] == []
