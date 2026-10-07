"""Tests du TerminalService Core — PTY réel, pas de simulation.

Matrice : création, E/S stdin/stdout/stderr, Ctrl+C, resize, terminaison,
reconnexion, sessions multiples, nettoyage, fuite de processus, timeout de
lecture et sécurité (root refusé, secrets filtrés, cwd borné).

Ces tests forkent de VRAIS processus (`/bin/sh`) : le comportement à prouver
(ligne discipline, groupe de signaux, ioctl) est exactement ce qu'un mock ne
peut pas garantir.
"""

from __future__ import annotations

import os
import time

import pytest
from core.terminal import (
    TerminalError,
    TerminalNotFound,
    TerminalSecurityError,
    TerminalService,
    TerminalState,
    build_clean_env,
    resolve_cwd,
)


def _alive(pid: int) -> bool:
    """Le PID existe-t-il encore (hors zombie) ?"""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
            return handle.read().split(") ", 1)[1].split(" ", 1)[0] != "Z"
    except OSError:
        return True


@pytest.fixture
def service(tmp_path):
    """Service Core avec shell `/bin/sh` et racine isolée (tmp_path)."""
    svc = TerminalService(shell="/bin/sh", root=str(tmp_path))
    yield svc
    svc.shutdown_all()  # teardown : aucun processus ne survit au test


@pytest.fixture(autouse=True)
def _no_root():
    """Le service refuse root par design : les tests tournent en non-root."""
    if os.geteuid() == 0:
        pytest.skip("terminal : root interdit par design")


def _drain(svc: TerminalService, session_id: str, needle: bytes, timeout: float = 5.0) -> bytes:
    """Lit le PTY jusqu'à trouver `needle`."""
    buffer = b""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        chunk = svc.read(session_id, timeout=0.2)
        if chunk:
            buffer += chunk
            if needle in buffer:
                return buffer
        time.sleep(0.02)
    return buffer


# ── Création ──────────────────────────────────────────────────────────────────


class TestCreate:
    def test_create_session_exposes_core_state(self, service):
        session = service.create(user="alice")
        assert session.state == TerminalState.RUNNING
        assert session.user == "alice"
        assert session.pid > 0
        assert session.cwd.startswith(service._root)
        assert session.id.startswith("term_")
        # Le descripteur ne fuit JAMAIS dans la vue destinée aux interfaces.
        assert "fd" not in session.to_dict()

    def test_created_session_runs_a_real_shell(self, service):
        session = service.create(user="alice")
        service.write(session.id, "echo READY_MARKER\n")
        assert b"READY_MARKER" in _drain(service, session.id, b"READY_MARKER")

    def test_two_sessions_are_independent(self, service):
        first = service.create(user="alice")
        second = service.create(user="bob")
        assert first.id != second.id
        assert first.pid != second.pid

        service.write(first.id, "echo FIRST_ONLY\n")
        assert b"FIRST_ONLY" in _drain(service, first.id, b"FIRST_ONLY")

        service.write(second.id, "echo SECOND_ONLY\n")
        output = _drain(service, second.id, b"SECOND_ONLY")
        assert b"SECOND_ONLY" in output
        assert b"FIRST_ONLY" not in output

    def test_unknown_session_is_not_found(self, service):
        with pytest.raises(TerminalNotFound):
            service.get("term_inexistant")


# ── E/S, Ctrl+C, resize ───────────────────────────────────────────────────────


class TestIo:
    def test_stdin_and_stdout_roundtrip(self, service):
        session = service.create(user="alice")
        service.write(session.id, "echo TRIP\n")
        assert b"TRIP" in _drain(service, session.id, b"TRIP")

    def test_stderr_is_streamed_in_the_same_pty(self, service):
        session = service.create(user="alice")
        # Un PTY fusionne stderr comme un vrai terminal : rien n'est perdu.
        service.write(session.id, "echo ERRLINE 1>&2\n")
        assert b"ERRLINE" in _drain(service, session.id, b"ERRLINE")

    def test_ansi_sequences_are_preserved(self, service):
        session = service.create(user="alice")
        service.write(session.id, "printf '\\033[32mANSI_OK\\033[0m\\n'\n")
        # On attend la séquence ESC elle-même : l'echo de la commande contient
        # déjà « ANSI_OK » mais pas les codes couleur.
        decoded = _drain(service, session.id, b"\x1b[32m").decode(errors="replace")
        assert "\033[32m" in decoded

    def test_ctrl_c_interrupts_the_foreground_process(self, service):
        session = service.create(user="alice")
        service.write(session.id, "sleep 30\n")
        time.sleep(0.3)
        assert _alive(session.pid)

        service.interrupt(session.id)

        # Le shell survit au SIGINT (c'est `sleep` qui meurt, pas le terminal).
        service.write(session.id, "echo STILL_ALIVE\n")
        assert b"STILL_ALIVE" in _drain(service, session.id, b"STILL_ALIVE")

    def test_resize_changes_the_pty_window(self, service):
        session = service.create(user="alice")
        service.resize(session.id, cols=132, rows=43)
        assert session.cols == 132
        assert session.rows == 43

        # Preuve réelle : le shell voit la nouvelle taille (ioctl effectif).
        service.write(session.id, "stty size\n")
        assert b"43 132" in _drain(service, session.id, b"43 132")

    def test_write_on_closed_session_is_refused(self, service):
        session = service.create(user="alice")
        service.terminate(session.id)
        with pytest.raises(TerminalNotFound):
            service.write(session.id, "echo x\n")

    def test_read_is_bounded_and_returns_empty_when_idle(self, service):
        session = service.create(user="alice")
        _drain(service, session.id, b"$", timeout=2.0)  # vide le prompt initial

        started = time.monotonic()
        assert service.read(session.id, timeout=0.05) == b""
        assert time.monotonic() - started < 2.0


# ── Terminaison, nettoyage, fuite de processus ─────────────────────────────────


class TestLifecycle:
    def test_terminate_closes_session_and_kills_process(self, service):
        session = service.create(user="alice")
        pid = session.pid

        closed = service.terminate(session.id)
        assert closed.state == TerminalState.CLOSED
        assert not _alive(pid)
        assert service.list_sessions() == []

    def test_close_releases_the_file_descriptor(self, service):
        session = service.create(user="alice")
        fd = session.fd
        assert fd is not None
        service.terminate(session.id)
        assert session.fd is None
        with pytest.raises(OSError):
            os.write(fd, b"x")

    def test_exited_session_is_purged_not_leaked(self, service):
        session = service.create(user="alice")
        service.write(session.id, "exit 3\n")
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and service.list_sessions():
            time.sleep(0.1)
        assert service.list_sessions() == []

    def test_shutdown_all_kills_every_session(self, service):
        sessions = [service.create(user="alice") for _ in range(3)]
        pids = [s.pid for s in sessions]

        service.shutdown_all()

        assert service.list_sessions() == []
        for pid in pids:
            assert not _alive(pid)

    def test_api_restart_leaves_no_orphan(self, tmp_path):
        # Nouvelle instance de service = API redémarrée : registre vide et
        # aucun processus du service précédent ne doit subsister.
        first = TerminalService(shell="/bin/sh", root=str(tmp_path))
        session = first.create(user="alice")
        pid = session.pid

        second = TerminalService(shell="/bin/sh", root=str(tmp_path))
        assert second.list_sessions() == []
        with pytest.raises(TerminalNotFound):
            second.get(session.id)

        # Le restart s'accompagne du nettoyage explicite de l'ancien service.
        first.shutdown_all()
        assert not _alive(pid)

    def test_reconnect_reattaches_to_the_running_session(self, service):
        session = service.create(user="alice")
        service.write(session.id, "echo BEFORE\n")
        assert b"BEFORE" in _drain(service, session.id, b"BEFORE")

        # Déconnexion puis retour du client : la session vit toujours.
        again = service.get(session.id)
        assert again.state == TerminalState.RUNNING
        service.write(again.id, "echo AFTER\n")
        assert b"AFTER" in _drain(service, again.id, b"AFTER")

    def test_terminate_kills_a_shell_that_ignores_sigterm(self, service):
        session = service.create(user="alice")
        service.write(session.id, "trap '' TERM\n")
        time.sleep(0.3)

        service.terminate(session.id)  # doit finir en SIGKILL

        assert not _alive(session.pid)
        assert service.list_sessions() == []


# ── Sécurité ──────────────────────────────────────────────────────────────────


class TestSecurity:
    def test_root_session_is_refused(self, service, monkeypatch):
        monkeypatch.setattr(os, "geteuid", lambda: 0)
        with pytest.raises(TerminalSecurityError):
            service.create(user="root")

    def test_environment_never_carries_secrets(self, monkeypatch):
        monkeypatch.setenv("ETHAN_TOKEN", "super-secret")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-should-never-leak")
        monkeypatch.setenv("DB_PASSWORD", "hunter2")
        monkeypatch.setenv("MY_JWT_SECRET", "nope")
        monkeypatch.setenv("SAFE_VAR", "kept")

        env = build_clean_env({"HOME": "/workspace", "SAFE_VAR": "kept"})

        assert "ETHAN_TOKEN" not in env
        assert "OPENAI_API_KEY" not in env
        assert "DB_PASSWORD" not in env
        assert "MY_JWT_SECRET" not in env
        # L'environnement est une ALLOWLIST : rien du parent n'est hérité par
        # défaut, seules les variables explicitement demandées entrent.
        assert env["SAFE_VAR"] == "kept"
        assert env["HOME"] == "/workspace"

    def test_session_does_not_see_the_parent_token(self, service, monkeypatch):
        monkeypatch.setenv("ETHAN_TOKEN", "leak-me-not")
        session = service.create(user="alice")
        service.write(session.id, "echo TOKEN=[$ETHAN_TOKEN]\n")
        output = _drain(service, session.id, b"TOKEN=")
        assert b"leak-me-not" not in output

    def test_cwd_is_bounded_to_the_root(self, service):
        # Un cwd qui tente de s'échapper retombe sur la racine : fail-closed.
        assert resolve_cwd("../../etc", service._root) == service._root

        session = service.create(user="alice", cwd="../../../etc")
        assert session.cwd == service._root

    def test_cwd_inside_root_is_honoured(self, service):
        target = os.path.join(service._root, "subdir")
        os.makedirs(target, exist_ok=True)
        session = service.create(user="alice", cwd="subdir")
        assert session.cwd.endswith("subdir")

    def test_resize_bounds_are_enforced(self, service):
        session = service.create(user="alice")
        service.resize(session.id, cols=99999, rows=-5)
        assert session.cols <= 500
        assert session.rows >= 1

    def test_session_view_exposes_no_internal_fields(self, service):
        payload = service.create(user="alice").to_dict()
        for forbidden in ("fd", "task", "deadline"):
            assert forbidden not in payload
        assert set(payload) == {
            "id",
            "user",
            "cwd",
            "state",
            "pid",
            "exit_code",
            "created_at",
            "last_activity",
            "cols",
            "rows",
            "hostname",
            "permission",
        }


# ── Erreurs ───────────────────────────────────────────────────────────────────


class TestErrors:
    def test_errors_carry_stable_codes(self):
        assert TerminalNotFound("x").code == "TERMINAL-NOTFOUND"
        assert TerminalSecurityError("x").code == "TERMINAL-SEC"
        assert TerminalError("x", code="TERMINAL-CLOSED").code == "TERMINAL-CLOSED"

    def test_terminate_unknown_session_raises(self, service):
        with pytest.raises(TerminalNotFound):
            service.terminate("term_ghost")
