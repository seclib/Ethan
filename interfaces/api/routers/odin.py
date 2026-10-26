"""Odin router — passerelle HTTP dédiée et sécurisée.

Ce routeur expose UNIQUEMENT les opérations de cycle de vie contrôlées
pour l'application plugin Odin :
- GET  /v1/plugins/odin/status
- POST /v1/plugins/odin/start
- POST /v1/plugins/odin/stop
- POST /v1/plugins/odin/restart
- GET  /v1/plugins/odin/logs
- GET  /v1/plugins/odin/health
- POST /v1/plugins/odin/install
- POST /v1/plugins/odin/uninstall

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
from core.plugins.odin import (
    STATE_ACTIVE,
    STATE_DEGRADED,
    STATE_ERROR,
    STATE_STOPPED,
    get_odin_service,
)
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/plugins/odin", tags=["odin"])


@router.get("/status")
async def get_status(
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    """Retourne l'état réel et vérifié de l'application Odin."""
    service = get_odin_service()
    return await service.get_status()


@router.post("/start")
async def start_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Démarre le service Docker Compose après vérification des conflits de ports."""
    service = get_odin_service()
    res = await service.start()
    if res.get("status") != STATE_ACTIVE:
        err_msg = res.get("error") or (
            "Odin n'a pas passé sa sonde de santé."
            if res.get("status") == STATE_DEGRADED
            else "Erreur lors du démarrage du conteneur."
        )
        if "Conflit de port" in err_msg:
            raise HTTPException(status_code=409, detail=err_msg)
        raise HTTPException(status_code=503, detail=err_msg)
    return res


@router.post("/stop")
async def stop_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Arrête le service Docker Compose sans supprimer les données."""
    service = get_odin_service()
    res = await service.stop()
    if res.get("status") != STATE_STOPPED:
        raise HTTPException(
            status_code=503,
            detail=res.get("error") or "L'état arrêté d'Odin n'a pas pu être vérifié.",
        )
    return res


@router.post("/restart")
async def restart_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Redémarre le conteneur du service."""
    service = get_odin_service()
    res = await service.restart()
    if res.get("status") != STATE_ACTIVE:
        raise HTTPException(
            status_code=503,
            detail=res.get("error") or "Le démarrage d'Odin n'a pas pu être vérifié.",
        )
    return res


@router.get("/logs")
async def get_logs(
    tail: int = 100,
    _: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    """Retourne les logs récents du service (tail limité, secrets redactés)."""
    service = get_odin_service()
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
    service = get_odin_service()
    return await service.get_health()


@router.post("/install")
async def install_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Déploie le service Odin via docker compose up -d si non déjà actif."""
    service = get_odin_service()
    res = await service.install()
    if res.get("status") != STATE_ACTIVE:
        err_msg = res.get("error") or "Erreur lors du déploiement du conteneur."
        if "Conflit de port" in err_msg:
            raise HTTPException(status_code=409, detail=err_msg)
        raise HTTPException(status_code=503, detail=err_msg)
    return res


@router.post("/uninstall")
async def uninstall_service(
    _: bool = Depends(require_permission(Permission.PLUGINS)),
) -> dict[str, Any]:
    """Désinstalle le service Odin : arrêt et retrait des conteneurs."""
    service = get_odin_service()
    res = await service.uninstall()
    if res.get("status") == STATE_ERROR:
        raise HTTPException(status_code=500, detail=res.get("error") or "Erreur de désinstallation.")
    return res


# ── Routeur de compatibilité temporaire (GEV -> Odin) ────────────────────
legacy_router = APIRouter(
    prefix="/v1/plugins/gods-eye-view",
    tags=["gods-eye-view-deprecated"],
    deprecated=True,
)


@legacy_router.get("/status")
async def legacy_get_status(_: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    logger.warning("Déprécié : /v1/plugins/gods-eye-view/status utilisé. Migrer vers /v1/plugins/odin/status.")
    return await get_status(_)


@legacy_router.post("/start")
async def legacy_start_service(_: bool = Depends(require_permission(Permission.PLUGINS))) -> dict[str, Any]:
    logger.warning("Déprécié : /v1/plugins/gods-eye-view/start utilisé. Migrer vers /v1/plugins/odin/start.")
    return await start_service(_)


@legacy_router.post("/stop")
async def legacy_stop_service(_: bool = Depends(require_permission(Permission.PLUGINS))) -> dict[str, Any]:
    logger.warning("Déprécié : /v1/plugins/gods-eye-view/stop utilisé. Migrer vers /v1/plugins/odin/stop.")
    return await stop_service(_)


@legacy_router.post("/restart")
async def legacy_restart_service(_: bool = Depends(require_permission(Permission.PLUGINS))) -> dict[str, Any]:
    logger.warning("Déprécié : /v1/plugins/gods-eye-view/restart utilisé. Migrer vers /v1/plugins/odin/restart.")
    return await restart_service(_)


@legacy_router.get("/logs")
async def legacy_get_logs(tail: int = 100, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    logger.warning("Déprécié : /v1/plugins/gods-eye-view/logs utilisé. Migrer vers /v1/plugins/odin/logs.")
    return await get_logs(tail=tail, _=_)


@legacy_router.get("/health")
async def legacy_get_health(_: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    logger.warning("Déprécié : /v1/plugins/gods-eye-view/health utilisé. Migrer vers /v1/plugins/odin/health.")
    return await get_health(_)


__all__ = ["router", "legacy_router"]
