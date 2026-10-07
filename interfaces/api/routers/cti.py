"""HTTP gateway for the Core-owned ETHAN-CTI domain."""

from __future__ import annotations

from typing import Any

from core.auth import Permission
from core.cti import CTIError, CTIManager
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from interfaces.api.auth import current_user_id, require_permission

router = APIRouter(prefix="/v1/cti", tags=["cti"])
_manager: CTIManager | None = None


def set_cti_manager(manager: CTIManager | None) -> None:
    global _manager
    _manager = manager


def get_cti_manager() -> CTIManager:
    if _manager is None:
        raise HTTPException(status_code=503, detail="CTI manager not initialized")
    return _manager


def _owner_id(request: Request) -> str:
    owner_id = current_user_id(request)
    if not owner_id:
        raise HTTPException(status_code=401, detail="Authenticated user required")
    return owner_id


def _translate_error(error: CTIError) -> HTTPException:
    if "already exists" in str(error):
        return HTTPException(status_code=409, detail=str(error))
    if "not available" in str(error):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=422, detail=str(error))


@router.get("/manifest", dependencies=[Depends(require_permission(Permission.READ))])
async def get_manifest():
    return get_cti_manager().manifest()


@router.get("/status", dependencies=[Depends(require_permission(Permission.READ))])
async def get_status(request: Request):
    manager = get_cti_manager()
    owner_id = _owner_id(request)
    objects = await manager.list_objects(owner_id, limit=200)
    return {
        "status": "operational",
        "service": "ethan-cti",
        "model": "STIX 2.1",
        "object_count": len(objects),
        "object_count_limit": 200,
    }


@router.get("/objects", dependencies=[Depends(require_permission(Permission.READ))])
async def list_objects(
    request: Request,
    object_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
):
    objects = await get_cti_manager().list_objects(
        _owner_id(request), object_type=object_type, limit=limit
    )
    return {"items": objects, "count": len(objects)}


@router.get("/objects/{stix_id}", dependencies=[Depends(require_permission(Permission.READ))])
async def get_object(stix_id: str, request: Request):
    record = await get_cti_manager().get_object(_owner_id(request), stix_id)
    if record is None:
        raise HTTPException(status_code=404, detail="CTI object not found")
    return record


@router.post(
    "/objects",
    status_code=201,
    dependencies=[Depends(require_permission(Permission.WRITE))],
)
async def create_object(data: dict[str, Any], request: Request):
    try:
        return await get_cti_manager().create_object(_owner_id(request), data)
    except CTIError as exc:
        raise _translate_error(exc) from exc
