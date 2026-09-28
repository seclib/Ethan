"""Connections Router — passerelle HTTP vers le ConnectionManager Core.

Le Core possède toute la logique (OAuth, tokens, statuts, permissions,
events). Ce router n'ajoute aucune règle métier : il identifie
l'utilisateur (JWT), vérifie le RBAC et délègue.

Sécurité :
- Les tokens ne sont JAMAIS retournés (aucune route ne les expose) ;
  ``connection-tokens`` n'est lisible que par le Core/Runtime.
- L'utilisateur est déduit du JWT (``request.state.user``) — un utilisateur
  ne peut opérer que sur SES connexions (vérifié côté Core en plus).
- Les mutations exigent ``Permission.PLUGINS`` ; la lecture ``Permission.READ``.
"""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from core.integrations.connections import ConnectionError, ConnectionManager
from fastapi import APIRouter, Depends, HTTPException, Request
from interfaces.api.auth import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connections", tags=["connections"])

_manager: ConnectionManager | None = None


def set_connection_manager(manager: ConnectionManager) -> None:
    global _manager
    _manager = manager


def get_connection_manager() -> ConnectionManager:
    if _manager is None:
        raise HTTPException(503, "Connection manager not initialized")
    return _manager


def _current_user(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(401, "Authentication required")
    return str(user)


def _map_error(exc: ConnectionError) -> HTTPException:
    message = str(exc)
    code = 404 if "not found" in message.lower() else 422
    return HTTPException(code, message)


@router.get("", dependencies=[Depends(require_permission(Permission.READ))])
async def list_connections(request: Request):
    """Connexions de l'utilisateur courant (sans aucun secret)."""
    return await get_connection_manager().list(_current_user(request))


@router.get("/providers", dependencies=[Depends(require_permission(Permission.READ))])
async def list_providers_catalog():
    """Catalogue des connecteurs disponibles (id, label, scopes explicites)."""
    return get_connection_manager().catalog()


@router.post(
    "/{provider_id}/connect",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def connect(request: Request, provider_id: str, data: dict[str, Any] | None = None):
    """Connecter (ou reconnecter si ``reconnect=true``) : retourne l'URL
    d'autorisation OAuth. Aucun secret dans la réponse.
    """
    user = _current_user(request)
    manager = get_connection_manager()
    data = data or {}
    try:
        if bool(data.get("reconnect")):
            return await manager.reconnect(user, provider_id, data.get("redirect_uri"))
        return await manager.start(user, provider_id, data.get("redirect_uri"))
    except ConnectionError as exc:
        raise _map_error(exc) from exc


@router.post(
    "/{provider_id}/callback",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def callback(request: Request, provider_id: str, data: dict[str, Any]):
    """Callback OAuth : échange le code (vérifié par ``state`` côté Core)."""
    user = _current_user(request)
    code = str(data.get("code") or "")
    state = str(data.get("state") or "")
    if not code or not state:
        raise HTTPException(422, "Both 'code' and 'state' are required")
    try:
        return await get_connection_manager().callback(user, provider_id, code, state)
    except ConnectionError as exc:
        raise _map_error(exc) from exc


@router.post(
    "/{provider_id}/test",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def test_connection(request: Request, provider_id: str):
    """Tester réellement la connexion (appel API du service)."""
    try:
        return await get_connection_manager().test(_current_user(request), provider_id)
    except ConnectionError as exc:
        raise _map_error(exc) from exc


@router.get(
    "/{provider_id}/permissions",
    dependencies=[Depends(require_permission(Permission.READ))],
)
async def get_permissions(request: Request, provider_id: str):
    """Voir les permissions (scopes demandés vs accordés)."""
    try:
        return await get_connection_manager().permissions(_current_user(request), provider_id)
    except ConnectionError as exc:
        raise _map_error(exc) from exc


@router.delete(
    "/{provider_id}",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def disconnect(request: Request, provider_id: str):
    """Déconnecter : purge les tokens, conserve l'historique du statut."""
    try:
        return await get_connection_manager().disconnect(_current_user(request), provider_id)
    except ConnectionError as exc:
        raise _map_error(exc) from exc


@router.post(
    "/{provider_id}/operations/{operation}",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def run_operation(
    request: Request,
    provider_id: str,
    operation: str,
    data: dict[str, Any] | None = None,
):
    """Exécute une opération DÉCLARÉE par le connecteur (Core : scope,
    appartenance et disponibilité vérifiés). Aucun token dans la réponse."""
    try:
        return await get_connection_manager().run_operation(
            _current_user(request), provider_id, operation, data
        )
    except ConnectionError as exc:
        raise _map_error(exc) from exc


@router.post(
    "/{provider_id}/credentials",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def connect_credentials(request: Request, provider_id: str, data: dict[str, Any]):
    """Connexion par identifiants (SMTP/IMAP). Les secrets sont testés puis
    stockés UNIQUEMENT côté Core (``connection-tokens``) — jamais renvoyés."""
    if not isinstance(data, dict) or not data:
        raise HTTPException(422, "Credentials payload is required")
    try:
        return await get_connection_manager().connect_password(
            _current_user(request),
            provider_id,
            {str(k): str(v) for k, v in data.items()},
        )
    except ConnectionError as exc:
        raise _map_error(exc) from exc


__all__ = ["router", "set_connection_manager", "get_connection_manager"]
