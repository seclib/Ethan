"""DAĒNĀ P2.8.2 — Routes API des Project Anchors : tests ciblés.

Environnement isolé : store Core en mémoire, projets et données semés dans
des domaines temporaires. Aucun accès à PostgreSQL de production, aucune
donnée réelle touchée.

Couverture :
  - Délégation effective au service Core (aucune logique métier au routeur)
  - Permissions READ (lecture) et MEMORY (écriture)
  - Refus d'accès sans permission
  - Traduction des erreurs : règle métier (422) vs indisponibilité (503)
  - Distinction inventaire vide / inventaire indisponible
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.projects.anchors import ProjectAnchorService, ProjectAnchorStoreUnavailable
from core.state.record_store import CoreRecordStore
from interfaces.api.auth import auth_middleware, create_access_token
from interfaces.api.routers import projects as projects_router


def _run(coro):
    """Exécute une coroutine dans une boucle événementielle dédiée."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _project(project_id: str, *, active: bool = True, name: str = "Projet") -> dict:
    return {
        "id": project_id,
        "name": name,
        "description": "",
        "instructions": "",
        "user_id": "tester",
        "metadata": {},
        "is_active": active,
        "created_at": "2026-11-12T00:00:00Z",
        "updated_at": "2026-11-12T00:00:00Z",
    }


def _knowledge(record_id: str, label: str) -> dict:
    return {
        "id": record_id,
        "label": label,
        "node_type": "concept",
        "content": "c",
        "source": "s",
        "connections": [],
        "metadata": {},
        "created_at": "2026-11-12T00:00:00Z",
        "updated_at": "2026-11-12T00:00:00Z",
    }


@pytest.fixture()
def store() -> CoreRecordStore:
    """Store isolé avec deux projets actifs et un inactif."""
    store = CoreRecordStore()
    _run(store.save("projects", "p-alpha", _project("p-alpha", name="Alpha")))
    _run(store.save("projects", "p-beta", _project("p-beta", name="Beta")))
    _run(store.save("projects", "p-archive", _project("p-archive", active=False)))
    _run(store.save("knowledge", "kn-1", _knowledge("kn-1", "Nœud")))
    _run(store.save("knowledge", "kn-libre", _knowledge("kn-libre", "Libre")))
    return store


@pytest.fixture()
def client(store: CoreRecordStore, monkeypatch):
    """Client API branché sur un service d'ancrage isolé."""
    projects_router.set_project_anchor_service(ProjectAnchorService(store))

    async def _user_record(username: str):
        return {"username": username, "roles": ["user"], "is_active": True}

    monkeypatch.setattr("interfaces.api.auth.fetch_user_record", _user_record)

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(projects_router.router)

    with TestClient(app) as test_client:
        yield test_client

    projects_router.set_project_anchor_service(None)


def _auth(role: str = "user", user_id: str = "alice") -> dict[str, str]:
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ── Délégation au Core ──────────────────────────────────────────────────


def test_attach_delegates_to_the_core_service(client):
    """La route d'écriture délègue au service Core et renvoie son ancre."""
    response = client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-1", "actor": "tester"},
        headers=_auth(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "p-alpha"
    assert body["target_id"] == "kn-1"
    assert body["actor"] == "tester"
    assert body["history"][-1]["target_existence"] == "verified"


def test_attach_is_idempotent_over_http(client):
    """Rattacher deux fois ne crée pas de seconde ancre."""
    payload = {"target_type": "knowledge_node", "target_id": "kn-1"}
    first = client.post("/v1/projects/p-alpha/anchors", json=payload, headers=_auth())
    second = client.post("/v1/projects/p-alpha/anchors", json=payload, headers=_auth())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["anchor_id"] == second.json()["anchor_id"]


def test_list_and_scope_routes_expose_the_core_result(client):
    """Les routes de lecture exposent le résultat du service Core."""
    client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-1"},
        headers=_auth(),
    )

    listed = client.get("/v1/projects/p-alpha/anchors", headers=_auth())
    scope = client.get(
        "/v1/projects/p-alpha/anchors/knowledge_node/kn-1/scope", headers=_auth()
    )

    assert listed.status_code == 200
    assert listed.json()["targets"] == ["kn-1"]
    assert scope.status_code == 200
    assert scope.json()["scope"] == "project"
    assert scope.json()["in_project"] is True


def test_detach_route_removes_the_anchor(client):
    """La route de détachement marque l'ancre sans supprimer la donnée."""
    client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-1"},
        headers=_auth(),
    )

    detached = client.delete(
        "/v1/projects/p-alpha/anchors/knowledge_node/kn-1", headers=_auth()
    )

    assert detached.status_code == 200
    assert detached.json()["detached"] is True
    scope = client.get(
        "/v1/projects/p-alpha/anchors/knowledge_node/kn-1/scope", headers=_auth()
    )
    assert scope.json()["scope"] == "global"


# ── Permissions HROT ────────────────────────────────────────────────────


def test_read_routes_require_the_read_permission(client):
    """Sans authentification, les routes de lecture sont refusées."""
    assert client.get("/v1/projects/p-alpha/anchors").status_code == 401
    assert (
        client.get("/v1/projects/p-alpha/anchors/knowledge_node/kn-1/scope").status_code
        == 401
    )


def test_write_routes_require_the_memory_permission(client):
    """Un rôle sans la permission MEMORY ne peut pas rattacher."""
    response = client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-1"},
        headers=_auth(role="viewer"),
    )

    assert response.status_code == 403
    assert "memory" in response.json()["detail"].lower()


def test_viewer_can_read_but_not_write(client):
    """Un rôle `viewer` lit les ancres sans pouvoir les modifier."""
    assert client.get("/v1/projects/p-alpha/anchors", headers=_auth(role="viewer")).status_code == 200
    assert (
        client.delete(
            "/v1/projects/p-alpha/anchors/knowledge_node/kn-1", headers=_auth(role="viewer")
        ).status_code
        == 403
    )


def test_user_with_memory_permission_can_attach(client):
    """Un rôle porteur de MEMORY peut attacher et détacher."""
    attached = client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-1"},
        headers=_auth(role="user"),
    )
    assert attached.status_code == 200

    detached = client.delete(
        "/v1/projects/p-alpha/anchors/knowledge_node/kn-1", headers=_auth(role="user")
    )
    assert detached.status_code == 200


# ── Traitement des erreurs ──────────────────────────────────────────────


def test_unknown_target_type_is_a_client_error(client):
    """Un type inconnu est une erreur du client (422)."""
    response = client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "inexistant", "target_id": "kn-1"},
        headers=_auth(),
    )

    assert response.status_code == 422
    assert "target_type" in response.json()["detail"]


def test_unknown_project_is_a_client_error(client):
    """Un projet inconnu est une règle métier (422), pas une panne."""
    response = client.post(
        "/v1/projects/p-inconnu/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-1"},
        headers=_auth(),
    )

    assert response.status_code == 422
    assert "not found" in response.json()["detail"].lower()


def test_missing_target_is_refused_over_http(client):
    """Une cible inexistante est refusée (422)."""
    response = client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-absent"},
        headers=_auth(),
    )

    assert response.status_code == 422
    assert "not found" in response.json()["detail"].lower()


def test_exclusive_conflict_is_a_client_error(client):
    """Le conflit d'exclusivité est une règle métier (422)."""
    client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "session", "target_id": "sess-1"},
        headers=_auth(),
    )

    conflict = client.post(
        "/v1/projects/p-beta/anchors",
        json={"target_type": "session", "target_id": "sess-1"},
        headers=_auth(),
    )

    assert conflict.status_code == 422
    assert "exclusive" in conflict.json()["detail"].lower()


def test_store_failure_is_a_server_error_not_a_missing_project(
    client, store: CoreRecordStore
):
    """Une panne du store produit un 503, jamais un « projet introuvable »."""

    class _BrokenStore(CoreRecordStore):
        async def get_strict(self, domain: str, record_id: str) -> dict[str, Any] | None:
            raise __import__(
                "core.state.record_store", fromlist=["RecordStoreUnavailable"]
            ).RecordStoreUnavailable("simulated failure")

    projects_router.set_project_anchor_service(ProjectAnchorService(_BrokenStore()))

    response = client.post(
        "/v1/projects/p-alpha/anchors",
        json={"target_type": "knowledge_node", "target_id": "kn-1"},
        headers=_auth(),
    )

    assert response.status_code == 503
    assert "indisponible" in response.json()["detail"].lower()


def test_detach_of_an_unknown_anchor_is_a_not_found(client):
    """Détacher une ancre inexistante renvoie 404."""
    response = client.delete(
        "/v1/projects/p-alpha/anchors/knowledge_node/kn-1", headers=_auth()
    )

    assert response.status_code == 404


def test_detach_with_invalid_identifiers_is_a_client_error(client):
    """Un identifiant vide est refusé par la validation (422)."""
    response = client.delete("/v1/projects/p-alpha/anchors/knowledge_node/", headers=_auth())

    assert response.status_code in (404, 422)


# ── Inventaire global ───────────────────────────────────────────────────


def test_global_inventory_distinguishes_empty_from_unavailable(client):
    """La route d'inventaire global expose la disponibilité de la source."""
    available = client.get(
        "/v1/projects/p-alpha/anchors/global?target_type=knowledge_node", headers=_auth()
    )
    unavailable = client.get(
        "/v1/projects/p-alpha/anchors/global?target_type=memory_record", headers=_auth()
    )

    assert available.status_code == 200
    assert available.json()["status"] == "ok"
    assert "kn-libre" in available.json()["targets"]

    assert unavailable.status_code == 200
    assert unavailable.json()["status"] == "unavailable"
    assert unavailable.json()["targets"] == []
    assert unavailable.json()["reason"]


def test_global_inventory_requires_read_permission(client):
    """L'inventaire global est protégé par la permission de lecture."""
    assert (
        client.get("/v1/projects/p-alpha/anchors/global?target_type=knowledge_node").status_code
        == 401
    )
