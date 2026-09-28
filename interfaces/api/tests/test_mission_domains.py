"""Tests du wiring Core → API des missions (routers/v1.py).

Les routes ``/v1/missions`` délèguent au ``MissionManager`` Core injecté via
``set_core_domain_services()`` — le router n'est qu'une passerelle HTTP, il ne
possède aucune logique ni aucun état métier (Première Loi d'ETHAN).

Le manager est observé DIRECTEMENT (store ``CoreRecordStore`` partagé) après
chaque appel router — aucun mock du domaine.  Non-régression : les routes
doivent lire le manager INJECTÉ, jamais une copie locale fantôme.
"""

from __future__ import annotations

import asyncio

import pytest
from core.missions import MissionManager, MissionStatus, StepStatus
from core.state import CoreRecordStore
from fastapi import HTTPException
from routers import v1


@pytest.fixture()
def wired():
    """MissionManager Core réel (store in-memory) injecté dans le router v1."""
    store = CoreRecordStore()
    manager = MissionManager(store=store)
    v1.set_core_domain_services(v1.CoreDomainServices(missions=manager))
    yield manager, store
    v1.set_core_domain_services(v1.CoreDomainServices())


def test_mission_lifecycle_is_delegated_to_the_core_manager(wired):
    """create → list → get → verify → approve → delete via les routes v1."""
    manager, store = wired

    created = asyncio.run(
        v1.create_mission(
            {"title": "Refactor API", "description": "Move CRUD", "steps": [{"title": "Step 1"}]}
        )
    )
    mission_id = created["id"]
    step_id = created["steps"][0]["id"]

    # La mission existe dans le store Core, pas seulement dans la réponse HTTP.
    assert asyncio.run(store.get("missions", mission_id)) is not None

    listed = asyncio.run(v1.list_missions())
    assert [m["id"] for m in listed] == [mission_id]

    fetched = asyncio.run(v1.get_mission(mission_id))
    assert fetched["title"] == "Refactor API"

    verified = asyncio.run(v1.verify_mission_step(mission_id, step_id))
    assert verified["verified"] is True
    waiting = asyncio.run(v1.get_mission(mission_id))
    assert waiting["steps"][0]["status"] == StepStatus.WAITING_APPROVAL.value

    asyncio.run(v1.approve_mission_step(mission_id, step_id))
    completed = asyncio.run(v1.get_mission(mission_id))
    assert completed["status"] == MissionStatus.COMPLETED.value
    assert completed["steps_completed"] == 1

    assert asyncio.run(v1.delete_mission(mission_id)) == {"status": "deleted"}
    assert asyncio.run(store.get("missions", mission_id)) is None


def test_mission_routes_read_the_injected_manager(wired):
    """Les routes lisent le manager INJECTÉ — aucun shadow manager local."""
    manager, _ = wired
    mission = asyncio.run(manager.create("Injected", steps=[{"title": "step"}]))

    listed = asyncio.run(v1.list_missions())
    assert [m["id"] for m in listed] == [mission.id]

    fetched = asyncio.run(v1.get_mission(mission.id))
    assert fetched["title"] == "Injected"


def test_mission_routes_surface_domain_errors_as_http(wired):
    """Erreurs domaine → HTTP : 404 mission inconnue, 422 titre vide."""
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.get_mission("ghost"))
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.create_mission({"title": "   "}))
    assert exc.value.status_code == 422

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.delete_mission("ghost"))
    assert exc.value.status_code == 404


def test_mission_list_filters_by_status(wired):
    """Le filtre ?status= est résolu par le Core (valeur inconnue → 422)."""
    manager, _ = wired
    asyncio.run(manager.create("Pending one", steps=[]))
    done = asyncio.run(manager.create("Done one", steps=[]))
    asyncio.run(manager.update(done.id, {"status": MissionStatus.COMPLETED.value}))

    pending = asyncio.run(v1.list_missions(status="pending"))
    assert [m["title"] for m in pending] == ["Pending one"]

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.list_missions(status="bogus"))
    assert exc.value.status_code == 422
