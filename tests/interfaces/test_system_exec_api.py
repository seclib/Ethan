"""Tests HTTP du routeur system-exec — passerelle mince, pas de logique.

Matrice : 401 sans token, 403 viewer sur POST, catalogue fermé
(`docker_socket_granted is False`), 202 + PENDING_APPROVAL + corrélation
approbation, 422 commande/args/cwd, 404 opération inconnue, 503 sans service, isolation
demandeur (bob ne lit pas l'opération d'alice).

Le service Core est réel (pas de mock métier) avec un catalogue de test
restreint ; le catalogue de production reste lecture seule.
"""

from __future__ import annotations

import os
import secrets

import pytest

# L'auth refuse de démarrer sans secret : même convention que contract_kit.py.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))

from core.approval import ApprovalEngine  # noqa: E402
from core.audit import AuditStore  # noqa: E402
from core.system_exec import SystemExecService  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from interfaces.api.auth import auth_middleware, create_access_token  # noqa: E402
from interfaces.api.routers import system_exec as system_exec_router  # noqa: E402


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setattr("core.system_exec.service.os.geteuid", lambda: 1000)
    svc = SystemExecService(
        root=str(tmp_path),
        approval_engine=ApprovalEngine(),
        audit_store=AuditStore(),
        command_validators={"echo": lambda args: args == ["hello"]},
    )
    system_exec_router.set_system_exec_service(svc)
    yield svc
    system_exec_router.set_system_exec_service(None)


@pytest.fixture
def client(service):
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(system_exec_router.router)
    with TestClient(app) as test_client:
        yield test_client


def _auth(role: str = "admin", user_id: str = "alice") -> dict[str, str]:
    token = create_access_token({"sub": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_catalogue_requires_authentication(client):
    assert client.get("/v1/system/exec/catalogue").status_code == 401


def test_catalogue_is_closed_and_docker_denied(client):
    body = client.get("/v1/system/exec/catalogue", headers=_auth()).json()
    entries = {item["command"]: item for item in body["commands"]}
    assert entries["echo"]["docker_socket_granted"] is False
    assert entries["echo"]["requires_approval"] is True


def test_create_requires_execute_permission(client):
    denied = client.post(
        "/v1/system/exec/operations",
        headers=_auth("viewer"),
        json={"command": "echo", "args": ["hello"]},
    )
    assert denied.status_code == 403


def test_create_returns_pending_approval(client):
    created = client.post(
        "/v1/system/exec/operations",
        headers=_auth(),
        json={"command": "echo", "args": ["hello"]},
    )
    assert created.status_code == 202
    body = created.json()
    assert body["status"] == "PENDING_APPROVAL"
    assert body["approval_correlation_id"] == body["id"]
    assert body["actor"] == "alice"


def test_unknown_command_args_and_cwd_are_rejected(client):
    assert (
        client.post(
            "/v1/system/exec/operations",
            headers=_auth(),
            json={"command": "sh", "args": ["-c", "id"]},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/system/exec/operations",
            headers=_auth(),
            json={"command": "echo", "args": ["bye"]},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/system/exec/operations",
            headers=_auth(),
            json={"command": "echo", "args": ["hello"], "cwd": "../../etc"},
        ).status_code
        == 422
    )


def test_unknown_operation_is_not_found(client):
    assert (
        client.get("/v1/system/exec/operations/exec_ghost", headers=_auth()).status_code
        == 404
    )


def test_operations_are_private_to_the_requester(client):
    created = client.post(
        "/v1/system/exec/operations",
        headers=_auth(),
        json={"command": "echo", "args": ["hello"]},
    ).json()
    assert (
        client.get(
            f"/v1/system/exec/operations/{created['id']}",
            headers=_auth(user_id="bob"),
        ).status_code
        == 403
    )


def test_uninitialized_service_is_unavailable():
    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(system_exec_router.router)
    system_exec_router.set_system_exec_service(None)
    try:
        with TestClient(app) as lonely:
            response = lonely.get("/v1/system/exec/catalogue", headers=_auth())
            assert response.status_code == 503
    finally:
        system_exec_router.set_system_exec_service(None)
