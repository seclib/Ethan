"""Câblage du SecurityGateway sur le plan de contrôle (CTO P0-1).

Le ``SecurityGateway`` (``core/security/gateway.py``) valide les actions des
routes qui installent du code externe via ``interfaces/api/gateway_guard``.
Ce fichier verrouille deux choses :

1. **Câblage** : les routes ``POST /v1/plugins/install`` et
   ``POST /v1/skills/import`` exigent à la fois la permission RBAC
   ``PLUGINS`` **et** le guard du gateway — et la permission est résolue
   AVANT le guard (une identité non autorisée n'épuise même pas le rate
   limit du gateway) ;
2. **Comportement du guard** : rejet → 403, dépassement de rate limit → 429,
   et l'acteur transmis au gateway est le ``sub`` du JWT (le rate limit est
   isolé par utilisateur, pas par rôle partagé).

Convention : introspection déclarative (``permission`` / ``gateway_action``),
jamais d'exécution HTTP réelle ici — les tests d'exécution du gateway lui-même
vivent dans ``tests/security/``.
"""

from __future__ import annotations

import pytest
from core.auth import Permission
from core.security.types import ActionType
from fastapi import HTTPException
from routers import v1


def _routes_of(router) -> list:
    inner = getattr(router, "router", router)
    return list(getattr(inner, "routes") or [])


def _dependency_calls(route) -> list:
    """Callables des dépendances de route, dans l'ordre de résolution."""
    dependant = getattr(route, "dependant", None)
    return [dep.call for dep in getattr(dependant, "dependencies", []) or []]


def _route_for(method: str, path: str):
    for route in _routes_of(v1.router):
        if getattr(route, "path", None) == path:
            if method.upper() in {m.upper() for m in getattr(route, "methods", set())}:
                return route
    raise AssertionError(f"Route introuvable : {method.upper()} {path}")


# ── 1. Câblage ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("path", ["/v1/plugins/install", "/v1/skills/import"])
def test_route_exige_permission_et_gateway(path: str) -> None:
    calls = _dependency_calls(_route_for("POST", path))

    permissions = [c.permission for c in calls if hasattr(c, "permission")]
    guarded = [c.gateway_action for c in calls if hasattr(c, "gateway_action")]

    assert Permission.PLUGINS in permissions, f"{path} a perdu son gate RBAC PLUGINS"
    assert guarded == [ActionType.PLUGIN_INSTALL], (
        f"{path} doit être passée par le SecurityGateway (PLUGIN_INSTALL)"
    )


@pytest.mark.parametrize("path", ["/v1/plugins/install", "/v1/skills/import"])
def test_permission_resolue_avant_le_guard(path: str) -> None:
    """RBAC d'abord : un rôle sans permission ne consomme pas le rate limit."""
    calls = _dependency_calls(_route_for("POST", path))
    idx_perm = next(i for i, c in enumerate(calls) if getattr(c, "permission", None) is not None)
    idx_guard = next(
        i for i, c in enumerate(calls) if getattr(c, "gateway_action", None) is not None
    )
    assert idx_perm < idx_guard, f"{path}: le gate RBAC doit précéder le gateway guard"


# ── 2. Comportement du guard ─────────────────────────────────────────────────


class _FakeState:
    def __init__(self, payload: dict) -> None:
        self.token_payload = payload
        self.user = payload.get("sub", "unknown")


class _FakeRequest:
    def __init__(self, payload: dict) -> None:
        self.state = _FakeState(payload)


class _StubGateway:
    """Gateway factice : renvoie la décision imposée, mémorise l'appel."""

    def __init__(self, valid: bool, error: str | None = None) -> None:
        self._valid = valid
        self._error = error
        self.calls: list[dict] = []

    async def execute(self, action_type, params, source="llm", actor=None):
        from core.security.types import ActionResult

        self.calls.append(
            {"action_type": action_type, "source": source, "actor": actor, "params": params}
        )
        return ActionResult(action_id="stub", valid=self._valid, status="stub", error=self._error)


class _FakeGatewayModule:
    """Remplace la coroutine ``get_security_gateway`` par un getter sync."""

    def __init__(self, gateway: _StubGateway) -> None:
        self._gateway = gateway

    async def __call__(self):
        return self._gateway


ADMIN = {"role": "admin", "sub": "alice", "sid": "s1"}


async def _run_checker(monkeypatch, gateway: _StubGateway, payload: dict) -> None:
    import interfaces.api.gateway_guard as gateway_guard

    monkeypatch.setattr(gateway_guard, "get_security_gateway", _FakeGatewayModule(gateway))
    checker = gateway_guard.gateway_guard(ActionType.PLUGIN_INSTALL)
    await checker(_FakeRequest(payload))


@pytest.mark.asyncio
async def test_gateway_accepte_laisse_passer(monkeypatch) -> None:
    gateway = _StubGateway(valid=True)
    await _run_checker(monkeypatch, gateway, ADMIN)
    assert len(gateway.calls) == 1
    call = gateway.calls[0]
    assert call["action_type"] == ActionType.PLUGIN_INSTALL.value
    assert call["actor"] == "alice", "le rate limit doit être isolé par utilisateur (sub)"
    assert call["source"] == "admin"


@pytest.mark.asyncio
async def test_rejet_du_gateway_leve_403(monkeypatch) -> None:
    gateway = _StubGateway(valid=False, error="permission refusée par politique")
    with pytest.raises(HTTPException) as excinfo:
        await _run_checker(monkeypatch, gateway, ADMIN)
    assert excinfo.value.status_code == 403


@pytest.mark.asyncio
async def test_rate_limit_leve_429(monkeypatch) -> None:
    gateway = _StubGateway(valid=False, error="Rate limit exceeded for actor alice")
    with pytest.raises(HTTPException) as excinfo:
        await _run_checker(monkeypatch, gateway, ADMIN)
    assert excinfo.value.status_code == 429
    assert "Rate limit" in excinfo.value.detail


@pytest.mark.asyncio
async def test_role_non_admin_mappe_sur_user(monkeypatch) -> None:
    gateway = _StubGateway(valid=True)
    await _run_checker(monkeypatch, gateway, {"role": "viewer", "sub": "bob"})
    call = gateway.calls[0]
    assert call["source"] == "user"
    assert call["actor"] == "bob"
