"""Security Gateway guard — validation des routes API sensibles (CTO P0-1).

Le SecurityGateway (``core/security/gateway.py``) est branché sur les routes
qui installent du code externe. Pour chaque appel :

1. ``require_permission`` (RBAC) s'exécute d'abord — seule une identité
   autorisée atteint le gateway ;
2. le gateway applique sa chaîne (signature → permissions → politiques →
   **rate limit par acteur** → audit append-only) ;
3. un rejet lève 403 (ou 429 pour un dépassement de rate limit) avant toute
   exécution — l'exécution reste du ressort du handler puis du Core.
"""

from __future__ import annotations

import logging

from core.security.gateway import SecurityGateway
from core.security.types import ActionType
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

_gateway = SecurityGateway()
_gateway_ready = False


async def get_security_gateway() -> SecurityGateway:
    """Singleton du SecurityGateway (initialisé paresseusement)."""
    global _gateway_ready
    if not _gateway_ready:
        await _gateway.initialize()
        _gateway_ready = True
    return _gateway


def gateway_guard(action_type: ActionType):
    """Dépendance FastAPI : valide l'action via le SecurityGateway.

    Usage (``require_permission`` AVANT le guard dans la liste ``dependencies``) ::

        @router.post("/x", dependencies=[
            Depends(require_permission(Permission.PLUGINS)),
            Depends(gateway_guard(ActionType.PLUGIN_INSTALL)),
        ])
    """

    async def checker(request: Request) -> None:
        payload = getattr(request.state, "token_payload", None) or {}
        role = str(payload.get("role") or "user").lower()
        # Rôles Core : admin porte ``*:*`` dans le PermissionChecker, les
        # autres rôles sont mappés sur le rôle « user » (permissions de base).
        identity_type = "admin" if role == "admin" else "user"
        actor = str(payload.get("sub") or getattr(request.state, "user", "anonymous"))

        gateway = await get_security_gateway()
        result = await gateway.execute(
            action_type.value,
            {"session_id": str(payload.get("sid") or "api")},
            source=identity_type,
            actor=actor,
        )
        if not result.valid:
            error = result.error or "Action refusée par le Security Gateway."
            code = (
                status.HTTP_429_TOO_MANY_REQUESTS
                if "rate limit" in error.lower()
                else status.HTTP_403_FORBIDDEN
            )
            logger.warning(
                "Security Gateway rejected %s for %s (%s): %s",
                action_type.value,
                actor,
                code,
                error,
            )
            raise HTTPException(status_code=code, detail=error)

    # Contrat d'introspection (même convention que ``require_permission``) :
    # les tests de frontière et les matrices « route → garde » relisent
    # l'action protégée sans exécuter le gate. Purement déclaratif.
    checker.gateway_action = action_type
    return checker
