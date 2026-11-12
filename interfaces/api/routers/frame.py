"""Frame router — passerelle HTTP dédiée et sécurisée.

Application indépendante Frame (fork HyperFrames), pilotée uniquement par
son cycle de vie Compose. Toute l'intelligence et la configuration restent
dans Frame; ETHAN n'expose que les opérations autorisées.
"""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from core.plugins.frame import (
    STATE_ACTIVE,
    STATE_ERROR,
    STATE_STOPPED,
    get_frame_service,
)
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/plugins/frame", tags=["frame"])


@router.get("/status")
async def get_status(
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    service = get_frame_service()
    return await service.get_status()


@router.post("/start")
async def start_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    service = get_frame_service()
    res = await service.start()
    if res.get("status") != STATE_ACTIVE:
        err_msg = res.get("error") or "Erreur lors du démarrage du conteneur Frames."
        if "Conflit de port" in str(err_msg):
            raise HTTPException(status_code=409, detail=err_msg)
        raise HTTPException(status_code=503, detail=err_msg)
    return res


@router.post("/stop")
async def stop_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    service = get_frame_service()
    res = await service.stop()
    if res.get("status") != STATE_STOPPED:
        raise HTTPException(
            status_code=503,
            detail=res.get("error") or "L'état arrêté de Frames n'a pas pu être vérifié.",
        )
    return res


@router.post("/restart")
async def restart_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    service = get_frame_service()
    res = await service.restart()
    if res.get("status") != STATE_ACTIVE:
        raise HTTPException(
            status_code=503,
            detail=res.get("error") or "Le démarrage de Frames n'a pas pu être vérifié.",
        )
    return res


@router.get("/logs")
async def get_logs(
    tail: int = 100,
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    service = get_frame_service()
    res = await service.get_logs(tail=tail)
    if not res.get("ok", False):
        raise HTTPException(
            status_code=500,
            detail=res.get("error") or "Erreur lors de la lecture des logs.",
        )
    return res


@router.get("/health")
async def get_health(
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    service = get_frame_service()
    return await service.get_health()


@router.post("/install")
async def install_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    service = get_frame_service()
    res = await service.install()
    if res.get("status") != STATE_ACTIVE:
        err_msg = res.get("error") or "Erreur lors du déploiement du conteneur Frames."
        if "Conflit de port" in str(err_msg):
            raise HTTPException(status_code=409, detail=err_msg)
        raise HTTPException(status_code=503, detail=err_msg)
    return res


@router.post("/uninstall")
async def uninstall_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    service = get_frame_service()
    res = await service.uninstall()
    if res.get("status") == STATE_ERROR:
        raise HTTPException(status_code=500, detail=res.get("error") or "Erreur de désinstallation de Frames.")
    return res


__all__ = ["router"]
