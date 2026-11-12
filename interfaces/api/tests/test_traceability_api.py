"""DAĒNĀ P2.8.3 — Routes API de traçabilité : tests ciblés.

Environnement isolé : corpus DAĒNĀ temporaire, store Core en mémoire,
gestionnaire de clés API en mémoire. Le corpus réel n'est jamais touché.

Couverture :
  - Contrôle d'accès HROT (portée machine + permission RBAC)
  - Enregistrement d'un rapport, d'une anomalie, d'une dette
  - Transition d'anomalie
  - Contrôle de fin d'intervention
  - Conflit d'identifiant (409) et échec de persistance (503)
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from core.auth.api_keys import APIKeyManager
from core.engineering_memory.service import EngineeringMemoryService
from core.engineering_memory.traceability import TraceabilityService
from core.state.record_store import CoreRecordStore
from fastapi import FastAPI
from fastapi.testclient import TestClient
from interfaces.api.auth import (
    auth_middleware,
    create_access_token,
    set_api_key_manager,
)
from interfaces.api.routers import engineering_memory as em_router

DAENA_DIRECTORIES = (
    "Archives/Events",
    "Archives/Rapports-Agents",
    "Knowledge/Composants",
    "Knowledge/Decisions",
    "Knowledge/Incidents",
    "Knowledge/Tests-et-Preuves",
    "Operational-Memory",
    "_meta",
)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    """Client API avec un corpus DAENA temporaire et une cle de service."""
    root = tmp_path / "daena"
    for directory in DAENA_DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)

    em = EngineeringMemoryService(root=root)
    em_router.set_traceability_service(
        TraceabilityService(em, fallback_dir=tmp_path / "fallback")
    )

    manager = APIKeyManager(store=CoreRecordStore())
    set_api_key_manager(manager)
    scoped_key = _run(
        manager.create_key(
            user_id="opencode-plugin",
            name="scoped",
            scopes=["memory:traceability"],
        )
    )["key"]
    unscoped_key = _run(
        manager.create_key(
            user_id="plain-client",
            name="unscoped",
            scopes=["plugins:autre"],
        )
    )["key"]

    async def _user_record(username: str):
        return {"username": username, "roles": ["admin"], "is_active": True}

    monkeypatch.setattr("interfaces.api.auth.fetch_user_record", _user_record)

    app = FastAPI()
    app.middleware("http")(auth_middleware)
    app.include_router(em_router.router)

    with TestClient(app) as test_client:
        test_client.scoped_key = scoped_key
        test_client.unscoped_key = unscoped_key
        yield test_client

    em_router.set_traceability_service(None)
    set_api_key_manager(None)


def _scoped(client) -> dict[str, str]:
    return {"Authorization": f"Bearer {client.scoped_key}"}


def _unscoped(client) -> dict[str, str]:
    return {"Authorization": f"Bearer {client.unscoped_key}"}


def _admin() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': 'admin', 'role': 'admin'})}"}


def _payload(**overrides):
    payload = {
        "intervention_id": "EVT-20261112T000000000000-API",
        "mission": "P2.8.3",
        "phase": "P2.8",
        "agent": "opencode",
        "nature": "feature",
        "validation_level": "TESTED",
        "context": "Contexte",
        "work_description": "Travaux realises via l'API",
        "files_modified": ["core/engineering_memory/traceability.py"],
        "tests": [
            {"name": "api", "command": "pytest -q", "passed": 1, "failed": 0, "result": "OK"}
        ],
        "remaining_work": ["rien"],
    }
    payload.update(overrides)
    return payload


# ── Controle d'acces HROT ─────────────────────────────────────────────


def test_les_routes_exigent_une_authentification(client):
    """Sans identite, aucune route de tracabilite n'est accessible."""
    assert client.post("/v1/memory/traceability/interventions", json=_payload()).status_code == 401
    assert client.get("/v1/memory/traceability/interventions").status_code == 401


def test_une_cle_sans_portee_est_refusee(client):
    """Une cle de service depourvue de la portee est refusee (403)."""
    response = client.post(
        "/v1/memory/traceability/interventions", json=_payload(), headers=_unscoped(client)
    )
    assert response.status_code == 403
    assert "memory:traceability" in response.json()["detail"]


def test_une_cle_avec_portee_est_acceptee(client):
    """La portee `memory:traceability` autorise l'ecriture."""
    response = client.post(
        "/v1/memory/traceability/interventions", json=_payload(), headers=_scoped(client)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["persisted"] is True
    assert body["status"] == "recorded"


def test_une_session_admin_est_acceptee(client):
    """Un role RBAC disposant de la permission `record` reste accepte."""
    response = client.post(
        "/v1/memory/traceability/interventions", json=_payload(), headers=_admin()
    )
    assert response.status_code == 201


# ── Cycle de vie documentaire ──────────────────────────────────────────


def test_le_rapport_est_relisible_et_listable(client):
    """Le rapport enregistre est relisible et present dans la liste."""
    client.post("/v1/memory/traceability/interventions", json=_payload(), headers=_scoped(client))

    read = client.get(
        "/v1/memory/traceability/interventions/EVT-20261112T000000000000-API",
        headers=_scoped(client),
    )
    assert read.status_code == 200
    body = read.json()
    assert body["id"] == "EVT-20261112T000000000000-API"
    assert body["structure"]["mission"] == "P2.8.3"
    assert body["structure"]["kind"] == "intervention"
    assert body["path"].endswith(".md")

    listed = client.get("/v1/memory/traceability/interventions", headers=_scoped(client))
    assert listed.status_code == 200
    assert any(item["id"] == "EVT-20261112T000000000000-API" for item in listed.json()["results"])


def test_anomalie_et_transition(client):
    """Une anomalie est enregistree, puis sa transition est tracee."""
    created = client.post(
        "/v1/memory/traceability/anomalies",
        json={
            "anomaly_id": "INC-2026-001-API",
            "description": "Anomalie via API",
            "component": "core.api",
            "severity": "LOW",
        },
        headers=_scoped(client),
    )
    assert created.status_code == 201
    assert created.json()["persisted"] is True

    transition = client.post(
        "/v1/memory/traceability/anomalies/INC-2026-001-API/transition",
        json={"state": "FIXED", "note": "corrigee", "actor": "opencode"},
        headers=_scoped(client),
    )
    assert transition.status_code == 201
    assert transition.json()["persisted"] is True


def test_un_etat_invalide_est_rejete(client):
    """Un état hors nomenclature est refusé (422)."""
    response = client.post(
        "/v1/memory/traceability/anomalies/INC-2026-001-API/transition",
        json={"state": "PEUT-ETRE"},
        headers=_scoped(client),
    )
    assert response.status_code == 422


def test_dette_technique(client):
    """Une dette technique est enregistree via l'API."""
    response = client.post(
        "/v1/memory/traceability/debts",
        json={
            "debt_id": "DEBT-2026-001-API",
            "description": "Dette via API",
            "priority": "LOW",
        },
        headers=_scoped(client),
    )
    assert response.status_code == 201
    assert response.json()["persisted"] is True


def test_une_identifiant_manquant_est_rejete(client):
    """Un identifiant d'anomalie absent est refusé (422)."""
    response = client.post(
        "/v1/memory/traceability/anomalies",
        json={"description": "sans identifiant"},
        headers=_scoped(client),
    )
    assert response.status_code == 422


def test_le_conflit_didentifiant_est_signale(client):
    """Un identifiant deja utilise avec un contenu different donne 409."""
    client.post("/v1/memory/traceability/interventions", json=_payload(), headers=_scoped(client))
    conflict = client.post(
        "/v1/memory/traceability/interventions",
        json=_payload(work_description="Contenu divergent"),
        headers=_scoped(client),
    )
    assert conflict.status_code == 409
    assert conflict.json()["conflict"] is True
    assert conflict.json()["persisted"] is False


def test_le_controle_de_fin_valide_les_huit_conditions(client):
    """Le controle de fin renvoie l'etat des huit conditions."""
    client.post("/v1/memory/traceability/interventions", json=_payload(), headers=_scoped(client))
    response = client.post(
        "/v1/memory/traceability/interventions/EVT-20261112T000000000000-API/complete",
        headers=_scoped(client),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["complete"] is True
    assert body["persisted"] is True
    assert len(body["checks"]) >= 8


def test_un_rapport_absent_nest_pas_declare_complet(client):
    """Le controle d'un rapport inexistant renvoie un echec explicite."""
    response = client.post(
        "/v1/memory/traceability/interventions/EVT-20261112T000000000000-ABSENT/complete",
        headers=_scoped(client),
    )
    assert response.status_code == 409
    body = response.json()
    assert body["complete"] is False
    assert body["persisted"] is False
