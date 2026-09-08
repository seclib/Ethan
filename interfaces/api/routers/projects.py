"""Projects Router — passerelle HTTP vers le ProjectManager Core.

Le Core possède toute la logique (projets = conteneur de conversations +
scope de ressources + contexte d'exécution) ; ce router n'ajoute aucune
règle métier.  Aucune ressource n'est dupliquée : les associations ne sont
que des identifiants.

Documents de projet : le router délègue au pipeline Core
(`core/rag/ingestion.py`) — le WebUI ne parse ni n'embede jamais.
"""

from __future__ import annotations

from typing import Any

# RBAC (Permission) vit dans core/auth ; la résolution du user_id JWT est
# effectuée par auth_middleware (interfaces.api.auth) qui stocke le username
# dans request.state.user et le payload JWT dans request.state.token_payload.
# Le Core reste découpé : le router API est le bon endroit pour ce helper.
from core.auth import Permission
from core.projects import ProjectManager
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/projects", tags=["projects"])

_project_manager: ProjectManager | None = None


def set_project_manager(manager: ProjectManager | None) -> None:
    global _project_manager
    _project_manager = manager


def get_project_manager() -> ProjectManager:
    if _project_manager is None:
        raise HTTPException(503, "ProjectManager not initialized")
    return _project_manager


def _current_user_id(request: Request) -> str | None:
    """Déduit l'utilisateur courant depuis le JWT déjà vérifié par auth_middleware.

    `auth_middleware` (interfaces.api.auth) a déjà validé le Bearer token / cookie
    et a stocké `request.state.user` (username = champ `sub` du JWT).
    Nécessite donc une authentification préalable (sauf pour GET /default).
    """
    return getattr(request.state, "user", None)


def _not_found(exc: ValueError) -> HTTPException:
    """Un id inexistant lève 404, une règle violée 422."""
    code = 404 if "not found" in str(exc).lower() else 422
    return HTTPException(code, str(exc))


_LISTS = ("folder_ids", "knowledge_ids", "collection_ids", "skill_ids", "tool_ids")


def _coerce(data: dict[str, Any]) -> dict[str, Any]:
    """Normalise les champs de type liste du payload (sécurisé)."""
    out: dict[str, Any] = {}
    for key in _LISTS:
        if key in data:
            value = data[key]
            out[key] = list(value) if value is not None else []
    return out


# ── Fallback « General (Default) » ─────────────────────────────────────


@router.get("/default")
async def get_default_project(request: Request):
    """Retourne le projet général (fallback — toujours disponible).

    N'exige pas de permissions : il sert d'entrée par défaut au sélecteur
    WebUI. Aucun projet n'est créé en base.
    """
    uid = _current_user_id(request)
    return get_project_manager().get_project("general", user_id=uid) or {}


# ── CRUD projects ──────────────────────────────────────────────────


@router.get("")
async def list_projects(request: Request):
    """Liste plate des projets visibles par l'utilisateur (triés par nom)."""
    uid = _current_user_id(request)
    return await get_project_manager().list_projects(user_id=uid)


@router.post("", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def create_project(request: Request, data: dict[str, Any]):
    """Crée un projet — aucun champ n'est imposé (nom requis)."""
    uid = _current_user_id(request)
    try:
        return await get_project_manager().create_project(
            name=data.get("name", ""),
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            user_id=uid or data.get("user_id", "anonymous"),
            agent_id=data.get("agent_id"),
            provider_id=data.get("provider_id"),
            model=data.get("model"),
            metadata=data.get("metadata"),
            folder_ids=data.get("folder_ids"),
            knowledge_ids=data.get("knowledge_ids"),
            collection_ids=data.get("collection_ids"),
            skill_ids=data.get("skill_ids"),
            tool_ids=data.get("tool_ids"),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.get("/{project_id}")
async def get_project(request: Request, project_id: str):
    uid = _current_user_id(request)
    project = await get_project_manager().get_project(project_id, user_id=uid)
    if project is None:
        raise HTTPException(404, f"Project {project_id} not found")
    return project


@router.patch(
    "/{project_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def update_project(request: Request, project_id: str, data: dict[str, Any]):
    """Mise à jour partielle : nom, description, instructions, ressources…"""
    uid = _current_user_id(request)
    try:
        project = await get_project_manager().update_project(project_id, uid, data)
    except ValueError as exc:
        raise _not_found(exc) from exc
    if project is None:
        raise HTTPException(404, f"Project {project_id} not found")
    return project


@router.delete(
    "/{project_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def delete_project(request: Request, project_id: str):
    """Supprime le conteneur — conversations et ressources restent intactes."""
    uid = _current_user_id(request)
    deleted = await get_project_manager().delete_project(project_id, user_id=uid)
    if not deleted:
        raise HTTPException(404, f"Project {project_id} not found")
    return {"status": "deleted", "project_id": project_id}


# ── Context (résolution pour le ChatPipeline) ────────────────────────


@router.get("/{project_id}/context")
async def project_context(project_id: str):
    """Contexte résolu du projet (agents, modèle, ressources) — lecture pure.

    `user_id` non requis : le contexte d'exécution (pour le Runtime) est
    indépendant du scope utilisateur.
    """
    context = await get_project_manager().resolve_context(project_id)
    if context is None:
        raise HTTPException(404, f"Project {project_id} not found")
    return context


# ── Documents du projet (délégation au pipeline Core) ─────────────────


@router.get("/{project_id}/documents")
async def list_project_documents(request: Request, project_id: str):
    """Liste les documents RAG rattachés au projet (scope utilisateur)."""
    uid = _current_user_id(request)
    try:
        docs = await get_project_manager().list_project_documents(project_id, user_id=uid)
    except ValueError as exc:
        raise _not_found(exc) from exc
    return docs


@router.post(
    "/{project_id}/documents",
    dependencies=[Depends(require_permission(Permission.FILES))],
)
async def upload_project_document(
    request: Request,
    project_id: str,
    file: UploadFile = File(...),
):
    """Upload un fichier dans le projet (multipart → pipeline Core).

    Le fichier est enregistré avec `status: processing` ; le pipeline RAG
    (core/rag/pipeline.py) se charge de l'extraction, du chunking et de
    l'embedding de manière asynchrone.
    """
    uid = _current_user_id(request)
    # Validation de la taille (50 Mo max — aligné sur web_ingest).
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 50 MB)")
    # Validation MIME (formats supportés par le pipeline Core).
    allowed = {
        "text/plain", "text/markdown", "text/csv", "application/json",
        "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword", "image/png", "image/jpeg", "image/webp",
    }
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(415, f"Unsupported file type: {file.content_type}")
    try:
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        doc = await get_project_manager().record_document_upload(
            project_id=project_id,
            file_id=tmp_path,
            filename=file.filename or "uploaded",
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents),
            user_id=uid,
            contents=contents,
        )
    except ValueError as exc:
        raise _not_found(exc) from exc
    return doc


@router.delete(
    "/{project_id}/documents/{doc_id}",
    dependencies=[Depends(require_permission(Permission.FILES))],
)
async def delete_project_document(request: Request, project_id: str, doc_id: str):
    """Supprime un document du projet (scope vérifié, 403 si hors scope)."""
    uid = _current_user_id(request)
    deleted = await get_project_manager().delete_project_document(
        project_id, doc_id, user_id=uid
    )
    if not deleted:
        raise HTTPException(404, f"Document {doc_id} not found in project {project_id}")
    return {"status": "deleted", "document_id": doc_id, "project_id": project_id}