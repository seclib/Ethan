"""Router API — Durable Application Manifests (read-only + governed writes)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.applications.manifest_repository import ApplicationManifestRepository
from interfaces.api.auth import require_permission
from core.auth import Permission

router = APIRouter(prefix="/v1", tags=["application-manifests"])


def _repository() -> ApplicationManifestRepository:
    return ApplicationManifestRepository()


@router.get(
    "/application-manifests",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def list_application_manifests(app_id: str | None = None, instance_id: str | None = None) -> dict[str, Any]:
    repository = _repository()
    records = repository.list(app_id=app_id, instance_id=instance_id)
    return {"manifests": [record.to_dict() for record in records]}
