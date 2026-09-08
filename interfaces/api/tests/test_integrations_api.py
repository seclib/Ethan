"""Tests API — Intégrations (routes /integrations, RBAC, credentials).

Exécute les fonctions du router avec le vrai IntegrationManager (store
mémoire) et vérifie :
- les gates RBAC (PLUGINS requis pour muter, 403 sinon) via require_permission
- le credential handling : les credentials ne sont JAMAIS dans une réponse
- le lifecycle connect/disconnect/test au niveau HTTP
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from core.auth import Permission
from core.integrations import IntegrationManager
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import require_permission
from interfaces.api.routers import integrations as integrations_router
from interfaces.api.routers.integrations import set_integration_manager

# Références (le module évite que pytest collecte test_integration comme test)
connect_integration = integrations_router.connect_integration
create_integration = integrations_router.create_integration
delete_integration = integrations_router.delete_integration
disconnect_integration = integrations_router.disconnect_integration
get_integration = integrations_router.get_integration
list_integrations = integrations_router.list_integrations
test_integration = integrations_router.test_integration
update_integration = integrations_router.update_integration
integrations_router.test_integration.__test__ = False
integrations_router.test_connection = getattr(
    integrations_router, "test_connection", None
)


SECRET = "sk-integration-secret-98765"


class _FakeRequest:
    """Request factice pour les routes (user_id non utilisé par ce router)."""


@pytest.fixture()
def manager():
    mgr = IntegrationManager(store=CoreRecordStore())
    set_integration_manager(mgr)
    yield mgr
    set_integration_manager(None)


def _run(coro):
    return asyncio.run(coro)


# ── Routes CRUD (délégation Core, sans secrets) ────────────────────────────


def test_create_and_list_without_secrets(manager):
    created = _run(create_integration({
        "name": "github-prod",
        "kind": "developer",
        "config": {"base_url": "https://api.github.com"},
        "credentials": {"token": SECRET},
        "capabilities": ["repos.read"],
        "required_permissions": ["execute"],
    }))
    assert created["name"] == "github-prod"
    assert SECRET not in str(created)

    listing = _run(list_integrations(_FakeRequest(), kind=None))
    assert len(listing) == 1
    assert SECRET not in str(listing)
    assert listing[0]["has_credentials"] is True
    assert listing[0]["credential_keys"] == ["token"]


def test_get_detail_reports_credential_keys_not_values(manager):
    created = _run(create_integration({
        "name": "s3", "kind": "storage",
        "credentials": {"secret_key": SECRET},
    }))
    detail = _run(get_integration(created["id"]))
    assert SECRET not in str(detail)
    assert detail["has_credentials"] is True
    assert detail["credential_keys"] == ["secret_key"]


def test_create_invalid_kind_returns_422(manager):
    with pytest.raises(HTTPException) as exc:
        _run(create_integration({"name": "x", "kind": "demo-thing"}))
    assert exc.value.status_code == 422


def test_get_missing_returns_404(manager):
    with pytest.raises(HTTPException) as exc:
        _run(get_integration("ghost"))
    assert exc.value.status_code == 404


def test_update_config_and_rotate_credentials(manager):
    created = _run(create_integration({
        "name": "rot", "kind": "storage", "credentials": {"token": SECRET}
    }))
    updated = _run(update_integration(created["id"], {
        "config": {"bucket": "ethan"},
        "credentials": {"token": "sk-rotated"},
    }))
    assert updated["config"] == {"bucket": "ethan"}
    assert SECRET not in str(updated)
    # Rotation effective côté Core
    creds = _run(manager.get_credentials(created["id"]))
    assert creds == {"token": "sk-rotated"}


def test_delete_purges_credentials(manager):
    created = _run(create_integration({
        "name": "bye", "kind": "storage", "credentials": {"token": SECRET}
    }))
    result = _run(delete_integration(created["id"]))
    assert result["status"] == "deleted"
    assert _run(manager.get_credentials(created["id"])) == {}


# ── Lifecycle HTTP ─────────────────────────────────────────────────────────


def test_connect_disconnect_test_flow(manager):
    created = _run(create_integration({
        "name": "flow", "kind": "web-search",
        "credentials": {"api_key": "k"},
        "metadata": {"required_credentials": ["api_key"]},
    }))

    health = _run(test_integration(created["id"]))
    assert health["connected"] is True

    connected = _run(connect_integration(created["id"]))
    assert connected["status"] == "connected"
    assert SECRET not in str(connected)

    disconnected = _run(disconnect_integration(created["id"]))
    assert disconnected["status"] == "disconnected"

    with pytest.raises(HTTPException) as exc:
        _run(connect_integration("ghost"))
    assert exc.value.status_code == 404


def test_connect_disabled_via_http(manager):
    created = _run(create_integration({"name": "off", "kind": "mcp", "enabled": False}))
    with pytest.raises(HTTPException) as exc:
        _run(connect_integration(created["id"]))
    assert exc.value.status_code == 422


# ── RBAC : mutations exigent PLUGINS, lecture READ ──────────────────────────


def _permission_gate(permission: Permission, role: str | None):
    """Construit une fausse request avec le rôle donné et exécute le gate."""

    class _Req:
        pass

    request = _Req()
    request.state = type("State", (), {})()
    request.state.token_payload = {"role": role} if role else {}
    checker = require_permission(permission)
    return checker(request)


def test_plugins_permission_required_for_mutations():
    """user/viewer (sans PLUGINS) → 403 sur toute mutation d'intégration."""
    for role in ("user", "viewer", None):
        with pytest.raises(HTTPException) as exc:
            _permission_gate(Permission.PLUGINS, role)
        assert exc.value.status_code == 403


def test_admin_has_plugins_permission():
    assert _permission_gate(Permission.PLUGINS, "admin") is True


def test_read_permission_allows_listing_for_all_roles():
    for role in ("admin", "user", "viewer"):
        assert _permission_gate(Permission.READ, role) is True


def test_integration_declared_permissions_are_ethan_permissions(manager):
    """Les permissions déclarées d'une intégration sont des permissions ETHAN
    valides — une intégration ne peut pas inventer ses propres droits."""
    created = _run(create_integration({
        "name": "scoped", "kind": "automation",
        "required_permissions": ["execute", "files"],
    }))
    valid = {p.value for p in Permission}
    assert set(created["required_permissions"]) <= valid
    with pytest.raises(HTTPException) as exc:
        _run(create_integration({
            "name": "escalate", "kind": "automation",
            "required_permissions": ["become-root"],
        }))
    assert exc.value.status_code == 422
