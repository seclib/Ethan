"""Core Domains Router — passerelle HTTP vers le DomainManager Core.

Le Core possède toute la logique (domains de spécialité, memberships
many-to-many vers knowledge / collections RAG / skills / sources) ; ce
router n'ajoute aucune règle métier.  Aucune ressource n'est déplacée ou
dupliquée : le rattachement n'est qu'une relation.
"""

from __future__ import annotations

from typing import Any

from core.auth import Permission
from core.domains import DomainManager
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

router = APIRouter(prefix="/v1/domains", tags=["domains"])

_domain_manager: DomainManager | None = None


def set_domain_manager(manager: DomainManager | None) -> None:
    global _domain_manager
    _domain_manager = manager


def get_domain_manager() -> DomainManager:
    if _domain_manager is None:
        raise HTTPException(503, "DomainManager not initialized")
    return _domain_manager


def _not_found(exc: ValueError) -> HTTPException:
    """Un id inexistant lève 404, une règle violée 422."""
    code = 404 if "not found" in str(exc) else 422
    return HTTPException(code, str(exc))


# ── Lectures (déclarées avant /{domain_id} pour éviter les collisions) ──────


@router.get("")
async def list_domains(user_id: str | None = None):
    """Liste plate des domains, enrichie de ``resource_count``."""
    return await get_domain_manager().list_domains_with_counts(user_id=user_id)


@router.get("/index")
async def get_domain_index(resource_type: str):
    """Index batch ``{resource_id: [domain_id, ...]}`` (lecture pure)."""
    manager = get_domain_manager()
    index: dict[str, list[str]] = {}
    for domain in await manager.list_domains():
        for ref in await manager.list_resource_ids(domain["id"], resource_type):
            index.setdefault(ref["resource_id"], []).append(domain["id"])
    return index


@router.get("/by-resource/{resource_type}/{resource_id}")
async def list_domains_of_resource(resource_type: str, resource_id: str):
    """Domains contenant une ressource (multi-membership possible)."""
    return await get_domain_manager().list_domains_for_resource(
        resource_type, resource_id
    )


# ── CRUD domains ────────────────────────────────────────────────────────────


@router.post("", dependencies=[Depends(require_permission(Permission.MEMORY))])
async def create_domain(data: dict[str, Any]):
    """Crée un domain de spécialité (nom unique, librement choisi)."""
    try:
        return await get_domain_manager().create_domain(
            data.get("name", ""),
            description=data.get("description", ""),
            user_id=data.get("user_id", "anonymous"),
            icon=data.get("icon"),
            color=data.get("color"),
            order=int(data["order"]) if data.get("order") is not None else 0,
            metadata=data.get("metadata"),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc


@router.get("/{domain_id}")
async def get_domain(domain_id: str):
    domain = await get_domain_manager().get_domain(domain_id)
    if domain is None:
        raise HTTPException(404, f"Domain {domain_id} not found")
    return domain


@router.patch(
    "/{domain_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def update_domain(domain_id: str, data: dict[str, Any]):
    """Mise à jour partielle : nom, description, icône, couleur, ordre."""
    kwargs: dict[str, Any] = {}
    for key in ("name", "description", "icon", "color", "order", "metadata"):
        if key in data:
            kwargs[key] = data[key]
    try:
        domain = await get_domain_manager().update_domain(domain_id, **kwargs)
    except ValueError as exc:
        raise _not_found(exc) from exc
    if domain is None:
        raise HTTPException(404, f"Domain {domain_id} not found")
    return domain


@router.delete(
    "/{domain_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def delete_domain(domain_id: str):
    """Supprime un domain — les ressources rattachées ne sont pas supprimées."""
    deleted = await get_domain_manager().delete_domain(domain_id)
    if deleted is None:
        raise HTTPException(404, f"Domain {domain_id} not found")
    return {"status": "deleted", **deleted}


# ── memberships (relation domain ↔ ressource) ──────────────────────────────


@router.post(
    "/{domain_id}/resources",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def attach_resource(domain_id: str, data: dict[str, Any]):
    """Rattache une ressource à un domain (idempotent, relation pure)."""
    try:
        membership = await get_domain_manager().attach_resource(
            domain_id,
            data.get("resource_type", ""),
            data.get("resource_id", ""),
        )
    except ValueError as exc:
        raise _not_found(exc) from exc
    return membership


@router.delete(
    "/{domain_id}/resources/{resource_type}/{resource_id}",
    dependencies=[Depends(require_permission(Permission.MEMORY))],
)
async def detach_resource(domain_id: str, resource_type: str, resource_id: str):
    """Détache une ressource d'un domain (la ressource reste intacte)."""
    detached = await get_domain_manager().detach_resource(
        domain_id, resource_type, resource_id
    )
    if not detached:
        raise HTTPException(404, "Resource not attached to this domain")
    return {
        "status": "detached",
        "domain_id": domain_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
    }


@router.get("/{domain_id}/resources")
async def list_domain_resources(domain_id: str, resource_type: str | None = None):
    """Ressources réelles du domain, résolues par les managers Core."""
    try:
        return await get_domain_manager().list_resources(domain_id, resource_type)
    except ValueError as exc:
        raise _not_found(exc) from exc
