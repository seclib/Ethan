"""Extensions API — façade unique sur Capabilities, Plugins et Cookbook.

Passerelle MINCE (aucune logique metier) : ce routeur mappe des verbes REST sur
le `ExtensionManager` du Core et laisse l'authentification, l'autorisation
(RBAC) et la validation au Core et au middleware d'auth.

Le Core reste la source de verite : aucune route ne renvoie un etat calcule ou
simule cote API. Une installation est decrite par un `operation_id` que le
client suit jusqu'a un etat TERMINAL (SUCCESS / ERROR / TIMEOUT / CANCELLED) —
jamais un « installe » optimiste.
"""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from core.extensions.types import TransitionError
from fastapi import APIRouter, Depends, HTTPException, Request
from interfaces.api.auth import current_user_id, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/extensions", tags=["extensions"])

_manager: Any | None = None


def set_extension_manager(manager: Any) -> None:
    """Injecte l'ExtensionManager Core au demarrage de l'API."""
    global _manager
    _manager = manager


def get_extension_manager() -> Any:
    if _manager is None:
        raise HTTPException(503, "Extension manager not initialized")
    return _manager


def _error(exc: Exception) -> HTTPException:
    """Traduit les erreurs Core en statuts HTTP (sans fuite interne)."""
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc).strip("'"))
    if isinstance(exc, TransitionError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, (ValueError, TypeError)):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, NotImplementedError):
        return HTTPException(status_code=409, detail=str(exc))
    logger.exception("extensions: erreur interne")
    return HTTPException(status_code=500, detail="Erreur interne du Core")


def _actor(request: Request) -> str:
    return current_user_id(request) or "user"


# ── Catalogue ────────────────────────────────────────────────────────────────


@router.get("")
async def list_extensions(
    kind: str | None = None,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Catalogue unifie des trois types, avec l'etat REEL et les actions possibles."""
    statuses = await get_extension_manager().discover()
    items = [s.to_dict() for s in statuses]
    if kind:
        items = [i for i in items if i.get("kind") == kind]
    return {"extensions": items}


@router.get("/operations")
async def list_operations(
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Operations de cycle de vie, en cours ET terminees."""
    return {"operations": await get_extension_manager().list_operations()}


@router.get("/operations/{operation_id}")
async def get_operation(
    operation_id: str,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Progression d'une operation.

    404 = identifiant inconnu (jamais cree ou purge) — permet a l'interface
    d'arreter de scruter au lieu de boucler sur une operation disparue.
    """
    op = await get_extension_manager().get_operation(operation_id)
    if op is None:
        raise HTTPException(404, "operation inconnue")
    return op


@router.post("/operations/{operation_id}/cancel")
async def cancel_operation(
    operation_id: str,
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Annule une operation : la reponse est immediate."""
    ok = await get_extension_manager().cancel_operation(operation_id)
    return {"cancelled": ok}


# ── Cycle de vie ────────────────────────────────────────────────────────────


@router.post("/{extension_id}/install", status_code=202)
async def install_extension(
    extension_id: str,
    request: Request,
    body: dict[str, Any] | None = None,
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Lance l'installation. Retourne un `operation_id` a suivre jusqu'au bout."""
    try:
        config = (body or {}).get("config") or {}
        operation_id = await get_extension_manager().install(
            extension_id, config, actor=_actor(request)
        )
        return {"operation_id": operation_id, "extension_id": extension_id}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/{extension_id}/uninstall", status_code=202)
async def uninstall_extension(
    extension_id: str,
    request: Request,
    body: dict[str, Any] | None = None,
    _: bool = Depends(require_permission(Permission.ADMIN)),
):
    """Desinstalle. La suppression des donnees est EXPLICITE et confirmee."""
    try:
        payload = body or {}
        delete_data = bool(payload.get("delete_data", False))
        if delete_data and not payload.get("confirm_delete_data"):
            raise HTTPException(
                422,
                "suppression de donnees non confirmee : envoyer confirm_delete_data=true",
            )
        operation_id = await get_extension_manager().uninstall(
            extension_id, delete_data=delete_data, actor=_actor(request)
        )
        return {
            "operation_id": operation_id,
            "extension_id": extension_id,
            "delete_data": delete_data,
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/{extension_id}/update", status_code=202)
async def update_extension(
    extension_id: str,
    request: Request,
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Mise a jour — re-applique l'installation (idempotent)."""
    try:
        operation_id = await get_extension_manager().update(
            extension_id, actor=_actor(request)
        )
        return {"operation_id": operation_id, "extension_id": extension_id}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/{extension_id}/enable", status_code=202)
async def enable_extension(
    extension_id: str,
    request: Request,
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Active — refuse si le type ne sait pas le faire (ex. Cookbook)."""
    try:
        operation_id = await get_extension_manager().enable(
            extension_id, actor=_actor(request)
        )
        return {"operation_id": operation_id, "extension_id": extension_id}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/{extension_id}/disable", status_code=202)
async def disable_extension(
    extension_id: str,
    request: Request,
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Desactive sans rien supprimer."""
    try:
        operation_id = await get_extension_manager().disable(
            extension_id, actor=_actor(request)
        )
        return {"operation_id": operation_id, "extension_id": extension_id}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/{extension_id}/configure")
async def configure_extension(
    extension_id: str,
    body: dict[str, Any],
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Applique une configuration — validee par le systeme d'origine."""
    try:
        state = await get_extension_manager().configure(
            extension_id, (body or {}).get("config") or {}
        )
        return {"extension_id": extension_id, "config_keys": sorted(state.config)}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.get("/{extension_id}/plan")
async def plan_extension(
    extension_id: str,
    uninstall: bool = False,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Plan de mutation quand le type sait en produire un."""
    try:
        return await get_extension_manager().plan(extension_id, uninstall=uninstall)
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.get("/{extension_id}/logs")
async def extension_logs(
    extension_id: str,
    tail: int = 200,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Logs du runtime — absent pour les types sans runtime."""
    try:
        return await get_extension_manager().logs(extension_id, tail=tail)
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc
@router.get("/{extension_id}")
async def get_extension(
    extension_id: str,
    _: bool = Depends(require_permission(Permission.READ)),
):
    status = await get_extension_manager().get(extension_id)
    if status is None:
        raise HTTPException(404, "extension inconnue")
    return status.to_dict()
