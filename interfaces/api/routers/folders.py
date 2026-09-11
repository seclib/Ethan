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


# ── Consolidation (opérations explicites, rapport Core) ─────────────────────


@router.post(
    "/merge",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def merge_folders(data: dict[str, Any]):
    """Fusionne le contenu de plusieurs dossiers vers une cible.

    Body: ``{folder_ids: [...], target_id, remove_sources?: bool}``.
    Les ressources sont re-classées (jamais dupliquées, jamais écrasées) ;
    les sources ne sont supprimées que si ``remove_sources`` est explicite.
    Retourne un rapport : operation_id, status, attached, skipped,
    removed_sources, errors (partiels jamais masqués).
    """
    try:
        return await get_folder_manager().merge_folders(
            list(data.get("folder_ids") or []),
            str(data.get("target_id", "")),
            remove_sources=bool(data.get("remove_sources", False)),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/copy-resources",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def copy_resources_to_folder(data: dict[str, Any]):
    """Copy logique de plusieurs ressources vers un dossier cible.

    Body: ``{items: [{resource_type, resource_id}, ...], target_id}``.
    Les classifications existantes sont conservées (multi-membership) ;
    l'original n'est jamais retiré ni modifié.
    """
    try:
        return await get_folder_manager().copy_resources_to_folder(
            list(data.get("items") or []),
            str(data.get("target_id", "")),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/move-resources",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def move_resources_to_folder(data: dict[str, Any]):
    """Move logique de plusieurs ressources vers un dossier cible.

    Body: ``{items: [{resource_type, resource_id}, ...], target_id}``.
    La cible devient l'unique dossier de chaque ressource (detach des
    autres) ; la ressource n'est jamais supprimée physiquement.
    """
    try:
        return await get_folder_manager().move_resources_to_folder(
            list(data.get("items") or []),
            str(data.get("target_id", "")),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/{folder_id}/to-collection",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def folder_to_collection(
    folder_id: str,
    data: dict[str, Any] | None = None,
):
    """Convertit un dossier en collection Knowledge (pipeline officiel).

    Body optionnel : ``{description?, user_id?}``.  Crée une collection
    portant le nom du dossier, rattache le dossier à la collection et
    attache les ressources ``knowledge`` classées dans le dossier à la
    collection.  Aucune ré-indexation ni copie physique.
    """
    data = data or {}
    try:
        return await get_folder_manager().folder_to_collection(
            folder_id,
            description=str(data.get("description", "")),
            user_id=str(data.get("user_id", "anonymous")),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


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


# ── Restore / Corbeille ───────────────────────────────────────────────────────


@router.get("/deleted", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def list_deleted_items(user_id: str | None = None):
    """Liste les éléments soft-deletés (corbeille)."""
    return await get_folder_manager().list_deleted_items(user_id)


@router.post(
    "/deleted/{deleted_id}/restore",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def restore_item(deleted_id: str, data: dict[str, Any] | None = None):
    """Restaure un élément supprimé."""
    data = data or {}
    try:
        await get_folder_manager().restore_item(deleted_id, user_id=data.get("user_id"))
    except ValueError as exc:
        raise _not_found(exc) from exc
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    return {"status": "restored", "id": deleted_id}


@router.delete("/deleted/empty", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def empty_trash(data: dict[str, Any] | None = None):
    """Purgé définitif de la corbeille."""
    data = data or {}
    count = await get_folder_manager().empty_trash(user_id=data.get("user_id"))
    return {"status": "emptied", "count": count}


# ── Archive Consolidé ─────────────────────────────────────────────────────────


@router.post(
    "/archive",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def create_archive(data: dict[str, Any]):
    """Planifie la création d'une archive consolidée depuis des dossiers."""
    try:
        return await get_folder_manager().create_archive(
            name=str(data.get("name", "")),
            folder_ids=list(data.get("folder_ids") or []),
            fmt=str(data.get("format", "zip")),
            compression_level=int(data.get("compression_level", 6)),
            include_metadata=bool(data.get("include_metadata", True)),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.get(
    "/archive/{archive_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def get_archive_status(archive_id: str):
    """Retourne le statut d'une archive (polling async)."""
    # TODO : connecter à folder-archives store une fois le worker d'archive implémenté
    # (placeholder pour l'instant — le créateur reçoit déjà le statut `pending`)
    return {
        "id": archive_id,
        "name": "",
        "path": "",
        "status": "pending",
        "file_count": 0,
        "size_bytes": 0,
        "created_at": "",
        "format": "zip",
    }
