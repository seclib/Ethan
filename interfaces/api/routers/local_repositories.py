"""Router API — local Git repository discovery, validation and controlled registration."""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Mapping

from core.applications import ApplicationIntegrationRegistry
from core.applications.local_repository_discovery import LocalRepositoryDiscovery
from core.applications.models import ApplicationManifest, ValidationError, ValidationResult
from core.applications.validator import ContractValidator
from fastapi import APIRouter, Body, Depends, HTTPException
from interfaces.api.auth import require_permission
from core.auth import Permission

router = APIRouter(prefix="/v1", tags=["local-repositories"])


def _local_discovery_root() -> Path:
    configured = os.environ.get("ETHAN_LOCAL_REPOSITORY_ROOT")
    return Path(configured).expanduser().resolve() if configured else (Path.home() / "AI").resolve()


def _local_repository(path: str):
    system = LocalRepositoryDiscovery(root=_local_discovery_root(), max_depth=6)
    entries = {analysis.path: analysis for analysis in system.discover()}
    if path not in entries:
        raise HTTPException(status_code=404, detail=f"Local repository not found: {path}")
    return entries[path]


def _load_application_manifest(repo_path: str):
    system = LocalRepositoryDiscovery(root=_local_discovery_root(), max_depth=6)
    entries = {analysis.path: analysis for analysis in system.discover()}
    if repo_path not in entries:
        raise HTTPException(status_code=404, detail=f"Local repository not found: {repo_path}")

    actual_path = _local_discovery_root() / repo_path
    manifest_path = actual_path / "ethan-application-manifest.yaml"
    if not manifest_path.is_file():
        return None, ValidationResult(False, "INVALID", ("manifest file is missing",), ()), None

    try:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return None, ValidationResult(False, "INVALID", (str(exc),), ()), manifest_path

    result = ContractValidator().validate_manifest_data(payload)
    manifest = None
    if result.is_valid and isinstance(payload, dict):
        try:
            manifest = ApplicationManifest.from_mapping(payload)
        except (ValidationError, ValueError, TypeError) as exc:
            result = ValidationResult(False, "INVALID", (str(exc),), result.warnings, identity=result.identity)
            manifest = None
    return manifest, result, manifest_path


_APPLICATION_REGISTRY = ApplicationIntegrationRegistry()


@router.get(
    "/local-repositories",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def list_local_repositories() -> list[dict[str, Any]]:
    system = LocalRepositoryDiscovery(root=_local_discovery_root(), max_depth=4)
    return [analysis.to_dict() for analysis in system.discover()]


@router.get(
    "/local-repositories/{path:path}/compatibility",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def validate_local_repository_compat(path: str) -> dict[str, Any]:
    _local_repository(path)
    manifest, validation, manifest_path = _load_application_manifest(path)
    registered = False
    if manifest is not None:
        existing = _APPLICATION_REGISTRY.get(manifest.identity.app_id, manifest.identity.instance_id)
        registered = existing is not None
    return {
        "path": path,
        "manifest_path": None if manifest_path is None else str(manifest_path),
        "valid": validation.is_valid,
        "status": validation.status,
        "errors": list(validation.errors),
        "warnings": list(validation.warnings),
        "registered": registered,
    }


@router.get(
    "/local-repositories/{path:path}",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def get_local_repository(path: str) -> dict[str, Any]:
    system = LocalRepositoryDiscovery(root=_local_discovery_root(), max_depth=6)
    entries = {analysis.path: analysis for analysis in system.discover()}
    if path not in entries:
        raise HTTPException(status_code=404, detail=f"Local repository not found: {path}")
    entry = entries[path]
    payload = entry.to_dict()
    manifest, validation, _ = _load_application_manifest(path)
    payload["application_validation"] = {
        "valid": validation.is_valid,
        "status": validation.status,
        "errors": list(validation.errors),
        "warnings": list(validation.warnings),
        "registered": _APPLICATION_REGISTRY.get(manifest.identity.app_id, manifest.identity.instance_id) is not None if manifest else None,
    }
    return payload


@router.post(
    "/local-repositories/{path:path}/compatibility",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def validate_local_repository_compat_post(path: str) -> dict[str, Any]:
    return await validate_local_repository_compat(path)


@router.post(
    "/local-repositories/{path:path}/register",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def register_local_repository(path: str, approval: Mapping[str, Any] = Body(...)) -> dict[str, Any]:
    if approval.get("approved") is not True:
        raise HTTPException(status_code=403, detail="Explicit approval is required before registration")

    manifest, validation, _ = _load_application_manifest(path)
    if not validation.is_valid or manifest is None:
        raise HTTPException(status_code=422, detail="Local repository manifest is not valid")

    identity = manifest.identity
    existing = _APPLICATION_REGISTRY.get(identity.app_id, identity.instance_id)
    if existing is not None:
        return {
            "status": "already_registered",
            "registration_id": existing.registration_id,
            "app_id": existing.app_id,
            "instance_id": existing.instance_id,
            "state": existing.state.value,
        }

    try:
        record = _APPLICATION_REGISTRY.register(manifest, emit_event=False, actor="local-repository-api")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "status": "registered",
        "registration_id": record.registration_id,
        "app_id": record.app_id,
        "instance_id": record.instance_id,
        "state": record.state.value,
        "capabilities": list(record.capabilities),
    }


__all__ = ["router"]
