"""Diagnostics Router — exposition HTTP du service Core de diagnostic.

Le Core possède toute la logique (``core/diagnostics``) : ce router ne fait
que composer les dépendances réelles du lifespan et déléguer. Aucune donnée
fictive, aucune logique métier ici.

Routes :
    GET /diagnostics          → rapport de santé réel (12 composants)
    GET /diagnostics/metrics  → métriques système réelles (CPU, RAM, GPU…)
"""

from __future__ import annotations

import logging

from core.auth import Permission
from core.diagnostics import SystemDiagnostics, SystemMetrics
from fastapi import APIRouter, Depends, HTTPException, Query
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

_service: SystemDiagnostics | None = None
_metrics: SystemMetrics | None = None


def set_diagnostics_service(service: SystemDiagnostics) -> None:
    global _service
    _service = service


def set_metrics_service(service: SystemMetrics) -> None:
    global _metrics
    _metrics = service


@router.get("", dependencies=[Depends(require_permission(Permission.READ))])
async def run_diagnostics(
    components: str | None = Query(
        None, description="Sous-ensemble séparé par des virgules (ex: nats,providers)"
    ),
):
    """Rapport de diagnostic réel — chaque check interroge le composant vrai."""
    if _service is None:
        raise HTTPException(503, "Diagnostics service not initialized")
    wanted = [c.strip() for c in components.split(",")] if components else None
    try:
        return await _service.run(wanted)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Diagnostics run failed: %s", exc)
        raise HTTPException(500, f"Diagnostics failed: {exc}") from exc


@router.get("/metrics", dependencies=[Depends(require_permission(Permission.READ))])
async def get_metrics(
    docker: bool = Query(True, description="Inclure docker stats (peut prendre ~1s)"),
):
    """Métriques système réelles — sections indisponibles explicites."""
    if _metrics is None:
        raise HTTPException(503, "Metrics service not initialized")
    try:
        return _metrics.collect(include_docker=docker)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Metrics collect failed: %s", exc)
        raise HTTPException(500, f"Metrics failed: {exc}") from exc


__all__ = [
    "router",
    "set_diagnostics_service",
    "set_metrics_service",
]
