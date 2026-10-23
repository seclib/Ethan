"""Tests — God's Eye View service confine (etats, erreurs, confinement)."""

import asyncio
from datetime import datetime, timezone

import pytest
from core.plugins import gods_eye_view as mod
from core.plugins.gods_eye_view import (
    STATE_ACTIVE,
    STATE_ERROR,
    STATE_STARTING,
    STATE_STOPPED,
    STATE_STOPPING,
    GodsEyeViewService,
    get_gods_eye_view_service,
)


def _service(**kw) -> GodsEyeViewService:
    svc = GodsEyeViewService.__new__(GodsEyeViewService)
    svc._repo_dir = kw.get("repo_dir", "/tmp/gev")
    svc._compose_file = kw.get("compose_file", "/tmp/gev/compose.yaml")
    svc._port = kw.get("port", 4173)
    svc._host = kw.get("host", "127.0.0.1")
    svc._docker_cmd = "docker"
    svc._lock = asyncio.Lock()
    svc._state = kw.get("state", STATE_STOPPED)
    svc._last_error = kw.get("error")
    svc._last_updated = datetime.now(timezone.utc).isoformat()
    svc._cached_container_id = kw.get("container_id")
    return svc


def test_status_dict_stopped_allows_start():
    svc = _service(state=STATE_STOPPED)
    payload = svc._build_status_dict(state=STATE_STOPPED, healthy=False)
    assert payload["status"] == STATE_STOPPED
    assert payload["allowed_actions"] == ["start"]
    assert payload["healthy"] is False


def test_status_dict_active_allows_stop_restart_open():
    svc = _service(state=STATE_ACTIVE)
    payload = svc._build_status_dict(state=STATE_ACTIVE, healthy=True)
    assert payload["allowed_actions"] == ["stop", "restart", "open"]


def test_status_dict_error_allows_recovery():
    svc = _service(state=STATE_ERROR, error="boom")
    payload = svc._build_status_dict(state=STATE_ERROR, healthy=False, error="boom")
    assert payload["allowed_actions"] == ["start", "restart"]
    assert payload["error"] == "boom"


def test_transient_states_forbid_actions():
    svc = _service()
    starting = svc._build_status_dict(state=STATE_STARTING, healthy=False)
    assert starting["allowed_actions"] == []
    stopping = svc._build_status_dict(state=STATE_STOPPING, healthy=False)
    assert stopping["allowed_actions"] == []


@pytest.mark.asyncio
async def test_run_docker_rejects_arbitrary_command():
    svc = _service()
    with pytest.raises(ValueError):
        await svc._run_docker(["exec", "x"])


@pytest.mark.asyncio
async def test_run_docker_allows_frozen_verbs(monkeypatch: pytest.MonkeyPatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)

    class _Proc:
        returncode = 0

        async def communicate(self):
            return b"out", b""

    async def _fake_exec(*args, **kwargs):
        return _Proc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    ok, _ = await svc._run_docker(["ps", "--format", "json"])
    assert ok is True


def test_confinement_rejects_foreign_path(tmp_path):
    foreign = tmp_path / "evil"
    foreign.mkdir()
    (foreign / "compose.yaml").write_text("x")
    with pytest.raises(ValueError):
        GodsEyeViewService(repo_dir=foreign)


def test_singleton_settable():
    svc = _service()
    mod.set_gods_eye_view_service(svc)
    try:
        assert mod.get_gods_eye_view_service() is svc
        assert get_gods_eye_view_service() is svc
    finally:
        mod.set_gods_eye_view_service(None)


