"""Router API — Discoverable application catalogue (MEM-014 Phase 41+)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.applications import (
    ApplicationCatalog,
    CatalogSource,
    ApplicationIntegrationRegistry,
)
from core.applications.capability_contract import (
    ApplicationCapabilityContract,
    ApplicationCapabilityRegistration,
    get_application_capability_contracts,
    register_application_capability,
)
from core.applications.capability_execution import (
    TRUSTED_IMPLEMENTATION_ALIASES,
    bind_capability_implementation,
    activate_capability_binding,
    invoke_capability,
)
try:
    from core.plugins.odin import get_odin_service
    from core.plugins.frame import get_frame_service
except Exception:
    get_odin_service = None
    get_frame_service = None

try:
    from core.plugins.odin import get_odin_service
    from core.plugins.frame import get_frame_service
except Exception:
    get_odin_service = None
    get_frame_service = None
try:
    from interfaces.api.routers.local_repositories import _APPLICATION_REGISTRY
except Exception:
    _APPLICATION_REGISTRY = None
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from interfaces.api.auth import require_permission
from core.auth import ExecutionContext, Permission
from core.applications.models import ValidationError

def _application_integration_registry():
    global _APPLICATION_REGISTRY
    if _APPLICATION_REGISTRY is None:
        _APPLICATION_REGISTRY = ApplicationIntegrationRegistry()
    return _APPLICATION_REGISTRY

router = APIRouter(prefix="/v1", tags=["applications"])

_APPLICATION_ROOT = Path(__file__).resolve().parents[3] / "examples"


def _discover_catalog_roots() -> list[tuple[CatalogSource, Path]]:
    explicit = __import__("os").environ.get("ETHAN_APPLICATIONS_ROOT")
    candidates = [Path(explicit)] if explicit else [_APPLICATION_ROOT]
    roots: list[tuple[CatalogSource, Path]] = []
    for base in candidates:
        if not base.exists():
            continue
        manifests = [base / "ethan-application-manifest.yaml"] + sorted(base.glob("*/ethan-application-manifest.yaml"))
        if (base / "ethan-application-manifest.yaml").is_file():
            roots.append((CatalogSource.BUILTIN if base == _APPLICATION_ROOT else CatalogSource.LOCAL_EXAMPLE, base))
        for manifest in sorted(base.glob("*/ethan-application-manifest.yaml")):
            roots.append((CatalogSource.LOCAL_EXAMPLE, manifest.parent))
    if not roots and _APPLICATION_ROOT.exists():
        roots.append((CatalogSource.LOCAL_EXAMPLE, _APPLICATION_ROOT))
    return roots


_CATALOGS: list[ApplicationCatalog] | None = None


def _application_catalogs() -> list[ApplicationCatalog]:
    global _CATALOGS
    if _CATALOGS is None:
        _CATALOGS = []
        for source, path in _discover_catalog_roots():
            _CATALOGS.append(ApplicationCatalog(roots={source: path}, recursive=False))
    return _CATALOGS


def _application_entries():
    entries = []
    for catalog in _application_catalogs():
        entries.extend(catalog.entries())
    return entries


def _find_application(app_id: str):
    for catalog in _application_catalogs():
        found = catalog.find(app_id)
        if found is not None:
            return found
    return None


def _refresh_catalogs():
    for catalog in _application_catalogs():
        catalog.refresh()


@router.get("/applications", dependencies=[Depends(require_permission(Permission.READ))])
async def list_applications() -> list[dict[str, Any]]:
    """Retourne les entrées de catalogue découvertes par le Core.

    Ce endpoint expose une vue lecture seule ; la découverte et la validation
    restent la responsabilité du Core, pas de l'API.
    """
    return [entry.to_dict() for entry in _application_entries()]


@router.get("/applications/registered", dependencies=[Depends(require_permission(Permission.READ))])
async def list_registered_applications() -> list[dict[str, Any]]:
    """Expose the canonical registry that already owns Application integration records."""
    if _APPLICATION_REGISTRY is None:
        return []
    return _APPLICATION_REGISTRY.to_dict() if hasattr(_APPLICATION_REGISTRY, "to_dict") else [record.to_dict() for record in _APPLICATION_REGISTRY.list()]



@router.get("/application-capabilities", dependencies=[Depends(require_permission(Permission.READ))])
async def list_application_capabilities(application_id: str | None = None) -> list[dict[str, Any]]:
    """Retourne les contrats de capacités associés aux applications."""
    cells = get_application_capability_contracts(_application_integration_registry())
    if application_id is not None:
        cells = [item for item in cells if item.contract.application_id == application_id]
    return [item.to_dict() for item in cells]


@router.post("/application-capabilities/validate", dependencies=[Depends(require_permission(Permission.READ))])
async def validate_application_capability(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        contract = ApplicationCapabilityContract.from_mapping(payload.get("contract", payload))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if application_id := payload.get("application_id"):
        if contract.application_id != application_id:
            raise HTTPException(status_code=422, detail="contract application_id must match application_id")
    try:
        contract.validate()
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"valid": True, "contract": contract.to_dict()}


@router.post("/application-capabilities", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def register_application_capability_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("approved") is not True:
        raise HTTPException(status_code=403, detail="Explicit approval is required")
    app_id = payload.get("application_id")
    if not isinstance(app_id, str):
        raise HTTPException(status_code=422, detail="application_id is required")
    try:
        contract = ApplicationCapabilityContract.from_mapping(payload.get("contract", payload))
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if contract.application_id != app_id:
        raise HTTPException(status_code=422, detail="contract application_id must match application_id")

    registry = _application_integration_registry()
    if registry.get(app_id) is None:
        raise HTTPException(status_code=404, detail=f"Application not registered: {app_id}")

    try:
        registration = register_application_capability(registry, contract, approved=True)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "status": registration.registration_state,
        "capability_id": registration.capability_id,
        "application_id": registration.application_id,
        "approved": registration.approved,
        "contract": registration.contract.to_dict(),
    }



@router.get("/applications/{app_id}", dependencies=[Depends(require_permission(Permission.READ))])
async def get_application(app_id: str) -> dict[str, Any]:
    entry = _find_application(app_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
    return entry.to_dict()


@router.post("/applications/refresh", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def refresh_applications() -> dict[str, str]:
    _refresh_catalogs()
    return {"status": "refreshed", "count": str(len(_application_entries()))}



def _application_runtime_service(app_id: str):
    if app_id == "odin" and get_odin_service is not None:
        return get_odin_service()
    if app_id == "frame" and get_frame_service is not None:
        return get_frame_service()
    return None


@router.get(
    "/applications/{app_id}/runtime",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def get_application_runtime(app_id: str) -> dict[str, Any]:
    service = _application_runtime_service(app_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Runtime controller not found for application: {app_id}")
    status = await service.get_status()
    return {
        "app_id": app_id,
        "state": status.get("status"),
        "healthy": status.get("healthy"),
        "container_id": status.get("container_id"),
        "status": status,
    }


@router.post(
    "/applications/{app_id}/start",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def start_application_runtime(app_id: str) -> dict[str, Any]:
    service = _application_runtime_service(app_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Runtime controller not found for application: {app_id}")
    result = await service.start()
    return {"app_id": app_id, "action": "start", "result": result}


@router.post(
    "/applications/{app_id}/stop",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def stop_application_runtime(app_id: str) -> dict[str, Any]:
    service = _application_runtime_service(app_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Runtime controller not found for application: {app_id}")
    result = await service.stop()
    return {"app_id": app_id, "action": "stop", "result": result}


@router.post("/application-capabilities/{capability_id}/bind", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def bind_application_capability_implementation(capability_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    app_id = payload.get("application_id")
    if not isinstance(app_id, str):
        raise HTTPException(status_code=422, detail="application_id is required")
    implementation_alias = str(payload.get("implementation_alias", "")).strip()
    if implementation_alias not in TRUSTED_IMPLEMENTATION_ALIASES:
        raise HTTPException(status_code=422, detail=f"Unknown trusted implementation alias: {implementation_alias}")

    registry = _application_integration_registry()
    contracts = [item.contract for item in get_application_capability_contracts(registry)]
    contract = None
    for item in contracts:
        if item.application_id == app_id and item.capability_id == capability_id:
            contract = item
            break
    if contract is None:
        raise HTTPException(status_code=404, detail="capability contract is not registered")

    try:
        binding = bind_capability_implementation(
            registry,
            app_id,
            capability_id,
            implementation_alias,
            approved=bool(payload.get("approved", False)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    activation = bool(payload.get("activated", False))
    if activation:
        binding = activate_capability_binding(registry, app_id, capability_id, True)
    return {"status": "bound", "binding": binding.to_dict()}


@router.post("/application-capabilities/{capability_id}/activate", dependencies=[Depends(require_permission(Permission.PLUGINS))])
async def activate_application_capability(capability_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    app_id = payload.get("application_id")
    if not isinstance(app_id, str):
        raise HTTPException(status_code=422, detail="application_id is required")
    binding = activate_capability_binding(
        _application_integration_registry(),
        app_id,
        capability_id,
        bool(payload.get("activated", True)),
    )
    return {"status": "activated" if binding.activated else "deactivated", "binding": binding.to_dict()}


@router.post("/application-capabilities/{capability_id}/invoke", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def invoke_application_capability(
    capability_id: str,
    request: Request,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    app_id = payload.get("application_id")
    if not isinstance(app_id, str):
        raise HTTPException(status_code=422, detail="application_id is required")
    registry = _application_integration_registry()
    contracts = get_application_capability_contracts(registry)
    contract = None
    for item in contracts:
        if item.application_id == app_id and item.capability_id == capability_id:
            contract = item.contract
            break
    if contract is None:
        raise HTTPException(status_code=404, detail="capability contract is not registered")

    # Build an ExecutionContext from the authenticated principal so HROT
    # authorization receives agent identity, permissions, and request context.
    principal = getattr(request.state, "principal", None)
    execution_context = None
    if principal is not None:
        execution_context = ExecutionContext(
            principal=principal,
            agent_id=principal.actor_id or principal.subject_id,
            request_id=principal.request_id,
        )

    result = await invoke_capability(
        registry,
        app_id,
        capability_id,
        payload=payload.get("input", {}),
        execution_context=execution_context,
    )
    response = result.to_dict()
    if result.status != "success":
        raise HTTPException(status_code=424, detail=result.error)
    return response


__all__ = ["router"]
