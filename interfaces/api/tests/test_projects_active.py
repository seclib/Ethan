"""Tests réels des routes GET/POST ``/v1/projects/active``.

Ces routes servent le sélecteur de projet de la WebUI : ``POST`` valide et
confirme la sélection, ``GET`` fournit le fallback « General (Default) ».
Les handlers sont appelés directement (pattern du dépôt) avec un vrai
``ProjectManager`` sur ``CoreRecordStore`` mémoire — aucun mock du domaine.

Régression couverte : ``get_active_project`` doit *awaiter*
``ProjectManager.get_project`` (coroutine), faute de quoi la route renvoyait
un objet coroutine au lieu du projet.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from core.projects import ProjectManager
from core.state import CoreRecordStore
from fastapi import HTTPException
from interfaces.api.routers import projects as projects_module
from interfaces.api.routers.projects import set_project_manager


def _request(user: str | None = "user-a") -> SimpleNamespace:
    """Stub minimal de ``Request`` : seuls ``request.state.user`` est lu."""
    return SimpleNamespace(state=SimpleNamespace(user=user))


@pytest.fixture()
def manager():
    """Vrai ProjectManager (CoreRecordStore mémoire) injecté dans le router."""
    mgr = ProjectManager(store=CoreRecordStore())
    set_project_manager(mgr)
    yield mgr
    set_project_manager(None)


def test_get_active_project_returns_project_dict(manager):
    """Le fallback renvoie le projet General sérialisable (pas une coroutine)."""
    project = asyncio.run(projects_module.get_active_project(_request("alice")))

    assert isinstance(project, dict)
    assert project["id"] == "general"
    assert project["user_id"] == "alice"


def test_set_active_project_accepts_own_project(manager):
    """Un utilisateur peut activer un projet qui lui appartient."""
    project = asyncio.run(manager.create_project(user_id="alice", name="Recon"))

    selection = asyncio.run(
        projects_module.set_active_project({"active_project_id": project["id"]}, _request("alice"))
    )
    assert selection == {"active_project_id": project["id"]}


def test_set_active_project_general_is_always_allowed(manager):
    """Le projet virtuel « general » est accepté sans exister en base."""
    selection = asyncio.run(
        projects_module.set_active_project({"active_project_id": "general"}, _request("alice"))
    )
    assert selection == {"active_project_id": "general"}


def test_set_active_project_rejects_foreign_project(manager):
    """Isolation : activer le projet d'un autre utilisateur → 404."""
    foreign = asyncio.run(manager.create_project(user_id="mallory", name="Secret"))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            projects_module.set_active_project(
                {"active_project_id": foreign["id"]}, _request("alice")
            )
        )
    assert exc.value.status_code == 404


@pytest.mark.parametrize(
    "payload", [None, {}, {"active_project_id": None}, {"active_project_id": "null"}]
)
def test_set_active_project_resets_selection(manager, payload):
    """Absence / null → réinitialisation vers le fallback général."""
    selection = asyncio.run(projects_module.set_active_project(payload, _request("alice")))
    assert selection == {"active_project_id": None}


def test_handlers_tolerate_missing_request(manager):
    """Appels directs sans ``Request`` : l'utilisateur retombe sur None."""
    selection = asyncio.run(projects_module.set_active_project({"active_project_id": "general"}))
    assert selection == {"active_project_id": "general"}
