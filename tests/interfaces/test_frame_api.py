"""Tests API — routeur Frame (RBAC, surface minimale)."""

import inspect

from interfaces.api.routers import frame as frame_router

FRAME_STATUS_PATH = "/v1/plugins/frame/status"
FRAME_START_PATH = "/v1/plugins/frame/start"


def test_status_and_start_paths_exist():
    status_route = next(
        r for r in frame_router.router.routes if getattr(r, "path", "") == FRAME_STATUS_PATH
    )
    start_route = next(
        r for r in frame_router.router.routes if getattr(r, "path", "") == FRAME_START_PATH
    )
    assert "GET" in (status_route.methods or set())
    assert "POST" in (start_route.methods or set())


def test_rbac_declared_on_routes():
    assert "Permission.READ" in inspect.getsource(frame_router.get_status)
    assert "Permission.PLUGINS" in inspect.getsource(frame_router.start_service)
    assert "Permission.PLUGINS" in inspect.getsource(frame_router.stop_service)
    assert "Permission.PLUGINS" in inspect.getsource(frame_router.restart_service)


def test_lifecycle_router_matches_confinement_contract():
    src = inspect.getsource(frame_router.start_service)
    assert "409" in src and "Conflit de port" in src
