"""Logs Router — exposition des journaux de la pipeline logs/metrics Core.

Le Core possède toute la logique (core/telemetry, core/metrics/log_pipeline).
Ce router n'exporte que les endpoints HTTP et délègue à la service Core.

Routes :
    GET  /logs              → liste des logs récents (filtres: level, module)
    GET  /logs/count        → nombre total de logs par niveau
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/logs", tags=["logs"])

_service: "LogService" | None = None
logger = logging.getLogger(__name__)


def set_log_service(service: "LogService") -> None:
    """Enregistre le service de logs Core."""
    global _service
    _service = service


@router.get("")
async def list_logs(
    level: str | None = Query(None, description="Filtre par niveau (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    module: str | None = Query(None, description="Filtre par module d'origine"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximal de logs à retourner"),
):
    """Retourne les logs récents du journal Core."""
    if _service is None:
        raise HTTPException(503, "Log service not initialized")
    try:
        return await _service.list(level=level, module=module, limit=limit)
    except Exception as exc:  # noqa: BLE001
        logger.exception("List logs failed: %s", exc)
        raise HTTPException(500, f"Log listing failed: {exc}") from exc


@router.get("/count")
async def log_count():
    """Retourne le nombre total de logs par niveau."""
    if _service is None:
        raise HTTPException(503, "Log service not initialized")
    try:
        return _service.count()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Count logs failed: %s", exc)
        raise HTTPException(500, f"Log count failed: {exc}") from exc
