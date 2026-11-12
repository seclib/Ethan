"""God's Eye View router — passerelle HTTP dédiée et sécurisée.

Ce routeur expose UNIQUEMENT les opérations de cycle de vie contrôlées
pour l'application plugin God's Eye View :
- GET  /v1/plugins/gods-eye-view/status
- POST /v1/plugins/gods-eye-view/start
- POST /v1/plugins/gods-eye-view/stop
- POST /v1/plugins/gods-eye-view/restart

Règles de sécurité :
- Toutes les opérations passent par l'authentification et le RBAC.
- Aucune commande Docker arbitraire n'est exécutée depuis le client.
- Pas d'exposition du socket Docker au WebUI.
- Pas de démarrage automatique sans configuration explicite.
- Détection des conflits de ports locaux (port 4173).
"""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from core.plugins.gods_eye_view import STATE_ERROR, get_gods_eye_view_service
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/plugins/gods-eye-view", tags=["gods-eye-view"])


@router.get("/status")
async def get_status(
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    """Retourne l'état réel et vérifié de l'application God's Eye View."""
    service = get_gods_eye_view_service()
    return await service.get_status()


@router.post("/start")
async def start_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Démarre le service Docker Compose après vérification des conflits de ports."""
    service = get_gods_eye_view_service()
    res = await service.start()
    if res.get("status") == STATE_ERROR:
        err_msg = res.get("error") or "Erreur lors du démarrage du conteneur."
        # Si c'est un conflit de port, renvoyer HTTP 409 Conflict
        if "Conflit de port" in err_msg:
            raise HTTPException(status_code=409, detail=err_msg)
        raise HTTPException(status_code=500, detail=err_msg)
    return res


@router.post("/stop")
async def stop_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Arrête le service Docker Compose sans supprimer les données."""
    service = get_gods_eye_view_service()
    res = await service.stop()
    if res.get("status") == STATE_ERROR:
        raise HTTPException(status_code=500, detail=res.get("error") or "Erreur d'arrêt.")
    return res


@router.post("/restart")
async def restart_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Redémarre le conteneur du service."""
    service = get_gods_eye_view_service()
    res = await service.restart()
    if res.get("status") == STATE_ERROR:
        raise HTTPException(status_code=500, detail=res.get("error") or "Erreur de redémarrage.")
    return res


@router.get("/logs")
async def get_logs(
    tail: int = 100,
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    """Retourne les logs récents du service (tail limité, secrets redactés)."""
    service = get_gods_eye_view_service()
    res = await service.get_logs(tail=tail)
    if res.get("status") == "error":
        raise HTTPException(
            status_code=500,
            detail=res.get("error") or "Erreur lors de la lecture des logs.",
        )
    return res


@router.get("/health")
async def get_health(
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    """Vérification approfondie de l'état de santé du service (TCP + conteneur)."""
    service = get_gods_eye_view_service()
    return await service.get_health()


__all__ = ["router"]

