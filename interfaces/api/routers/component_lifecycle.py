"""Component lifecycle router — gateway HTTP vers le Capability Manager du Core.

Le Core (core/capability_manager) est la source de verite du cycle de vie :
  detect → install → configure → test → enable → disable → uninstall.

Ce router est une passerelle MINCE (aucune logique metier) : il mappe les
verbes REST sur le manager Core et laisse l'authentification, l'autorisation
(RBAC) et la validation au Core et au middleware d'auth.

Securite (section 10) :
- toutes les routes sont authentifiees (auth_middleware) ;
- les mutations exigent une permission dediee (ADMIN / SETTINGS / EXECUTE) ;
- aucune chaine utilisateur n'atteint une commande shell : le Core valide la
  configuration contre un schema (ConfigField) et n'utilise que des argv.
"""

from __future__ import annotations

import logging
from typing import Any

from core.auth import Permission
from fastapi import APIRouter, Depends, HTTPException, Request
from interfaces.api.auth import current_user_id, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["components"])


# ── injection du manager Core (meme pattern que capabilities.py) ──
_manager: Any | None = None


def set_component_manager(manager: Any) -> None:
    """Injecte le CapabilityManager Core au demarrage de l'API."""
    global _manager
    _manager = manager


def get_component_manager() -> Any:
    """Retourne le manager injecte ou en construit un a la volee (builtin)."""
    global _manager
    if _manager is None:
        from core.capability_manager.builtin import build_manager

        _manager = build_manager()
    return _manager


def _error(exc: Exception) -> HTTPException:
    """Traduit les erreurs Core en statuts HTTP (sans fuite interne)."""
    from core.capability_manager import TransitionError

    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc).strip("'"))
    if isinstance(exc, TransitionError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, (ValueError, TypeError)):
        return HTTPException(status_code=422, detail=str(exc))
    logger.exception("component lifecycle: erreur interne")
    return HTTPException(status_code=500, detail="Erreur interne du Core")


# ═══════════════════════════════════════════════════════════════════════════
# OPERATIONS (declarees AVANT /{capability_id} pour le routage FastAPI)
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/components/operations")
async def list_operations(
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Liste les operations de cycle de vie en cours ou terminees."""
    return {"operations": get_component_manager().list_operations()}


@router.get("/components/operations/{operation_id}")
async def get_operation(
    operation_id: str,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Progression detaillee d'une operation (etapes, avancement, erreur)."""
    operation = get_component_manager().get_operation(operation_id)
    if operation is None:
        raise HTTPException(404, "operation inconnue: " + operation_id)
    return operation


@router.post("/components/operations/{operation_id}/cancel")
async def cancel_operation(
    operation_id: str,
    _: bool = Depends(require_permission(Permission.ADMIN)),
):
    """Demande l'annulation d'une installation/desinstallation en cours."""
    cancelled = await get_component_manager().cancel_operation(operation_id)
    if not cancelled:
        raise HTTPException(409, "operation deja terminee: " + operation_id)
    return {"operation_id": operation_id, "cancel_requested": True}


# ═══════════════════════════════════════════════════════════════════════════
# ETAT DES COMPOSANTS
# ═══════════════════════════════════════════════════════════════════════════


@router.get("/components")
async def list_components(
    refresh: bool = False,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Liste les capabilities avec leur etat explicite (jamais un booleen)."""
    try:
        manager = get_component_manager()
        if refresh:
            await manager.detect()
        return {"capabilities": await manager.status_all()}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/components/detect", dependencies=[Depends(require_permission(Permission.EXECUTE))])
async def detect_components():
    """Relance la detection support/dependances/installation/sante."""
    try:
        states = await get_component_manager().detect()
        return {"states": {cid: st.state for cid, st in states.items()}}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.get("/components/{capability_id}")
async def get_component(
    capability_id: str,
    _: bool = Depends(require_permission(Permission.READ)),
):
    try:
        return await get_component_manager().status(capability_id)
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.get("/components/{capability_id}/logs")
async def get_component_logs(
    capability_id: str,
    tail: int = 200,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Logs d'exécution du composant (lecture seule, taille bornée).

    Le Core répond avec des logs réels quand le backend en produit
    (Docker) ; sinon `available=False` + raison — jamais de faux contenu.
    """
    try:
        return await get_component_manager().logs(capability_id, tail=tail)
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.get("/components/{capability_id}/plan")
async def plan_install(
    capability_id: str,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Plan d'installation : operations prevues AVANT toute confirmation."""
    try:
        plan = await get_component_manager().plan_install(capability_id)
        return plan.to_dict()
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.get("/components/{capability_id}/plan/uninstall")
async def plan_uninstall(
    capability_id: str,
    delete_data: bool = False,
    _: bool = Depends(require_permission(Permission.READ)),
):
    """Plan de desinstallation ; `delete_data` expose explicitement le risque."""
    try:
        plan = await get_component_manager().plan_uninstall(capability_id, delete_data)
        return plan.to_dict()
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/components/{capability_id}/install", status_code=202)
async def install_component(
    capability_id: str,
    request: Request,
    data: dict[str, Any] | None = None,
    _: bool = Depends(require_permission(Permission.ADMIN)),
):
    """Installe (explicitement), demarre et teste. Retourne un operation_id."""
    try:
        actor = current_user_id(request) or "user"
        operation_id = await get_component_manager().install(
            capability_id, (data or {}).get("config") or None, actor=actor
        )
        return {"operation_id": operation_id, "capability_id": capability_id}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/components/{capability_id}/configure")
async def configure_component(
    capability_id: str,
    data: dict[str, Any],
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Applique une configuration validee par le schema de la capability."""
    try:
        manager = get_component_manager()
        state = await manager.configure(capability_id, data.get("config", {}))
        return {"capability_id": capability_id, "config_keys": list(state.config.keys())}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post(
    "/components/{capability_id}/stop",
    dependencies=[Depends(require_permission(Permission.SETTINGS))],
)
async def stop_component(capability_id: str, request: Request):
    """Arrête le composant (données conservées) — section 3 de la spec UI."""
    try:
        actor = current_user_id(request) or "user"
        await get_component_manager().stop(capability_id, actor=actor)
        return await get_component_manager().status(capability_id)
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post(
    "/components/{capability_id}/start",
    dependencies=[Depends(require_permission(Permission.SETTINGS))],
)
async def start_component(capability_id: str, request: Request):
    """Démarre un composant arrêté et vérifie la santé réelle."""
    try:
        actor = current_user_id(request) or "user"
        await get_component_manager().start(capability_id, actor=actor)
        return await get_component_manager().status(capability_id)
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post(
    "/components/{capability_id}/test",
    dependencies=[Depends(require_permission(Permission.EXECUTE))],
)
async def test_component(capability_id: str):
    """Teste la sante reelle (endpoint/API/fonctionnel) — pas seulement installe."""
    try:
        return await get_component_manager().test(capability_id)
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/components/{capability_id}/enable")
async def enable_component(
    capability_id: str,
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Active dans ETHAN — exige l'etat READY (sante validee)."""
    try:
        await get_component_manager().enable(capability_id)
        return {"capability_id": capability_id, "enabled": True}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/components/{capability_id}/disable")
async def disable_component(
    capability_id: str,
    _: bool = Depends(require_permission(Permission.SETTINGS)),
):
    """Desactive dans ETHAN sans rien supprimer."""
    try:
        await get_component_manager().disable(capability_id)
        return {"capability_id": capability_id, "enabled": False}
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc


@router.post("/components/{capability_id}/uninstall", status_code=202)
async def uninstall_component(
    capability_id: str,
    data: dict[str, Any] | None = None,
    _: bool = Depends(require_permission(Permission.ADMIN)),
):
    """Desinstalle le composant ; la suppression des donnees est explicite."""
    try:
        payload = data or {}
        delete_data = bool(payload.get("delete_data", False))
        if delete_data and not payload.get("confirm_delete_data"):
            raise HTTPException(
                422,
                "suppression de donnees non confirmee : "
                "envoyer confirm_delete_data=true est requis",
            )
        operation_id = await get_component_manager().uninstall(
            capability_id, delete_data=delete_data
        )
        return {
            "operation_id": operation_id,
            "capability_id": capability_id,
            "delete_data": delete_data,
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _error(exc) from exc
