"""Router API — Application Integration Catalog (read-only generic catalogue)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from interfaces.api.auth import require_permission
from core.auth import Permission

from core.applications.application_registry import ApplicationIntegrationRegistry
from core.applications.integration_catalog import IntegrationCatalogService
from core.applications.manifest_repository import ApplicationManifestRepository
from pathlib import Path
import os

router = APIRouter(prefix="/v1", tags=["application-integration"])


_APPLICATION_INTEGRATION_REGISTRY = ApplicationIntegrationRegistry()


def _catalog_service() -> IntegrationCatalogService:
    try:
        repository_path = os.environ.get("ETHAN_APPLICATION_MANIFEST_STORE")
        if not repository_path:
            repository_path = str(Path.home() / ".ethan" / "application-manifests.sqlite")
        repository = ApplicationManifestRepository(persistence_path=repository_path)
    except Exception:
        repository = None
    return IntegrationCatalogService(registry=_APPLICATION_INTEGRATION_REGISTRY, manifest_repository=repository)


@router.get(
    "/application-integration/catalog",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def list_application_integration_catalog(
    _permissions: bool = Depends(require_permission(Permission.READ)),
) -> dict[str, Any]:
    del _permissions
    try:
        from core.applications.local_repository_discovery import LocalRepositoryDiscovery
        from pathlib import Path
        import os

        configured = os.environ.get("ETHAN_LOCAL_REPOSITORY_ROOT")
        root = Path(configured).expanduser().resolve() if configured else Path("/home/fatsio/AI/Ethan").resolve()
        service = _catalog_service()
        return service.build(root=root, max_depth=3)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
