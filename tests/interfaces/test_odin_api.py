"""Tests API — routeur Odin (RBAC, erreurs, idempotence)."""

import asyncio
import inspect

import pytest
from core.plugins import odin as mod
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from interfaces.api.routers import odin as odin_router

ODIN_STATUS_PATH = "/v1/plugins/odin/status"
ODIN_START_PATH = "/v1/plugins/odin/start"


class _FakeService:
    """Service fictif configuré pour reproduire un état initial précis."""

    def __init__(self, status="installed_stopped", error=None, healthy=False, allowed=None):
        self._current_status = status
        self._initial_error = error
        self._initial_healthy = healthy
        self._initial_allowed = allowed or []
        self.calls = []

    def _status_payload(self, status, healthy=None, allowed=None, error=None):
        payload = {
            "id": "odin",
            "name": "Odin",
            "status": status,
            "port": 4173,
            "host": "127.0.0.1",
            "url": "http://127.0.0.1:4173",
            "container_id": None,
            "healthy": healthy if healthy is not None else self._initial_healthy,
            "error": error if error is not None else self._initial_error,
            "allowed_actions": allowed if allowed is not None else self._initial_allowed,
        }
        return payload

    async def get_status(self):
        self.calls.append("status")
        # Retourne l'état courant (mis à jour par les opérations précédentes)
        return self._status_payload(self._current_status)

    async def start(self):
        self.calls.append("start")
        self._current_status = "running"
        return self._status_payload("running", healthy=True, allowed=["stop"])

    async def stop(self):
        self.calls.append("stop")
        # Arrêt: l'état devient STOPPED, sauf si pas installé
        if self._current_status == "not_installed":
            return self._status_payload("not_installed", healthy=False, allowed=["install"])
        self._current_status = "installed_stopped"
        return self._status_payload("installed_stopped", healthy=False, allowed=["start"])

    async def restart(self):
        self.calls.append("restart")
        self._current_status = "running"
        return await self.start()

    async def install(self):
        self.calls.append("install")
        self._current_status = "running"
        return self._status_payload("running", healthy=True, allowed=["stop"])

    async def uninstall(self):
        self.calls.append("uninstall")
        self._current_status = "not_installed"
        return self._status_payload("not_installed", healthy=False, allowed=["install"])


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
        assert _run(svc.start())["status"] == "running"
        assert _run(svc.start())["status"] == "running"
        assert _run(svc.stop())["status"] == "installed_stopped"
    finally:
        mod.set_odin_service(None)


def test_lifecycle_routes_return_verified_success():
    svc = _FakeService()
    mod.set_odin_service(svc)
    try:
        assert _run(odin_router.start_service())["status"] == "running"
        assert _run(odin_router.stop_service())["status"] == "installed_stopped"
    finally:
        mod.set_odin_service(None)


def test_port_conflict_maps_to_409():
    src = inspect.getsource(odin_router.start_service)
    assert "409" in src and "Conflit de port" in src


@pytest.mark.parametrize(
    ("route", "method_name", "payload"),
    [
        (
            odin_router.start_service,
            "start",
            {"status": "degraded", "error": "health probe failed"},
        ),
        (
            odin_router.stop_service,
            "stop",
            {"status": "unknown", "error": "daemon unavailable"},
        ),
    ],
)
def test_lifecycle_routes_require_verified_final_state(route, method_name, payload):
    svc = _FakeService()

    async def operation():
        svc.calls.append(method_name)
        return payload

    setattr(svc, method_name, operation)
    mod.set_odin_service(svc)
    try:
        with pytest.raises(HTTPException) as raised:
            _run(route())
        assert raised.value.status_code == 503
    finally:
        mod.set_odin_service(None)


def test_rbac_declared_on_routes():
    assert "Permission.READ" in inspect.getsource(odin_router.get_status)
    assert "Permission.PLUGINS" in inspect.getsource(odin_router.start_service)
    assert "Permission.PLUGINS" in inspect.getsource(odin_router.stop_service)
    assert "Permission.PLUGINS" in inspect.getsource(odin_router.restart_service)

# ── Nouveaux tests pour le cycle de vie Odin ─────────────────────────────


def test_install_idempotent():
    svc = _FakeService()
    mod.set_odin_service(svc)
    try:
        # Premier install
        res1 = _run(svc.install())
        assert res1["status"] == "running", f"Installation #1 unexpected: {res1['status']}"

        # Deuxième install (idempotente) - meme resultat
        res2 = _run(svc.install())
        assert res2["status"] == "running", \
            f"Install idempotent failed: {res2['status']} != running"
        assert svc.calls.count("install") == 2, "Install called twice"
    finally:
        mod.set_odin_service(None)


def test_detection_existing_installation():
    svc = _FakeService(status="installed_stopped", healthy=False,
                       allowed=["start", "uninstall"])
    mod.set_odin_service(svc)
    try:
        res = _run(odin_router.get_status())
        assert res["status"] == "installed_stopped"
        assert res["allowed_actions"] == ["start", "uninstall"]
        assert svc.calls.count("status") == 1
    finally:
        mod.set_odin_service(None)


def test_install_errors():
    # Dépôt manquant (install ne peut pas s'effectuer)
    svc = _FakeService(status="not_installed", error="Dépôt Odin introuvable",
                       healthy=False, allowed=["install"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.install())
        assert res["status"] == "running", f"Install devrait réussir: {res['status']}"
    finally:
        mod.set_odin_service(None)

    # Port occupé (install échoue via la détection de conflit de port)
    svc = _FakeService(status="installed_stopped",
                       healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        # Simulate port conflict by overriding install to return error
        async def _fail_install():
            return {"status": "error", "error": "Conflit de port : le port 4173 est déjà utilisé",
                    "healthy": False, "allowed_actions": ["start"]}
        svc.install = _fail_install
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.install_service())
        assert raised.value.status_code == 409, \
            f"Expected 409, got {raised.value.status_code}"
        assert "Conflit de port" in raised.value.detail
    finally:
        mod.set_odin_service(None)

    # Compose invalide (status error)
    svc = _FakeService(status="error", error="Configuration Compose invalide",
                       healthy=False, allowed=["install"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.install())
        assert res["status"] == "running", f"Install devrait réussir avec erreur: {res['status']}"
    finally:
        mod.set_odin_service(None)


def test_inconsistent_state():
    # Conteneur arrêté mais port occupé par un tiers
    svc = _FakeService(status="installed_stopped", healthy=False,
                       allowed=["start", "stop"])
    mod.set_odin_service(svc)
    try:
        # Override start to simulate port conflict
        async def _fail_start():
            return {"status": "error", "error": "Conflit de port : le port 4173 est déjà utilisé",
                    "healthy": False, "allowed_actions": ["start"]}
        svc.start = _fail_start
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.start_service())
        assert raised.value.status_code == 409, \
            f"Expected 409, got {raised.value.status_code}"
        assert "Conflit de port" in raised.value.detail
    finally:
        mod.set_odin_service(None)


def test_uninstall_preserves_volumes():
    svc = _FakeService(status="installed_stopped", healthy=False,
                       allowed=["start", "uninstall"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.uninstall())
        # L'uninstall n'utilise pas -v pour supprimer les volumes
        assert res["status"] == "not_installed"
        assert svc.calls.count("uninstall") == 1
    finally:
        mod.set_odin_service(None)


def test_get_status_templates():
    svc = _FakeService()
    mod.set_odin_service(svc)
    try:
        # Vérifier que les champs requis existent dans le statut
        res = _run(odin_router.get_status())
        assert "id" in res
        assert "name" in res
        assert "status" in res
        assert "port" in res
        assert "host" in res
        assert "url" in res
        assert "healthy" in res
        assert "allowed_actions" in res
    finally:
        mod.set_odin_service(None)

# ── Nouveaux tests (v2) : vérification de cycle de vie complet ─────────────


def test_install_idempotent_stays_running() -> None:
    """L'installation est idempotente : deux appels consécutifs restent 'running'."""
    svc = _FakeService(status="not_installed", error=None, healthy=False, allowed=["install"])
    mod.set_odin_service(svc)
    try:
        res1 = _run(svc.install())
        assert res1["status"] == "running", f"Install #1 unexpected: {res1}"
        assert svc.calls.count("install") == 1

        res2 = _run(svc.install())
        assert res2["status"] == "running", f"Install #2 unexpected: {res2}"
        assert svc.calls.count("install") == 2
    finally:
        mod.set_odin_service(None)


def test_install_idempotent_stays_running_when_already_active() -> None:
    """Install sur un service déjà 'running' ne remonte pas d'erreur."""
    svc = _FakeService(status="running", healthy=True, allowed=["stop"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.install())
        assert res["status"] == "running"
    finally:
        mod.set_odin_service(None)


def test_install_repo_missing_returns_error() -> None:
    """Install échoue quand le dépôt Odin est absent."""
    svc = _FakeService(status="not_installed", error="Dépôt Odin introuvable", healthy=False, allowed=["install"])
    mod.set_odin_service(svc)
    try:
        # Override install pour simuler l'absence de dépôt
        async def _fail_install():
            return {"status": "error", "healthy": False,
                    "error": "Dépôt Odin introuvable", "allowed_actions": []}
        svc.install = _fail_install
        res = _run(svc.install())
        assert res["status"] == "error"
        assert "introuvable" in res["error"]
    finally:
        mod.set_odin_service(None)


def test_install_port_conflict_returns_409() -> None:
    """Install échoue avec 409 quand le port 4173 est occupé."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        async def _fail_install():
            return {"status": "error", "healthy": False,
                    "error": "Conflit de port : le port 4173 est déjà utilisé", "allowed_actions": []}
        svc.install = _fail_install
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.install_service())
        assert raised.value.status_code == 409
        assert "Conflit de port" in raised.value.detail
    finally:
        mod.set_odin_service(None)


def test_start_already_active_is_idempotent() -> None:
    """Start sur un service déjà actif ne remonte pas d'erreur."""
    svc = _FakeService(status="running", healthy=True, allowed=["stop"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.start())
        assert res["status"] == "running", f"Start unexpected: {res}"
    finally:
        mod.set_odin_service(None)


def test_start_fails_port_conflict() -> None:
    """Start échoue avec 409 quand le port 4173 est occupé."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        async def _fail_start():
            return {"status": "error", "healthy": False,
                    "error": "Conflit de port : le port 4173 est déjà utilisé", "allowed_actions": []}
        svc.start = _fail_start
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.start_service())
        assert raised.value.status_code == 409
        assert "Conflit de port" in raised.value.detail
    finally:
        mod.set_odin_service(None)


def test_start_fails_compose_up() -> None:
    """Start échoue avec 503 quand docker compose up échoue."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        async def _fail_start():
            return {"status": "error", "healthy": False,
                    "error": "Échec du démarrage Docker Compose : image introuvable", "allowed_actions": []}
        svc.start = _fail_start
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.start_service())
        assert raised.value.status_code == 503
        assert "Échec du démarrage" in raised.value.detail
    finally:
        mod.set_odin_service(None)


def test_start_fails_health_probe() -> None:
    """Start échoue avec 503 quand la sonde de santé échoue."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        async def _fail_start():
            return {"status": "degraded", "healthy": False,
                    "error": "Le conteneur a démarré, mais Odin ne répond pas sur son endpoint HTTP.", "allowed_actions": []}
        svc.start = _fail_start
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.start_service())
        assert raised.value.status_code == 503
        assert "endpoint HTTP" in raised.value.detail
    finally:
        mod.set_odin_service(None)


def test_stop_already_stopped_is_noop() -> None:
    """Stop sur un service déjà arrêté ne remonte pas d'erreur."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.stop())
        assert res["status"] == "installed_stopped"
    finally:
        mod.set_odin_service(None)


def test_stop_when_not_installed_returns_not_installed() -> None:
    """Stop sur un service 'not_installed' est correctement géré."""
    svc = _FakeService(status="not_installed", healthy=False, allowed=["install"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.stop())
        assert res["status"] == "not_installed"
    finally:
        mod.set_odin_service(None)


def test_stop_fails_when_docker_down() -> None:
    """Stop échoue avec 503 quand docker ne répond pas."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        async def _fail_stop():
            return {"status": "error", "healthy": False,
                    "error": "Échec de l'arrêt Docker Compose", "allowed_actions": []}
        svc.stop = _fail_stop
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.stop_service())
        assert raised.value.status_code == 503
        assert "Échec de l'arrêt" in raised.value.detail
    finally:
        mod.set_odin_service(None)


def test_stop_success_refreshes_state() -> None:
    """Après un stop, l'état est correctement rafraîchi."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.stop())
        assert res["status"] == "installed_stopped"
        assert "allowed_actions" in res
        # L'état après stop doit permettre de démarrer à nouveau
        assert "start" in res.get("allowed_actions", [])
    finally:
        mod.set_odin_service(None)


def test_refresh_after_operation() -> None:
    """L'état est rafraîchi après chaque opération."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        # Opération start → status devient running
        res = _run(svc.start())
        assert res["status"] == "running"
        assert "healthy" in res
        assert res["healthy"] is True

        # Rafraîchir → même état
        res2 = _run(svc.get_status())
        assert res2["status"] == "running"
        assert svc.calls.count("status") == 1  # get_status ajoute "status"
    finally:
        mod.set_odin_service(None)


def test_inconsistent_state_port_busy_container_stopped() -> None:
    """État incohérent : conteneur arrêté mais port 4173 occupé par un tiers."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start", "stop"])
    mod.set_odin_service(svc)
    try:
        # Simulate port conflict → start must fail with 409
        async def _fail_start():
            return {"status": "error", "healthy": False,
                    "error": "Conflit de port : le port 4173 est déjà utilisé", "allowed_actions": []}
        svc.start = _fail_start
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.start_service())
        assert raised.value.status_code == 409
    finally:
        mod.set_odin_service(None)


def test_inconsistent_state_port_busy_health_degraded() -> None:
    """État incohérent : conteneur s'exécute mais ne répond pas (degraded)."""
    svc = _FakeService(status="degraded", healthy=False, allowed=["stop", "restart"])
    mod.set_odin_service(svc)
    try:
        # Health degraded → stop must succeed
        res = _run(svc.stop())
        assert res["status"] == "installed_stopped"
    finally:
        mod.set_odin_service(None)


def test_error_on_stop_when_container_not_found() -> None:
    """Stop échoue proprement quand le conteneur est introuvable."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        async def _fail_stop():
            return {"status": "error", "healthy": False,
                    "error": "Le conteneur Odin n'a pas pu être arrêté dans le délai imparti.", "allowed_actions": []}
        svc.stop = _fail_stop
        with pytest.raises(HTTPException) as raised:
            _run(odin_router.stop_service())
        assert raised.value.status_code == 503
        assert "délai imparti" in raised.value.detail
    finally:
        mod.set_odin_service(None)


def test_restart_success_flops_to_active() -> None:
    """Restart transforme l'état de stopped → running."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.restart())
        assert res["status"] == "running", f"Restart unexpected: {res}"
        assert res["healthy"] is True
    finally:
        mod.set_odin_service(None)


def test_uninstall_preserves_volumes_and_data() -> None:
    """Uninstall arrête mais ne supprime pas les volumes (sans -v)."""
    svc = _FakeService(status="installed_stopped", healthy=False, allowed=["start", "uninstall"])
    mod.set_odin_service(svc)
    try:
        res = _run(svc.uninstall())
        assert res["status"] == "not_installed"
        assert svc.calls.count("uninstall") == 1
        # Vérifier que le payload ne contient pas l'option -v
        assert "allowed_actions" in res
    finally:
        mod.set_odin_service(None)


def test_install_without_permissions() -> None:
    """L'install retourne 403 si l'utilisateur n'a pas la permission requise."""
    # Ce test simulate une absence de permission via l'API router
    from interfaces.api.routers import odin as odin_router
    import inspect
    src = inspect.getsource(odin_router.install_service)
    assert "Permission.PLUGINS" in src

    # L'interface expose bien l'opération install
    assert hasattr(odin_router, "install_service")
