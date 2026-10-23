"""Tests — service Odin confine (etats, erreurs, confinement)."""

import asyncio
from datetime import datetime, timezone

from pathlib import Path

import pytest
from core.plugins import odin as mod
from core.plugins.odin import (
    STATE_ACTIVE,
    STATE_ERROR,
    STATE_STARTING,
    STATE_STOPPED,
    STATE_NOT_INSTALLED,
    STATE_UNKNOWN,
    STATE_DEGRADED,
    STATE_STOPPING,
    OdinService,
    get_odin_service,
)


def _service(**kw) -> OdinService:
    svc = OdinService.__new__(OdinService)
    default_repo = Path(__file__).resolve().parents[2] / "examples" / "odin"
    svc._repo_dir = Path(kw.get("repo_dir", default_repo))
    svc._compose_file = Path(kw.get("compose_file", svc._repo_dir / "compose.yaml"))
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
    assert payload["allowed_actions"] == ["start", "uninstall"]
    assert payload["healthy"] is False


def test_status_dict_active_allows_stop_restart_open():
    svc = _service(state=STATE_ACTIVE)
    payload = svc._build_status_dict(state=STATE_ACTIVE, healthy=True)
    assert payload["allowed_actions"] == ["stop", "restart", "uninstall", "open"]


def test_status_dict_error_allows_recovery():
    svc = _service(state=STATE_ERROR, error="boom")
    payload = svc._build_status_dict(state=STATE_ERROR, healthy=False, error="boom")
    assert payload["allowed_actions"] == ["install", "start", "restart", "uninstall"]
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
    ok, _ = await svc._run_docker(["ps", "--all", "--format", "json"])
    assert ok is True
    with pytest.raises(ValueError):
        await svc._run_docker(["down", "-v"])


def test_health_probe_uses_private_controller_when_configured(monkeypatch):
    svc = _service()
    svc._controller_url = "http://odin-controller:8765"
    svc._controller_token = "test-only"
    calls = []

    def fake_request(path, args=None, timeout=10.0):
        calls.append((path, args))
        return {"ok": True}

    monkeypatch.setattr(svc, "_controller_request", fake_request)
    assert svc.check_health() is True
    assert calls == [("/run", ["probe"])]


@pytest.mark.asyncio
async def test_status_distinguishes_absent_stopped_running_and_unhealthy(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)
    monkeypatch.setattr(svc, "check_health", lambda: False)
    async def absent():
        return None
    monkeypatch.setattr(svc, "_inspect_container", absent)
    assert (await svc.get_status())["status"] == STATE_NOT_INSTALLED

    async def stopped():
        return {"State": "exited", "Name": "odin-1"}
    monkeypatch.setattr(svc, "_inspect_container", stopped)
    assert (await svc.get_status())["status"] == STATE_STOPPED

    async def running():
        return {"State": "running", "Name": "odin-1"}
    monkeypatch.setattr(svc, "_inspect_container", running)
    assert (await svc.get_status())["status"] == STATE_DEGRADED


@pytest.mark.asyncio
async def test_docker_unavailable_is_unknown_not_uninstalled(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    async def unavailable():
        raise RuntimeError("Docker daemon unavailable")
    monkeypatch.setattr(svc, "_inspect_container", unavailable)
    result = await svc.get_status()
    assert result["status"] == STATE_UNKNOWN
    assert "Docker daemon unavailable" in result["error"]


@pytest.mark.asyncio
async def test_failed_container_is_recoverable_and_offers_retry_and_uninstall(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    async def failed():
        return {"State": "exited", "ExitCode": 1, "Name": "odin-1"}
    monkeypatch.setattr(svc, "_inspect_container", failed)
    result = await svc.get_status()
    assert result["status"] == STATE_ERROR
    assert {"install", "uninstall"}.issubset(result["allowed_actions"])


def test_confinement_rejects_foreign_path(tmp_path):
    foreign = tmp_path / "evil"
    foreign.mkdir()
    (foreign / "compose.yaml").write_text("x")
    with pytest.raises(ValueError):
        OdinService(repo_dir=foreign)


def test_singleton_settable():
    svc = _service()
    mod.set_odin_service(svc)
    try:
        assert mod.get_odin_service() is svc
        assert get_odin_service() is svc
    finally:
        mod.set_odin_service(None)
