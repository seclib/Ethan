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
from core.projects.anchors import (
    AnchorScope,
    AnchorTargetType,
    ProjectAnchorError,
    ProjectAnchorService,
    ProjectAnchorStoreUnavailable,
)
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from interfaces.api.auth import authenticated_user_id, require_permission

router = APIRouter(prefix="/v1/projects", tags=["projects"])

_project_manager: ProjectManager | None = None
_anchor_service: ProjectAnchorService | None = None


def set_project_manager(manager: ProjectManager | None) -> None:
    global _project_manager
    _project_manager = manager


def get_project_manager() -> ProjectManager:
    if _project_manager is None:
        raise HTTPException(503, "ProjectManager not initialized")
    return _project_manager


def set_project_anchor_service(service: ProjectAnchorService | None) -> None:
    """Branche le service d'ancrage projet (Core-owned)."""
    global _anchor_service
    _anchor_service = service


def get_project_anchor_service() -> ProjectAnchorService:
    """Retourne le service d'ancrage projet."""
    if _anchor_service is None:
        raise HTTPException(503, "ProjectAnchorService not initialized")
    return _anchor_service


def _current_user_id(request: Request | None) -> str | None:
    """Déduit l'utilisateur courant depuis le JWT déjà vérifié par auth_middleware.

    `auth_middleware` (interfaces.api.auth) a déjà validé le Bearer token / cookie
    et a stocké `request.state.user` (username = champ `sub` du JWT).
    Nécessite donc une authentification préalable (sauf pour GET /default).
    Retourne ``None`` si ``request`` est ``None`` (appels directs des tests).
    """
    if request is None:
        return None
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
    uid = authenticated_user_id(request)
    return get_project_manager().get_project("general", user_id=uid) or {}


# ── CRUD projects ──────────────────────────────────────────────────


@router.get("")
async def list_projects(request: Request):
    """Liste plate des projets visibles par l'utilisateur (triés par nom)."""
    uid = authenticated_user_id(request)
    return await get_project_manager().list_projects(user_id=uid)


@router.post("", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def create_project(request: Request, data: dict[str, Any]):
    """Crée un projet — aucun champ n'est imposé (nom requis)."""
    uid = authenticated_user_id(request)
    try:
        return await get_project_manager().create_project(
            name=data.get("name", ""),
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            user_id=uid,
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


@router.get("/active", dependencies=[Depends(require_permission(Permission.READ))])
async def get_active_project(request: Request):
    """Retourne le projet couramment actif (fallback « General (Default) »).

    Le sélecteur WebUI appelle ``POST /active`` pour changer la sélection ; ce
    GET sert de fallback côté serveur lorsqu'aucun projet n'est encore actif.
    """
    uid = authenticated_user_id(request)
    project = await get_project_manager().get_project("general", user_id=uid)
    return project or {}


@router.post("/active", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def set_active_project(data: dict[str, Any] | None = None, request: Request = None):
    """Confirme la sélection de projet active côté serveur.

    Reçoit ``{ active_project_id }`` depuis la WebUI et valide l'accès au projet
    avant de le renvoyer. Le cookie de sélection est géré par l'interface.
    """
    data = data or {}
    uid = authenticated_user_id(request)
    project_id = data.get("active_project_id")
    if project_id is None or project_id == "null":
        # Réinit vers le fallback général
        return {"active_project_id": None}
    project = await get_project_manager().get_project(project_id, user_id=uid)
    if project is None and project_id != "general":
        raise HTTPException(404, f"Project {project_id} not found")
    return {"active_project_id": project_id}


@router.get("/{project_id}")
async def get_project(request: Request, project_id: str):
    uid = authenticated_user_id(request)
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
    uid = authenticated_user_id(request)
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
    uid = authenticated_user_id(request)
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



# ── Project Anchors (P2.8.2) ───────────────────────────────────────────
# Passerelle HTTP : toute la logique d'ancrage vit dans le Core
# (core/projects/anchors.py). Le router ne fait que valider, deleguer et
# projeter.
#
# Deux natures d'erreur sont distinguees : une regle metier violee est une
# erreur du client (422), une indisponibilite du store est une erreur
# serveur (503). Une panne technique ne doit jamais etre presentee comme un
# « projet introuvable ».


def _anchor_http_error(exc: Exception) -> HTTPException:
    """Traduit une erreur du service d'ancrage en reponse HTTP.

    Args:
        exc: Erreur levee par le service Core.

    Returns:
        Exception HTTP correspondant.
    """
    if isinstance(exc, ProjectAnchorStoreUnavailable):
        return HTTPException(
            status_code=503,
            detail="Le service d'ancrage est momentanement indisponible.",
        )
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/{project_id}/anchors", dependencies=[Depends(require_permission(Permission.READ))])
async def list_project_anchors(project_id: str, target_type: str | None = None):
    """Liste les donnees ancrees a un projet."""
    service = get_project_anchor_service()
    try:
        kind = AnchorTargetType(target_type) if target_type else None
    except ValueError as exc:
        raise HTTPException(422, f"unknown target_type: {target_type}") from exc
    try:
        targets = await service.targets_for_project(project_id, kind)
    except (ProjectAnchorError, ProjectAnchorStoreUnavailable) as exc:
        raise _anchor_http_error(exc) from exc
    return {"project_id": project_id, "target_type": target_type, "targets": targets}


@router.get(
    "/{project_id}/anchors/global",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def list_global_anchors(project_id: str, target_type: str = "knowledge_node"):
    """Liste les donnees de portee globale d'un type donne.

    La reponse distingue une liste **reellement vide** d'un inventaire
    **indisponible** : renvoyer une liste vide dans les deux cas ferait
    croire a tort qu'aucune donnee n'existe.
    """
    service = get_project_anchor_service()
    try:
        payload = await service.global_inventory(target_type)
    except (ProjectAnchorError, ProjectAnchorStoreUnavailable) as exc:
        raise _anchor_http_error(exc) from exc
    return {"project_id": project_id, **payload}


@router.post(
    "/{project_id}/anchors",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def attach_project_anchor(project_id: str, payload: dict[str, Any]):
    """Rattache une donnee a un projet (idempotent)."""
    service = get_project_anchor_service()
    try:
        kind = AnchorTargetType(payload.get("target_type", ""))
    except ValueError as exc:
        raise HTTPException(422, f"unknown target_type: {payload.get('target_type')}") from exc
    target_id = str(payload.get("target_id", ""))
    try:
        anchor = await service.attach(
            kind,
            target_id,
            project_id,
            actor=str(payload.get("actor", "")),
            metadata=payload.get("metadata"),
        )
    except (ProjectAnchorError, ProjectAnchorStoreUnavailable) as exc:
        raise _anchor_http_error(exc) from exc
    return anchor.to_dict()


@router.delete(
    "/{project_id}/anchors/{target_type}/{target_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def detach_project_anchor(
    project_id: str, target_type: str, target_id: str, actor: str = ""
):
    """Detache une donnee d'un projet sans supprimer la donnee."""
    service = get_project_anchor_service()
    try:
        kind = AnchorTargetType(target_type)
    except ValueError as exc:
        raise HTTPException(422, f"unknown target_type: {target_type}") from exc
    try:
        detached = await service.detach(kind, target_id, project_id, actor=actor)
    except (ProjectAnchorError, ProjectAnchorStoreUnavailable) as exc:
        raise _anchor_http_error(exc) from exc
    if not detached:
        raise HTTPException(404, "anchor not found")
    return {"detached": True, "project_id": project_id, "target_id": target_id}


@router.get(
    "/{project_id}/anchors/{target_type}/{target_id}/scope",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def project_anchor_scope(project_id: str, target_type: str, target_id: str):
    """Retourne la portee projet d'une donnee (global / project / multi_project)."""
    service = get_project_anchor_service()
    try:
        kind = AnchorTargetType(target_type)
    except ValueError as exc:
        raise HTTPException(422, f"unknown target_type: {target_type}") from exc
    try:
        scope = await service.scope_for(kind, target_id)
        projects = await service.projects_for(kind, target_id)
    except (ProjectAnchorError, ProjectAnchorStoreUnavailable) as exc:
        raise _anchor_http_error(exc) from exc
    return {
        "target_type": kind.value,
        "target_id": target_id,
        "scope": scope.value,
        "project_ids": projects,
        "in_project": project_id in projects,
    }


# ── Documents du projet (délégation au pipeline Core) ─────────────────


@router.get("/{project_id}/documents")
async def list_project_documents(request: Request, project_id: str):
    """Liste les documents RAG rattachés au projet (scope utilisateur)."""
    uid = authenticated_user_id(request)
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
    uid = authenticated_user_id(request)
    # Validation de la taille (50 Mo max — aligné sur web_ingest).
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 50 MB)")
    # Validation MIME (formats supportés par le pipeline Core).
    allowed = {
        "text/plain",
        "text/markdown",
        "text/csv",
        "application/json",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "image/png",
        "image/jpeg",
        "image/webp",
    }
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(415, f"Unsupported file type: {file.content_type}")
    try:
        import tempfile

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
    uid = authenticated_user_id(request)
    deleted = await get_project_manager().delete_project_document(project_id, doc_id, user_id=uid)
    if not deleted:
        raise HTTPException(404, f"Document {doc_id} not found in project {project_id}")
    return {"status": "deleted", "document_id": doc_id, "project_id": project_id}
