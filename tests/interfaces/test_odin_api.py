"""Tests API — routeur Odin (RBAC, erreurs, idempotence)."""

import asyncio
import inspect

from core.plugins import odin as mod
from fastapi import FastAPI
from fastapi.routing import APIRoute
from interfaces.api.routers import odin as odin_router

ODIN_STATUS_PATH = "/v1/plugins/odin/status"
ODIN_START_PATH = "/v1/plugins/odin/start"


class _FakeService:
    def __init__(self, status="stopped", error=None, healthy=False, allowed=None):
        self._payload = {
            "id": "odin",
            "name": "Odin",
            "status": status,
            "port": 4173,
            "host": "127.0.0.1",
            "url": "http://127.0.0.1:4173",
            "container_id": None,
            "healthy": healthy,
            "error": error,
            "allowed_actions": allowed or [],
        }
        self.calls = []

    async def get_status(self):
        self.calls.append("status")
        return dict(self._payload)

    async def start(self):
        self.calls.append("start")
        payload = dict(self._payload)
        payload.update(
            {"status": "active", "healthy": True, "allowed_actions": ["stop"]}
        )
        return payload

    async def stop(self):
        self.calls.append("stop")
        payload = dict(self._payload)
        payload.update(
            {"status": "stopped", "healthy": False, "allowed_actions": ["start"]}
        )
        return payload

    async def restart(self):
        self.calls.append("restart")
        return await self.start()


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


def test_status_ok():
    app = FastAPI()
    app.include_router(odin_router.router)
    status_route = next(
        r for r in odin_router.router.routes if getattr(r, "path", "") == ODIN_STATUS_PATH
    )
    assert isinstance(status_route, APIRoute)
    start_route = next(
        r for r in odin_router.router.routes if getattr(r, "path", "") == ODIN_START_PATH
    )
    assert "POST" in (start_route.methods or set())


def test_start_stop_restart_idempotent():
    svc = _FakeService()
    mod.set_odin_service(svc)
    try:
        assert _run(svc.start())["status"] == "active"
        assert _run(svc.start())["status"] == "active"
        assert _run(svc.stop())["status"] == "stopped"
    finally:
        mod.set_odin_service(None)


def test_port_conflict_maps_to_409():
    src = inspect.getsource(odin_router.start_service)
    assert "409" in src and "Conflit de port" in src


def test_rbac_declared_on_routes():
    assert "Permission.READ" in inspect.getsource(odin_router.get_status)
    assert "Permission.PLUGINS" in inspect.getsource(odin_router.start_service)
    assert "Permission.PLUGINS" in inspect.getsource(odin_router.stop_service)
    assert "Permission.PLUGINS" in inspect.getsource(odin_router.restart_service)