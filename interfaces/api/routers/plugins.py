"""Router API — Plugins (dédié, extrait de v1.py).

Toute la logique métier réside dans ``core.plugins.registry.PluginRegistry``.
Ce router est une passerelle HTTP mince.

Routes (préfixe /v1) :
    GET     /v1/plugins                              → catalogue + état
    GET     /v1/plugins/categories                   → catégories
    GET     /v1/plugins/{id}                         → détail
    GET     /v1/plugins/{id}/permissions             → permissions
    GET     /v1/plugins/{id}/capabilities           → capacités
    POST    /v1/plugins/install                      → installer
    POST    /v1/plugins/{id}/install                 → installer par id
    POST    /v1/plugins/{id}/enable                  → activer
    POST    /v1/plugins/{id}/disable                 → désactiver
    PUT     /v1/plugins/{id}/toggle                  → basculer
    PUT     /v1/plugins/{id}/update                  → synchroniser
    DELETE  /v1/plugins/{id}                         → désinstaller
    POST    /v1/plugins/{id}/connect                 → connecter
    DELETE  /v1/plugins/{id}/connection              → déconnecter
"""

from __future__ import annotations

from typing import Any

from core.auth import Permission
from core.plugins import PluginRegistry
from fastapi import APIRouter, Depends, HTTPException

from interfaces.api.auth import require_permission
from interfaces.api.gateway_guard import gateway_guard
from core.security.types import ActionType

router = APIRouter(prefix="/v1", tags=["plugins"])

# ── Dépendance (injection au démarrage via main.py) ───────────────────────

_plugin_registry: PluginRegistry | None = None


def set_plugin_registry(registry: PluginRegistry | None) -> None:
    global _plugin_registry
    _plugin_registry = registry


def _plugins() -> PluginRegistry:
    if _plugin_registry is None:
        from core.plugins import get_plugin_registry

        try:
            registry = get_plugin_registry()
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        set_plugin_registry(registry)
        return registry
    return _plugin_registry


# ── Routes ────────────────────────────────────────────────────────────────

@router.get("/plugins")
async def list_plugins():
    """Vue fusionnée catalogue + état (manifest + status/installed/connected)."""
    return await _plugins().list_plugins()


@router.get("/plugins/categories")
async def list_plugin_categories():
    """Catégories dynamiques dérivées du catalogue Core."""
    return {"categories": await _plugins().categories()}


@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    plugin = await _plugins().get(plugin_id)
    if plugin is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return plugin


@router.get("/plugins/{plugin_id}/permissions")
async def get_plugin_permissions(plugin_id: str):
    perms = await _plugins().permissions(plugin_id)
    if perms is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return perms


@router.get("/plugins/{plugin_id}/capabilities")
async def get_plugin_capabilities(plugin_id: str):
    caps = await _plugins().capabilities(plugin_id)
    if caps is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return caps


@router.post(
    "/plugins/install",
    dependencies=[
        Depends(require_permission(Permission.PLUGINS)),
        Depends(gateway_guard(ActionType.PLUGIN_INSTALL)),
    ],
)
async def install_plugin(data: dict[str, Any]):
    """Installe un plugin du catalogue (par id) ou, à défaut, un plugin custom."""
    plugin_id = data.get("id")
    try:
        if plugin_id:
            installed = await _plugins().install(str(plugin_id))
            if installed is not None:
                return installed
            name = str(data.get("name", "Unknown Plugin"))
            return await _plugins().install_custom(name, plugin_id=str(plugin_id))
        return await _plugins().install_custom(str(data.get("name", "Unknown Plugin")))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post(
    "/plugins/{plugin_id}/install", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def install_plugin_by_id(plugin_id: str):
    installed = await _plugins().install(plugin_id)
    if installed is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found in catalogue")
    return installed


@router.post(
    "/plugins/{plugin_id}/enable", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def enable_plugin(plugin_id: str):
    plugin = await _plugins().enable(plugin_id)
    if plugin is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return plugin


@router.post(
    "/plugins/{plugin_id}/disable", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def disable_plugin(plugin_id: str):
    plugin = await _plugins().disable(plugin_id)
    if plugin is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return plugin


@router.put(
    "/plugins/{plugin_id}/toggle", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def toggle_plugin(plugin_id: str):
    plugin = await _plugins().toggle(plugin_id)
    if plugin is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return plugin


@router.put(
    "/plugins/{plugin_id}/update", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def update_plugin(plugin_id: str):
    """Met à jour un plugin installé (synchronisation avec le manifest du catalogue)."""
    plugin = await _plugins().update(plugin_id)
    if plugin is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found or not installed")
    return plugin


@router.delete(
    "/plugins/{plugin_id}", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def uninstall_plugin(plugin_id: str, remove_data: bool = False):
    """Désinstalle un plugin."""
    result = await _plugins().uninstall(plugin_id, remove_data=remove_data)
    if result is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return result


@router.post(
    "/plugins/{plugin_id}/connect", dependencies=[Depends(require_permission(Permission.PLUGINS))]
)
async def connect_plugin(plugin_id: str, data: dict[str, Any] | None = None):
    """État « connecté » géré par le Core — jamais de secret dans le corps."""
    result = await _plugins().connect(plugin_id, (data or {}).get("config"))
    if result is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found or not installed")
    return result


@router.delete(
    "/plugins/{plugin_id}/connection",
    dependencies=[Depends(require_permission(Permission.PLUGINS))],
)
async def disconnect_plugin(plugin_id: str):
    result = await _plugins().disconnect(plugin_id)
    if result is None:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    return result