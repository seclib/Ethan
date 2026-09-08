"""Knowledge Import Router — passerelle HTTP vers le KnowledgeImportManager Core.

Endpoint d'import local-first :
  - POST /v1/knowledge/import     : 1 fichier (multipart)
  - POST /v1/knowledge/import-batch : N fichiers (multipart, multi-file)
  - GET  /v1/knowledge/imports/{job_id} : progression réelle du job

Le WebUI est un client passif : il envoie des octets et reçoit des résumés
(job_id + états).  Validation, extraction, chunking/embedding et memberships
appartiennent au Core ; aucun chemin absolu n'est accepté/renvoyé.
"""

from __future__ import annotations

from typing import Any

from core.auth import Permission
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/knowledge", tags=["knowledge-import"])

_import_manager: Any = None


def set_import_manager(manager: Any | None) -> None:
    global _import_manager
    _import_manager = manager


def _get_import_manager() -> Any:
    if _import_manager is None:
        raise HTTPException(503, "KnowledgeImportManager not initialized")
    return _import_manager


def _user_id(request: Request) -> str:
    payload = getattr(request.state, "token_payload", {})
    return payload.get("sub") or payload.get("user_id") or "anonymous"


async def _to_bytes(file: UploadFile) -> bytes:
    return await file.read()


@router.post(
    "/import",
    dependencies=[Depends(require_permission(Permission.WRITE))],
)
async def import_knowledge_file(
    request: Request,
    file: UploadFile = File(...),
    collection_id: str = Form(...),
):
    """Importe un fichier (multipart) vers une collection (job asynchrone)."""
    raw = await _to_bytes(file)
    if not raw:
        raise HTTPException(422, "Empty file")
    job_id = _get_import_manager().start_import(
        _user_id(request), [(file.filename or "unnamed", raw)], collection_id
    )
    return {"job_id": job_id, "collection_id": collection_id}


@router.post(
    "/import-batch",
    dependencies=[Depends(require_permission(Permission.WRITE))],
)
async def import_knowledge_batch(
    request: Request,
    collection_id: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """Importe plusieurs fichiers (dossier uploadé) vers une collection.

    ``files`` peut contenir des chemins relatifs (ex: ``subdir/file.md``) —
    conservés comme noms affichables, jamais résolus côté fichier système.
    """
    batch = [(f.filename or "unnamed", await _to_bytes(f)) for f in files]
    if not batch:
        raise HTTPException(422, "No files")
    job_id = _get_import_manager().start_import(
        _user_id(request), batch, collection_id
    )
    return {"job_id": job_id, "collection_id": collection_id, "count": len(batch)}


@router.get("/imports/{job_id}")
async def get_import_job(job_id: str, request: Request):
    """Progression réelle d'un import (owner-scoped)."""
    job = _get_import_manager().get_job(job_id, _user_id(request))
    if job is None:
        raise HTTPException(404, "Import job not found")
    return job