"""Folders Router — passerelle HTTP vers le FolderManager Core.

Le Core possède toute la logique (dossiers, arborescence, relations
multi-ressources) ; ce router n'ajoute aucune règle métier.  Les ressources
classées (knowledge, collections RAG, skills) restent possédées par leurs
managers Core d'origine — le classement n'est qu'une relation.
"""

from __future__ import annotations

from typing import Any

from core.auth import Permission
from core.folders import FolderManager
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/folders", tags=["folders"])

_folder_manager: FolderManager | None = None


def set_folder_manager(manager: FolderManager | None) -> None:
    global _folder_manager
    _folder_manager = manager


def get_folder_manager() -> FolderManager:
    if _folder_manager is None:
        raise HTTPException(503, "FolderManager not initialized")
    return _folder_manager


def _not_found(exc: ValueError) -> HTTPException:
    """Un id inexistant lève 404, une règle violée 422."""
    code = 404 if "not found" in str(exc) else 422
    return HTTPException(code, str(exc))


# ── Lectures (déclarées avant /{folder_id} pour éviter les collisions) ──────


@router.get("/tree")
async def list_folders_tree(
    user_id: str | None = None, collection_id: str | None = None
):
    """Arborescence des dossiers ; ``collection_id`` restreint la vue aux
    dossiers associés à cette collection (ancêtres conservés pour le fil
    d'Ariane)."""
    return await get_folder_manager().list_tree(
        user_id=user_id, collection_id=collection_id
    )


@router.get("/untagged")
async def list_untagged_resources(resource_type: str):
    """Ressources d'un type classées dans aucun dossier."""
    try:
        return await get_folder_manager().list_untagged(resource_type)
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.get("/index")
async def get_folder_index(resource_type: str | None = None):
    """Index batch ``{resource_id: [folder_id, ...]}`` pour filtrer les
    listes de ressources par dossier (lecture pure, aucune duplication)."""
    try:
        return await get_folder_manager().folder_index(resource_type)
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.get("/by-resource/{resource_type}/{resource_id}")
async def list_folders_of_resource(resource_type: str, resource_id: str):
    """Dossiers contenant une ressource (multi-membership possible)."""
    try:
        return await get_folder_manager().list_resource_folders(
            resource_type, resource_id
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/move-resource",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def move_resource_between_folders(data: dict[str, Any]):
    """Déplace une ressource vers l'ensemble de dossiers donné (remplacement)."""
    try:
        folder_ids = await get_folder_manager().move_resource(
            data.get("resource_type", ""),
            data.get("resource_id", ""),
            list(data.get("folder_ids") or []),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc
    return {
        "resource_type": data.get("resource_type"),
        "resource_id": data.get("resource_id"),
        "folder_ids": folder_ids,
    }


# ── CRUD dossiers ───────────────────────────────────────────────────────────


@router.post("", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def create_folder(data: dict[str, Any]):
    """Crée un dossier nommé librement (aucune catégorie imposée)."""
    try:
        return await get_folder_manager().create_folder(
            data.get("name", ""),
            description=data.get("description", ""),
            user_id=data.get("user_id", "anonymous"),
            parent_id=data.get("parent_id"),
            collection_id=data.get("collection_id"),
            icon=data.get("icon"),
            order=int(data["order"]) if data.get("order") is not None else 0,
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.get("/{folder_id}")
async def get_folder(folder_id: str):
    folder = await get_folder_manager().get_folder(folder_id)
    if folder is None:
        raise HTTPException(404, f"Folder {folder_id} not found")
    return folder


@router.patch(
    "/{folder_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def update_folder(folder_id: str, data: dict[str, Any]):
    """Mise à jour partielle : rename, description, icône, ordre, parent."""
    kwargs: dict[str, Any] = {}
    for key in (
        "name", "description", "icon", "order", "parent_id", "collection_id",
        "metadata",
    ):
        if key in data:
            kwargs[key] = data[key]
    try:
        folder = await get_folder_manager().update_folder(folder_id, **kwargs)
    except ValueError as exc:
        raise _not_found(exc) from exc
    if folder is None:
        raise HTTPException(404, f"Folder {folder_id} not found")
    return folder


@router.post(
    "/{folder_id}/move",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def move_folder(folder_id: str, data: dict[str, Any]):
    """Re-parente un dossier (``parent_id: null`` → racine, cycles rejetés)."""
    try:
        folder = await get_folder_manager().move_folder(
            folder_id, data.get("parent_id")
        )
    except ValueError as exc:
        raise _not_found(exc) from exc
    if folder is None:
        raise HTTPException(404, f"Folder {folder_id} not found")
    return folder


@router.delete(
    "/{folder_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def delete_folder(folder_id: str):
    """Supprime un dossier (les ressources ne sont pas supprimées)."""
    result = await get_folder_manager().delete_folder(folder_id)
    if result is None:
        raise HTTPException(404, f"Folder {folder_id} not found")
    return {"status": "deleted", **result}


# ── Classement des ressources ───────────────────────────────────────────────


@router.get("/{folder_id}/resources")
async def list_folder_resources(folder_id: str, resource_type: str | None = None):
    """Ressources réellement classées dans un dossier (résolues via Core)."""
    try:
        return await get_folder_manager().list_folder_resources(
            folder_id, resource_type
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/{folder_id}/resources",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def attach_resource(folder_id: str, data: dict[str, Any]):
    """Classe une ressource dans un dossier (idempotent, multi-membership)."""
    try:
        return await get_folder_manager().attach_resource(
            folder_id, data.get("resource_type", ""), data.get("resource_id", "")
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.delete(
    "/{folder_id}/resources/{resource_type}/{resource_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def detach_resource(folder_id: str, resource_type: str, resource_id: str):
    """Retire une ressource d'un dossier (sans supprimer la ressource)."""
    try:
        deleted = await get_folder_manager().detach_resource(
            folder_id, resource_type, resource_id
        )
    except ValueError as exc:
        raise _not_found(exc) from exc
    if not deleted:
        raise HTTPException(404, "Resource not classified in this folder")
    return {"status": "detached"}
