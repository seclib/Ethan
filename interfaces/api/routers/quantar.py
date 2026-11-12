"""Quantar router — MEM-014 Phase 36."""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from core.applications.quantar_service import quantar_service
from core.plugins.quantar import (
    STATE_ACTIVE,
    STATE_ERROR,
    STATE_STOPPED,
    STATE_UNKNOWN,
    get_quantar_service,
)
from core.plugins.quantar import (
    STATE_ACTIVE,
    STATE_ERROR,
    STATE_STOPPED,
    get_quantar_service,
)
from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/quantar", tags=["quantar"])


class PrepareAnalysisRequest(BaseModel):
    ticker: str
    analysis_date: str
    provider: str | None = None


@router.get("/status")
async def get_status(_: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    return quantar_service.status()


@router.get("/config")
async def get_config(_: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    return quantar_service.config()


@router.post("/analysis/prepare")
async def prepare_analysis(payload: PrepareAnalysisRequest, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.prepare_analysis(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analysis/start")
async def start_analysis(payload: PrepareAnalysisRequest, execute: bool = False, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        analysis = quantar_service.start_analysis(payload.model_dump(), execute=execute)
        return analysis
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.get_analysis(analysis_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}/results")
async def get_results(analysis_id: str, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.get_results(analysis_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analyses")
async def list_analyses(_: bool = Depends(require_permission(Permission.READ))) -> list[dict[str, Any]]:
    return quantar_service.list_analyses()


@router.get("/reports")
async def get_reports(_: bool = Depends(require_permission(Permission.READ)), analysis_id: str | None = None) -> list[dict[str, Any]]:
    try:
        return quantar_service.get_reports(analysis_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/lifecycle/status")
async def get_lifecycle_status(_: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    service = get_quantar_service()
    return await service.get_status()


@router.post("/lifecycle/start")
async def start_lifecycle(_: bool = Depends(require_permission(Permission.PLUGINS))) -> dict[str, Any]:
    service = get_quantar_service()
    res = await service.start()
    if res.get("status") not in (STATE_ACTIVE, "running"):
        err_msg = res.get("error") or "Erreur lors du démarrage du conteneur Quantar."
        raise HTTPException(status_code=503, detail=err_msg)
    return res


@router.post("/lifecycle/stop")
async def stop_lifecycle(_: bool = Depends(require_permission(Permission.PLUGINS))) -> dict[str, Any]:
    service = get_quantar_service()
    res = await service.stop()
    if res.get("status") not in (STATE_STOPPED, STATE_ERROR, "stopped"):
        raise HTTPException(status_code=503, detail=res.get("error") or "Erreur lors de l'arrêt du conteneur Quantar.")
    return res


class TaskRequest(BaseModel):
    ticker: str
    analysis_date: str
    provider: str | None = None
    metadata: dict[str, Any] | None = None
    task_id: str | None = None


@router.post("/tasks")
async def create_task(payload: TaskRequest, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.create_task(payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/start")
async def start_task(task_id: str, execute: bool = False, use_docker: bool = False, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        quantar_service.start_task(task_id, execute=False)
        if execute:
            return quantar_service.run_task(task_id, use_docker=use_docker)
        return quantar_service.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str, use_docker: bool = False, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.run_task(task_id, use_docker=use_docker)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, _: bool = Depends(require_permission(Permission.PLUGINS))) -> dict[str, Any]:
    try:
        return quantar_service.cancel_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str, tail: int = 100, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.get_logs(task_id, tail=tail)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str, _: bool = Depends(require_permission(Permission.READ))) -> dict[str, Any]:
    try:
        return quantar_service.get_result(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tasks")
async def list_tasks(_: bool = Depends(require_permission(Permission.READ))) -> list[dict[str, Any]]:
    return quantar_service.list_tasks()
