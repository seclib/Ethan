"""Tests réels du endpoint GET /internal/audit/search.

Utilise un vrai ``AuditStore`` (ring buffer mémoire + JSONL temporaire) et
journalise de vraies entrées avant d'interroger le endpoint via TestClient.
Aucune logique mockée : la recherche testée est celle du Core.

Couvre : correspondance action/acteur/details, ordre récent→ancien, liste
vide, validation du paramètre q (422), module non initialisé (503 — régression
du bug « tuple (dict, 503) » sérialisé en 200).
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import pytest

from core.audit import AuditStore
from interfaces.api.routers import internal as internal_router


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """App FastAPI minimale + AuditStore réel isolé dans tmp_path."""
    store = AuditStore(pg_conn=None, jsonl_path=tmp_path / "audit.jsonl")
    # Journalisation réelle d'entrées hétérogènes.
    store.log(
        category="security", decision="allowed",
        action="auth.login.success", actor="alice",
        source="webui", details={"ip": "10.0.0.5"},
        correlation_id="corr-1",
    )
    store.log(
        category="security", decision="denied",
        action="auth.login.failed", actor="mallory",
        source="webui", details={"reason": "bad password"},
        correlation_id="corr-2",
    )
    store.log(
        category="system", decision="auto",
        action="config.updated", actor="root",
        source="runtime", details={"section": "providers"},
    )
    monkeypatch.setattr(internal_router, "_audit", store)

    app = FastAPI()
    app.include_router(internal_router.router)
    with TestClient(app) as c:
        yield c
    monkeypatch.setattr(internal_router, "_audit", None)


def test_search_by_action(client):
    r = client.get("/internal/audit/search", params={"q": "auth.login"})
    assert r.status_code == 200
    entries = r.json()
    assert len(entries) == 2
    # Tri récent → ancien.
    assert entries[0]["action"] == "auth.login.failed"
    assert entries[1]["action"] == "auth.login.success"
    # Forme to_dict complète.
    assert set(entries[0]) >= {
        "id", "timestamp", "category", "decision", "action",
        "actor", "source", "details", "correlation_id",
    }
    assert entries[0]["category"] == "security"
    assert entries[0]["decision"] == "denied"


def test_search_by_actor_and_details(client):
    r1 = client.get("/internal/audit/search", params={"q": "mallory"})
    assert [e["action"] for e in r1.json()] == ["auth.login.failed"]

    # Recherche dans details (pas dans action/actor/source).
    r2 = client.get("/internal/audit/search", params={"q": "providers"})
    assert [e["action"] for e in r2.json()] == ["config.updated"]


def test_search_case_insensitive(client):
    r = client.get("/internal/audit/search", params={"q": "CONFIG.UPD"})
    assert [e["action"] for e in r.json()] == ["config.updated"]


def test_search_no_match(client):
    r = client.get("/internal/audit/search", params={"q": "inexistant-xyz"})
    assert r.status_code == 200
    assert r.json() == []


def test_search_requires_q(client):
    # q manquant → 422.
    assert client.get("/internal/audit/search").status_code == 422
    # q vide (min_length=1) → 422.
    assert client.get(
        "/internal/audit/search", params={"q": ""}
    ).status_code == 422


def test_search_module_not_initialized(monkeypatch):
    """Régression : module absent doit lever 503, pas sérialiser un tuple."""
    monkeypatch.setattr(internal_router, "_audit", None)
    app = FastAPI()
    app.include_router(internal_router.router)
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/internal/audit/search", params={"q": "x"})
    assert r.status_code == 503
    assert "not initialized" in r.json()["detail"]
