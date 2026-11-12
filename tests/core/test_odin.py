"""Tests — service Odin confine (etats, erreurs, confinement)."""

import asyncio
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest
from core.plugins import odin as mod
from core.plugins.odin import (
    STATE_ACTIVE,
    STATE_DEGRADED,
    STATE_ERROR,
    STATE_NOT_INSTALLED,
    STATE_STARTING,
    STATE_STOPPED,
    STATE_STOPPING,
    STATE_UNKNOWN,
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
    svc._lock = asyncio.Lock()
    svc._docker_cmd = "docker"
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


def test_status_dict_active_allows_stop_and_open():
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
    calls = []

    class FakeProc:
        returncode = 0
        async def communicate(self):
            calls.append("communicate")
            return b"[]", b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        calls.append(args)
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    ok, _ = await svc._run_docker(["ps", "--all", "--format", "json"])
    assert ok is True
    assert any("compose" in a and "ps" in a for a in calls)
    with pytest.raises(ValueError):
        await svc._run_docker(["down", "-v"])


@pytest.mark.asyncio
async def test_run_docker_reports_a_command_timeout(monkeypatch: pytest.MonkeyPatch):
    svc = _service()

    class FakeProc:
        returncode = -1
        async def communicate(self):
            raise asyncio.TimeoutError()

    async def fake_create_subprocess_exec(*args, **kwargs):
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    ok, output = await svc._run_docker(["ps", "--all", "--format", "json"], timeout=0.001)
    assert not ok
    assert "Timeout" in output


@pytest.mark.asyncio
async def test_health_probe_uses_http_endpoint(monkeypatch):
    svc = _service()
    calls = []

    class FakeResponse:
        status = 200

    class FakeUrlopen:
        status = 200

        def __init__(self):
            calls.append("urlopen")

        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: FakeUrlopen())
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("curl not found")))
    assert await svc.check_health() is True
    assert calls == ["urlopen"]


@pytest.mark.asyncio
async def test_status_distinguishes_absent_stopped_running_and_unhealthy(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)

    async def fake_health_false(*args, **kwargs):
        return False

    monkeypatch.setattr(svc, "check_health", fake_health_false)

    async def absent():
        return None

    monkeypatch.setattr(svc, "_inspect_container", absent)
    absent_status = await svc.get_status()
    assert absent_status["status"] == STATE_NOT_INSTALLED
    assert absent_status["allowed_actions"] == ["install"]

    async def stopped():
        return {"State": "exited", "ExitCode": 0, "Name": "odin-1"}

    monkeypatch.setattr(svc, "_inspect_container", stopped)
    assert (await svc.get_status())["status"] == STATE_STOPPED

    async def running():
        return {"State": "running", "Name": "odin-1"}

    monkeypatch.setattr(svc, "_inspect_container", running)
    degraded = await svc.get_status()
    assert degraded["status"] == STATE_DEGRADED
    assert degraded["healthy"] is False


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
async def test_unmanaged_listener_is_not_reported_as_odin_or_stopped(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: True)
    monkeypatch.setattr(svc, "check_health", lambda: True)

    async def absent():
        return None

    monkeypatch.setattr(svc, "_inspect_container", absent)
    result = await svc.get_status()
    assert result["status"] == STATE_NOT_INSTALLED
    assert result["allowed_actions"] == ["install"]


@pytest.mark.asyncio
async def test_failed_container_is_recoverable_and_offers_retry(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)

    async def failed():
        return {"State": "exited", "ExitCode": 1, "Name": "odin-1"}

    monkeypatch.setattr(svc, "_inspect_container", failed)
    result = await svc.get_status()
    assert result["status"] == STATE_ERROR
    assert result["allowed_actions"] == ["install", "start", "uninstall"]


@pytest.mark.asyncio
async def test_stop_uses_compose_down_and_preserves_stopped_start_action(monkeypatch):
    svc = _service()
    calls = []

    async def run_docker(args, timeout=60.0):
        calls.append(args)
        return True, ""

    async def no_containers():
        return None

    monkeypatch.setattr(svc, "_run_docker", run_docker)
    monkeypatch.setattr(svc, "_inspect_container", no_containers)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)
    result = await svc.stop()
    assert calls == [["stop"]]
    assert result["status"] == STATE_NOT_INSTALLED
    assert result["allowed_actions"] == ["install"]


@pytest.mark.asyncio
async def test_repeated_start_is_idempotent_for_the_same_compose_project(monkeypatch):
    svc = _service()
    calls = []
    container_present = False

    async def run_docker(args, timeout=60.0):
        nonlocal container_present
        calls.append(args)
        if args == ["up", "-d"]:
            container_present = True
        return True, ""

    async def inspect():
        if container_present:
            return {"State": "running", "Name": "odin-1"}
        return None

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(svc, "_run_docker", run_docker)
    monkeypatch.setattr(svc, "_inspect_container", inspect)

    async def fake_health_true(*args, **kwargs):
        return True

    monkeypatch.setattr(svc, "check_health", fake_health_true)
    monkeypatch.setattr(mod.asyncio, "sleep", no_sleep)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)

    first = await svc.start()
    second = await svc.start()
    assert first["status"] == STATE_ACTIVE
    assert second["status"] == STATE_ACTIVE
    assert calls == [["up", "-d"]]


@pytest.mark.asyncio
async def test_start_and_stop_requests_are_serialized(monkeypatch):
    svc = _service()
    calls = []
    container_present = False
    active_commands = 0
    max_active_commands = 0
    start_entered = asyncio.Event()
    release_start = asyncio.Event()
    real_sleep = asyncio.sleep

    async def run_docker(args, timeout=60.0):
        nonlocal container_present, active_commands, max_active_commands
        active_commands += 1
        max_active_commands = max(max_active_commands, active_commands)
        calls.append(args)
        if args == ["up", "-d"]:
            start_entered.set()
            await release_start.wait()
            container_present = True
        elif args in (["down"], ["stop"]):
            container_present = False
        active_commands -= 1
        return True, ""

    async def inspect():
        if container_present:
            return {"State": "running", "Name": "odin-1"}
        return {"State": "exited", "ExitCode": 0, "Name": "odin-1"}

    async def instant_sleep(_seconds):
        await real_sleep(0)

    monkeypatch.setattr(svc, "_run_docker", run_docker)
    monkeypatch.setattr(svc, "_inspect_container", inspect)

    async def fake_health_true(*args, **kwargs):
        return True

    monkeypatch.setattr(svc, "check_health", fake_health_true)
    monkeypatch.setattr(mod.asyncio, "sleep", instant_sleep)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)

    start_task = asyncio.create_task(svc.start())
    await start_entered.wait()
    stop_task = asyncio.create_task(svc.stop())
    await real_sleep(0)
    release_start.set()
    started, stopped = await asyncio.gather(start_task, stop_task)

    assert started["status"] == STATE_ACTIVE
    assert stopped["status"] == STATE_STOPPED
    assert calls == [["up", "-d"], ["stop"]]
    assert max_active_commands == 1


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


@pytest.mark.asyncio
async def test_controller_returns_non_ok_is_unhealthy(monkeypatch):
    svc = _service()
    svc._controller_url = "http://odin-controller:8765"
    svc._controller_token = "test-only"

    def fake_controller_request(path, args=None, timeout=10.0):
        return {"ok": False, "error": "container not found"}

    monkeypatch.setattr(svc, "_controller_request", fake_controller_request)
    assert await svc.check_health() is False


@pytest.mark.asyncio
async def test_controller_raises_is_unhealthy(monkeypatch):
    svc = _service()
    svc._controller_url = "http://odin-controller:8765"
    svc._controller_token = "test-only"

    def fake_controller_request(path, args=None, timeout=10.0):
        raise RuntimeError("controller unreachable")

    monkeypatch.setattr(svc, "_controller_request", fake_controller_request)
    assert await svc.check_health() is False


@pytest.mark.asyncio
async def test_controller_unavailable_in_get_status(monkeypatch):
    svc = _service()
    svc._controller_url = "http://odin-controller:8765"
    svc._controller_token = "test-only"

    def fake_controller_request(path, args=None, timeout=10.0):
        raise RuntimeError("controller unreachable")

    monkeypatch.setattr(svc, "_controller_request", fake_controller_request)
    result = await svc.get_status()
    assert result["status"] == STATE_UNKNOWN
    assert "controller" in result["error"].lower() or "inaccessible" in result["error"].lower()


@pytest.mark.asyncio
async def test_stop_timeout_when_container_does_not_stop(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)

    async def run_docker_ok(args, timeout=60.0):
        return True, ""

    async def inspect_always_running():
        return {"State": "running", "Name": "odin-1"}

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(svc, "_run_docker", run_docker_ok)
    monkeypatch.setattr(svc, "_inspect_container", inspect_always_running)
    monkeypatch.setattr(mod.asyncio, "sleep", no_sleep)

    result = await svc.stop()
    assert result["status"] == STATE_ERROR
    assert "délai imparti" in result["error"] or "timeout" in result["error"].lower()


@pytest.mark.asyncio
async def test_start_compose_up_fails(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)

    async def run_docker_fail(args, timeout=60.0):
        if args == ["up", "-d"]:
            return False, "docker compose up failed"
        return True, ""

    async def inspect_none():
        return None

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(svc, "_run_docker", run_docker_fail)
    monkeypatch.setattr(svc, "_inspect_container", inspect_none)
    monkeypatch.setattr(svc, "check_health", lambda *a, **k: False)
    monkeypatch.setattr(mod.asyncio, "sleep", no_sleep)

    result = await svc.start()
    assert result["status"] == STATE_ERROR
    assert "Échec du démarrage Docker Compose" in result["error"]


@pytest.mark.asyncio
async def test_docker_compose_ps_invalid_json(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)

    async def run_docker_bad_json(args, timeout=10.0):
        if args == ["ps", "--all", "--format", "json"]:
            return True, "not json at all\n{broken}\n"
        return True, ""

    monkeypatch.setattr(svc, "_run_docker", run_docker_bad_json)
    result = await svc.get_status()
    assert result["status"] == STATE_UNKNOWN


@pytest.mark.asyncio
async def test_restart_compose_fails(monkeypatch):
    svc = _service()
    monkeypatch.setattr(svc, "_validate_confinement", lambda: None)
    monkeypatch.setattr("core.plugins.odin.is_port_in_use", lambda *a, **k: False)

    async def run_docker_fail(args, timeout=60.0):
        if args == ["restart"]:
            return False, "docker compose restart failed"
        return True, ""

    async def inspect_running():
        return {"State": "running", "Name": "odin-1"}

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(svc, "_run_docker", run_docker_fail)
    monkeypatch.setattr(svc, "_inspect_container", inspect_running)
    monkeypatch.setattr(svc, "check_health", lambda *a, **k: True)
    monkeypatch.setattr(mod.asyncio, "sleep", no_sleep)

    result = await svc.restart()
    assert result["status"] == STATE_ERROR
    assert "Échec du redémarrage Docker Compose" in result["error"]
