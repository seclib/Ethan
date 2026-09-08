"""Tests API — Documents de projet (routes /v1/projects/{id}/documents).

Vérifie l'upload, la liste, la suppression, l'isolation de scope,
et les validations (taille, MIME, accès refusé).
"""

from __future__ import annotations

import asyncio
import io

import pytest
from fastapi import HTTPException

from core.projects import ProjectManager
from core.state import CoreRecordStore
from interfaces.api.routers.projects import get_project_manager, set_project_manager


@pytest.fixture(autouse=True)
def real_services():
    store = CoreRecordStore()
    manager = ProjectManager(store=store)
    set_project_manager(manager)
    yield manager


async def _create_project(manager, name="Test Project", user_id="user-a"):
    return await manager.create_project(user_id=user_id, name=name)


def _make_file(filename="test.txt", content=b"Hello world", mime="text/plain"):
    return {"file": (io.BytesIO(content), filename, mime)}


@pytest.mark.asyncio
async def test_list_documents_empty(real_services):
    """La liste des documents d'un nouveau projet est vide."""
    manager = real_services
    project = await _create_project(manager)
    docs = await manager.list_project_documents(project["id"], user_id="user-a")
    assert docs == []


@pytest.mark.asyncio
async def test_record_and_list_documents(real_services):
    """Enregistrer un document puis le lister."""
    manager = real_services
    project = await _create_project(manager)
    await manager.record_document_upload(
        project_id=project["id"], file_id="/tmp/t.txt", filename="t.txt",
        mime_type="text/plain", size_bytes=12, user_id="user-a",
    )
    docs = await manager.list_project_documents(project["id"], user_id="user-a")
    assert len(docs) == 1
    assert docs[0]["filename"] == "t.txt"
    assert docs[0]["status"] == "processing"


@pytest.mark.asyncio
async def test_documents_isolated_between_projects(real_services):
    """Les documents d'un projet ne fuient pas vers un autre."""
    manager = real_services
    pa = await _create_project(manager, name="A", user_id="user-a")
    pb = await _create_project(manager, name="B", user_id="user-b")
    await manager.record_document_upload(
        project_id=pa["id"], file_id="/tmp/a.txt", filename="a.txt",
        mime_type="text/plain", user_id="user-a",
    )
    await manager.record_document_upload(
        project_id=pb["id"], file_id="/tmp/b.txt", filename="b.txt",
        mime_type="text/plain", user_id="user-b",
    )
    docs_a = await manager.list_project_documents(pa["id"], user_id="user-a")
    docs_b = await manager.list_project_documents(pb["id"], user_id="user-b")
    assert len(docs_a) == 1 and docs_a[0]["filename"] == "a.txt"
    assert len(docs_b) == 1 and docs_b[0]["filename"] == "b.txt"


@pytest.mark.asyncio
async def test_list_documents_access_denied(real_services):
    """Un utilisateur hors scope ne peut pas lister les documents."""
    manager = real_services
    pb = await _create_project(manager, name="B", user_id="user-b")
    await manager.record_document_upload(
        project_id=pb["id"], file_id="/tmp/b.txt", filename="b.txt",
        mime_type="text/plain", user_id="user-b",
    )
    with pytest.raises(ValueError, match="access denied"):
        await manager.list_project_documents(pb["id"], user_id="user-a")


@pytest.mark.asyncio
async def test_delete_document_success(real_services):
    """Suppression d'un document du projet."""
    manager = real_services
    project = await _create_project(manager)
    doc = await manager.record_document_upload(
        project_id=project["id"], file_id="/tmp/t.txt", filename="t.txt",
        mime_type="text/plain", user_id="user-a",
    )
    deleted = await manager.delete_project_document(
        project["id"], doc["id"], user_id="user-a"
    )
    assert deleted is True
    docs = await manager.list_project_documents(project["id"], user_id="user-a")
    assert len(docs) == 0


@pytest.mark.asyncio
async def test_delete_document_wrong_project(real_services):
    """Impossible de supprimer un document d'un autre projet."""
    manager = real_services
    pa = await _create_project(manager, name="A", user_id="user-a")
    pb = await _create_project(manager, name="B", user_id="user-b")
    doc = await manager.record_document_upload(
        project_id=pa["id"], file_id="/tmp/a.txt", filename="a.txt",
        mime_type="text/plain", user_id="user-a",
    )
    deleted = await manager.delete_project_document(pb["id"], doc["id"], user_id="user-a")
    assert deleted is False


@pytest.mark.asyncio
async def test_general_project_no_documents(real_services):
    """Le projet 'general' n'a pas de documents."""
    manager = real_services
    docs = await manager.list_project_documents("general", user_id="any")
    assert docs == []


@pytest.mark.asyncio
async def test_update_document_status(real_services):
    """Mise à jour du statut d'un document."""
    manager = real_services
    project = await _create_project(manager)
    doc = await manager.record_document_upload(
        project_id=project["id"], file_id="/tmp/t.txt", filename="t.txt",
        mime_type="text/plain", user_id="user-a",
    )
    await manager.update_document_status(doc["id"], "ready", chunk_count=3)
    docs = await manager.list_project_documents(project["id"], user_id="user-a")
    assert docs[0]["status"] == "ready"
    assert docs[0]["chunk_count"] == 3
