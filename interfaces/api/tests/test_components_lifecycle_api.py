"""Tests API — routes component lifecycle : passerelle mince vers le Core.

Ces tests verrouillent la route de logs composant :
- la permission READ déclarée (matrice RBAC par route, ESR-006 §2) ;
- le passage par le CapabilityManager du Core (catalogue builtin réel) ;
- le refus honnête quand un backend ne produit pas de logs (jamais de faux
  contenu) ;
- la validation `tail` déléguée au Core (422, pas de lecture arbitraire).
"""

from __future__ import annotations

import asyncio
import inspect

import pytest
from core.auth import Permission
from fastapi import HTTPException
from interfaces.api.routers import component_lifecycle as components_router
from interfaces.api.routers.component_lifecycle import set_component_manager

get_component_logs = components_router.get_component_logs


def _run(coro):
    return asyncio.run(coro)


def _route_permissions(func) -> set:
    """Permissions déclaratives de la route dont `func` est l'endpoint.

    Lit le contrat d'introspection publié par ``require_permission``
    (``checker.permissions``) — paramètre de signature et `dependencies` du
    routeur, selon le style de déclaration choisi.
    """
    found: set = set()
    for param in inspect.signature(func).parameters.values():
        dep = getattr(param.default, "dependency", None)
        found.update(getattr(dep, "permissions", ()) or ())
    for route in components_router.router.routes:
        if getattr(route, "endpoint", None) is func:
            for dep_obj in route.dependencies:
                dep = getattr(dep_obj, "dependency", None)
                found.update(getattr(dep, "permissions", ()) or ())
    return found


@pytest.fixture()
def manager():
    from core.capability_manager.builtin import build_manager

    mgr = build_manager()
    set_component_manager(mgr)
    yield mgr
    set_component_manager(None)


def test_route_logs_exige_read(manager):
    """La lecture des logs est une opération READ — jamais une mutation."""
    assert Permission.READ in _route_permissions(get_component_logs)


def test_logs_memory_indisponible_honnete(manager):
    """Un composant sans processus permanent n'a pas de faux logs à montrer."""
    out = _run(get_component_logs("memory"))
    assert out["available"] is False
    assert out["lines"] == []
    assert out["detail"]


def test_logs_docker_passe_par_le_core(manager, monkeypatch):
    """Les logs Docker viennent du Core (manager injecté), pas du router."""
    from core.capability_manager import backends as backends_mod

    async def fake_run(argv, timeout=300.0):
        return True, "qdrant ready\nQDRANT_VERSION=1.12"

    monkeypatch.setattr(backends_mod, "_run", fake_run)
    out = _run(get_component_logs("qdrant", tail=10))
    assert out["available"] is True
    assert out["source"] == "docker"
    assert out["lines"] == ["qdrant ready", "QDRANT_VERSION=1.12"]


def test_logs_tail_invalide_422(manager):
    """`tail` hors bornes → 422 (validation Core), jamais une lecture bornée
    uniquement côté interface."""
    with pytest.raises(HTTPException) as exc:
        _run(get_component_logs("memory", tail=0))
    assert exc.value.status_code == 422
