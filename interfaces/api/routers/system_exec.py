"""Thin HTTP bridge for the Core controlled system-command capability."""

from __future__ import annotations

from typing import Annotated

from core.auth import Permission
from core.system_exec import (
    DEFAULT_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,
    SystemExecDenied,
    SystemExecError,
    SystemExecNotFound,
    SystemExecService,
    SystemExecValidationError,
)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from interfaces.api.auth import current_user_id, require_permission
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/system/exec", tags=["system-exec"])

_service: SystemExecService | None = None


def set_system_exec_service(service: SystemExecService | None) -> None:
    global _service
    _service = service


def get_system_exec_service() -> SystemExecService:
    if _service is None:
        raise HTTPException(503, "Controlled system execution is not initialized")
    return _service


class CreateOperation(BaseModel):
    command: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]*$")]
    args: list[Annotated[str, Field(max_length=256)]] = Field(default_factory=list, max_length=32)
    cwd: str | None = Field(default=None, max_length=512)
    timeout_seconds: float = Field(default=DEFAULT_TIMEOUT_SECONDS, gt=0, le=MAX_TIMEOUT_SECONDS)


def _http_error(exc: SystemExecError) -> HTTPException:
    if isinstance(exc, SystemExecNotFound):
        return HTTPException(404, detail={"code": exc.code, "message": str(exc)})
    if isinstance(exc, SystemExecValidationError):
        return HTTPException(422, detail={"code": exc.code, "message": str(exc)})
    if isinstance(exc, SystemExecDenied):
        return HTTPException(403, detail={"code": exc.code, "message": str(exc)})
    return HTTPException(500, detail={"code": exc.code, "message": "system execution failed"})


@router.get("/catalogue")
async def catalogue(_: bool = Depends(require_permission(Permission.READ))):
    """The fixed command catalogue, not an inventory of host executables."""
    return {"commands": get_system_exec_service().catalogue()}


@router.post("/operations", status_code=status.HTTP_202_ACCEPTED)
async def create_operation(
    body: CreateOperation,
    request: Request,
    _: bool = Depends(require_permission(Permission.EXECUTE)),
):
    """Request an approved command; execution begins only after human approval."""
    try:
        operation = get_system_exec_service().submit(
            actor=current_user_id(request) or "unknown",
            command=body.command,
            args=body.args,
            cwd=body.cwd,
            timeout_seconds=body.timeout_seconds,
        )
    except SystemExecError as exc:
        raise _http_error(exc) from exc
    return operation.to_dict()


@router.get("/operations/{operation_id}")
async def get_operation(
    operation_id: str,
    request: Request,
    _: bool = Depends(require_permission(Permission.EXECUTE)),
):
    try:
        return (
            get_system_exec_service()
            .get(operation_id, actor=current_user_id(request) or "unknown")
            .to_dict()
        )
    except SystemExecError as exc:
        raise _http_error(exc) from exc


@router.post("/operations/{operation_id}/cancel")
async def cancel_operation(
    operation_id: str,
    request: Request,
    _: bool = Depends(require_permission(Permission.EXECUTE)),
):
    try:
        operation = await get_system_exec_service().cancel(
            operation_id, actor=current_user_id(request) or "unknown"
        )
    except SystemExecError as exc:
        raise _http_error(exc) from exc
    return operation.to_dict()


__all__ = ["get_system_exec_service", "router", "set_system_exec_service"]
