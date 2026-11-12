from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from interfaces.api.routers.engineering_memory import memory_read_permission, memory_record_permission, router


def test_engineering_memory_router_records_and_retrieves(tmp_path: Path) -> None:
    os.environ["ETHAN_ENGINEERING_MEMORY_ROOT"] = str(tmp_path / "Obsidian")
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[memory_read_permission] = lambda: True
    application.dependency_overrides[memory_record_permission] = lambda: True
    client = TestClient(application)
    payload = {
        "id": "EVT-2026-010",
        "record_type": "engineering_event",
        "title": "router test",
        "status": "RECORDED",
        "source_of_fact": "test router",
        "provenance_level": "observed",
        "components": ["CMP-memory-service"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_refs": [],
        "authors": ["pytest-agent"],
        "origin": "declared",
        "confidence": "low",
        "notes": "integration test",
    }

    response = client.post("/v1/memory/events", json=payload)
    assert response.status_code == 200
    assert response.json()["id"] == payload["id"]

    fetched = client.get("/v1/memory/events/EVT-2026-010")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "router test"

    health = client.get("/v1/memory/health")
    assert health.status_code == 200
    assert health.json()["valid_records"] == 1


def test_engineering_memory_router_rejects_invalid_event(tmp_path: Path) -> None:
    os.environ["ETHAN_ENGINEERING_MEMORY_ROOT"] = str(tmp_path / "Obsidian")
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[memory_read_permission] = lambda: True
    application.dependency_overrides[memory_record_permission] = lambda: True
    client = TestClient(application)
    payload = {
        "id": "bad-id",
        "record_type": "engineering_event",
        "title": "invalid",
        "status": "RECORDED",
        "source_of_fact": "test router",
        "provenance_level": "observed",
        "components": ["CMP-memory-service"],
        "created_at": "not-a-date",
        "updated_at": "not-a-date",
        "evidence_refs": [],
        "authors": ["pytest-agent"],
        "origin": "declared",
        "confidence": "low",
        "notes": "",
    }

    response = client.post("/v1/memory/events", json=payload)
    assert response.status_code == 422


def test_engineering_memory_router_requires_record_permission(tmp_path: Path) -> None:
    os.environ["ETHAN_ENGINEERING_MEMORY_ROOT"] = str(tmp_path / "Obsidian")
    application = FastAPI()
    application.include_router(router)
    client = TestClient(application)
    payload = {
        "id": "EVT-2026-011",
        "record_type": "engineering_event",
        "title": "unauthorized probe",
        "status": "RECORDED",
        "source_of_fact": "test router",
        "provenance_level": "observed",
        "components": ["CMP-memory-service"],
        "created_at": "2026-11-03T00:00:00+00:00",
        "updated_at": "2026-11-03T00:00:00+00:00",
        "evidence_refs": [],
        "authors": ["pytest-agent"],
        "origin": "declared",
        "confidence": "low",
        "notes": "",
    }
    response = client.post("/v1/memory/events", json=payload)
    assert response.status_code == 403


def test_engineering_memory_router_requires_read_permission(tmp_path: Path) -> None:
    os.environ["ETHAN_ENGINEERING_MEMORY_ROOT"] = str(tmp_path / "Obsidian")
    application = FastAPI()
    application.include_router(router)
    client = TestClient(application)
    response = client.get("/v1/memory/health")
    assert response.status_code == 403
