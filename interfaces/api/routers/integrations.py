"""Integrations Router — passerelle HTTP vers le IntegrationManager Core.

Le Core possède toute la logique (identité, config, credentials, capacités,
permissions, health, lifecycle). Ce router n'ajoute aucune règle métier :
il vérifie le RBAC et délègue.

Sécurité :
- Les credentials ne sont JAMAIS retournés (aucune route ne les expose) ;
  elles sont acceptées en écriture (POST/PUT) et stockées dans le domaine
  dédié du Core.
- Les mutations exigent ``Permission.PLUGINS`` ; la lecture ``Permission.READ``.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from core.auth import Permission
from core.integrations import IntegrationError, IntegrationManager
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

_manager: IntegrationManager | None = None


def set_integration_manager(manager: IntegrationManager) -> None:
    global _manager
    _manager = manager


def get_integration_manager() -> IntegrationManager:
    if _manager is None:
        raise HTTPException(503, "Integration manager not initialized")
    return _manager


def _not_found(exc: IntegrationError) -> HTTPException:
    code = 404 if "not found" in str(exc).lower() else 422
    return HTTPException(code, str(exc))


@router.get("", dependencies=[Depends(require_permission(Permission.READ))])
async def list_integrations(request: Request, kind: str | None = None):
    """Liste les intégrations (sans secrets) avec leurs clés de credentials."""
    manager = get_integration_manager()
    integrations = await manager.list(kind=kind)
    result = []
    for integration in integrations:
        public = dict(integration)
        public["credential_keys"] = await manager.credential_keys(integration["id"])
        public["has_credentials"] = bool(public["credential_keys"])
        result.append(public)
    return result


@router.get("/{integration_id}", dependencies=[Depends(require_permission(Permission.READ))])
async def get_integration(integration_id: str):
    """Détail d'une intégration (sans secrets)."""
    manager = get_integration_manager()
    integration = await manager.get(integration_id)
    if integration is None:
        raise HTTPException(404, f"Integration {integration_id} not found")
    public = dict(integration)
    public["credential_keys"] = await manager.credential_keys(integration_id)
    public["has_credentials"] = bool(public["credential_keys"])
    return public


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def create_integration(data: dict[str, Any]):
    """Enregistre une intégration (credentials stockés dans le domaine dédié)."""
    manager = get_integration_manager()
    try:
        integration = await manager.register(
            name=str(data.get("name", "")),
            kind=str(data.get("kind", "")),
            description=str(data.get("description", "")),
            config=data.get("config") or {},
            credentials=data.get("credentials"),
            capabilities=data.get("capabilities") or [],
            required_permissions=data.get("required_permissions") or [],
            enabled=bool(data.get("enabled", True)),
            metadata=data.get("metadata") or {},
        )
    except IntegrationError as exc:
        raise _not_found(exc) from exc
    return integration


@router.put(
    "/{integration_id}",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def update_integration(integration_id: str, data: dict[str, Any]):
    """Met à jour la configuration d'une intégration."""
    manager = get_integration_manager()
    try:
        updated = await manager.update(integration_id, data)
    except IntegrationError as exc:
        raise _not_found(exc) from exc
    if updated is None:
        raise HTTPException(404, f"Integration {integration_id} not found")
    return updated


@router.delete(
    "/{integration_id}",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def delete_integration(integration_id: str):
    """Supprime une intégration et purge ses credentials."""
    manager = get_integration_manager()
    existed = await manager.delete(integration_id)
    if not existed:
        raise HTTPException(404, f"Integration {integration_id} not found")
    return {"status": "deleted", "integration_id": integration_id}


@router.post(
    "/{integration_id}/connect",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def connect_integration(integration_id: str):
    """Connecte l'intégration (healthcheck puis statut connected/error)."""
    manager = get_integration_manager()
    try:
        return await manager.connect(integration_id)
    except IntegrationError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/{integration_id}/disconnect",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def disconnect_integration(integration_id: str):
    """Déconnecte l'intégration."""
    manager = get_integration_manager()
    result = await manager.disconnect(integration_id)
    if result is None:
        raise HTTPException(404, f"Integration {integration_id} not found")
    return result


@router.post(
    "/{integration_id}/test",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def test_integration(integration_id: str):
    """Teste la connexion (healthcheck selon le kind)."""
    manager = get_integration_manager()
    try:
        return await manager.test_connection(integration_id)
    except IntegrationError as exc:
        raise _not_found(exc) from exc
