"""MCP Installer router — thin HTTP gateway to the Core `McpInstaller`.

Aucune logique métier ici : l'analyse, l'approbation HROT, l'installation
isolée et l'enregistrement restent dans ``core.mcp_installer`` et
``ToolServerManager``. Ce routeur ne fait que traduire REST → Core.
"""

from __future__ import annotations

from typing import Annotated

from core.auth import Permission
from core.mcp_installer import McpInstaller, McpInstallError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from interfaces.api.auth import current_user_id, require_permission
from pydantic import BaseModel, ConfigDict, Field, model_validator

router = APIRouter(prefix="/v1/mcp/installer", tags=["mcp-installer"])
# Phase 2 : endpoint partagé /v1/mcp/analyze (même Core, même politique)
shared_router = APIRouter(prefix="/v1/mcp", tags=["mcp-installer"])

_installer: McpInstaller | None = None


def set_mcp_installer(installer: McpInstaller | None) -> None:
    global _installer
    _installer = installer


def get_mcp_installer() -> McpInstaller:
    if _installer is None:
        raise HTTPException(503, "MCP installer is not initialized")
    return _installer


def _http_error(exc: McpInstallError) -> HTTPException:
    if exc.code == "MCP-NOT-FOUND":
        return HTTPException(404, detail={"code": exc.code, "message": str(exc)})
    return HTTPException(400, detail={"code": exc.code, "message": str(exc)})


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Annotated[str, Field(min_length=1, max_length=2048)]


class InstallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Annotated[str | None, Field(default=None, max_length=2048)]
    analysis_id: Annotated[str | None, Field(default=None, max_length=64)]
    confirmed_mcp: bool = False
    replaces: Annotated[str | None, Field(default=None, max_length=64)]

    @model_validator(mode="after")
    def _require_source(self) -> InstallRequest:
        if not self.source and not self.analysis_id:
            raise ValueError("source ou analysis_id requis")
        return self


class UpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed_mcp: bool = True


@router.post("/analyze", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def analyze_installer(body: AnalyzeRequest):
    """Analyse une source sans rien installer (lecture seule)."""
    try:
        return await get_mcp_installer().analyze(body.source)
    except McpInstallError as exc:
        raise _http_error(exc) from exc


@shared_router.post("/analyze", dependencies=[Depends(require_permission(Permission.ADMIN))])
async def analyze(body: AnalyzeRequest):
    """Analyse une source sans rien installer (lecture seule) — Phase 2.

    Expose le contrat partagé : source, projet, plan d'installation, statut
    d'identification (confirmé/probable/indéterminé/non-MCP/invalide) avec
    preuves. Aucun code tiers n'est installé, lancé ou exécuté.
    """
    try:
        return await get_mcp_installer().analyze(body.source)
    except McpInstallError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/install",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission(Permission.ADMIN))],
)
async def request_install(body: InstallRequest, request: Request):
    """Crée une demande HROT ; l'installation démarre après approbation."""
    try:
        return await get_mcp_installer().request_install(
            actor=current_user_id(request) or "unknown",
            source=body.source,
            analysis_id=body.analysis_id,
            confirmed_mcp=body.confirmed_mcp,
            replaces=body.replaces,
        )
    except McpInstallError as exc:
        raise _http_error(exc) from exc


@router.get("/installations", dependencies=[Depends(require_permission(Permission.READ))])
async def list_installations(include_removed: bool = False):
    return await get_mcp_installer().list(include_removed=include_removed)


@router.get(
    "/installations/{installation_id}",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def get_installation(installation_id: str):
    record = await get_mcp_installer().get(installation_id)
    if record is None:
        raise HTTPException(
            404, detail={"code": "MCP-NOT-FOUND", "message": "installation inconnue"}
        )
    return record


@router.get(
    "/installations/{installation_id}/update-check",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def check_update(installation_id: str):
    try:
        return await get_mcp_installer().check_update(installation_id)
    except McpInstallError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/installations/{installation_id}/update",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission(Permission.ADMIN))],
)
async def request_update(
    installation_id: str, body: UpdateRequest, request: Request
):
    """Met à jour via une nouvelle installation approuvée, puis retire l'ancienne."""
    try:
        return await get_mcp_installer().request_update(
            installation_id,
            actor=current_user_id(request) or "unknown",
            confirmed_mcp=body.confirmed_mcp,
        )
    except McpInstallError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/installations/{installation_id}/cancel",
    dependencies=[Depends(require_permission(Permission.ADMIN))],
)
async def cancel_installation(installation_id: str):
    try:
        record = await get_mcp_installer().cancel(installation_id)
    except McpInstallError as exc:
        raise _http_error(exc) from exc
    return record


@router.delete(
    "/installations/{installation_id}",
    dependencies=[Depends(require_permission(Permission.ADMIN))],
)
async def uninstall(installation_id: str, request: Request):
    """Désenregistre le serveur et supprime son isolation (jamais hors racine)."""
    try:
        return await get_mcp_installer().uninstall(
            installation_id, actor=current_user_id(request) or "unknown"
        )
    except McpInstallError as exc:
        raise _http_error(exc) from exc
