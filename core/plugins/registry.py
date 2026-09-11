"""Plugin Registry — le gestionnaire de plugins ETHAN (Core-owned).

Source de vérité unique du système Plugins :
  - catalogue : manifestes déclarés (core/plugins/catalog.py) ;
  - état : records persistés dans le domaine `webui_plugins` du
    CoreRecordStore (compatibles avec les enregistrements historiques) ;
  - permissions : déclarées dans le manifest, recoupées avec la
    ToolRegistry réelle pour les outils référencés.

Le registre n'exécute rien : il décrit, valide et arbitre les états.
L'exécution reste dans Runtime / ToolExecutor / Skills Executor.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

from .catalog import BUILTIN_PLUGINS, catalogue_categories, find_manifest
from .types import STATUS_ACTIVE, STATUS_AVAILABLE, STATUS_INACTIVE, PluginManifest

logger = logging.getLogger(__name__)

_DOMAIN = "webui_plugins"


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class PluginRegistry:
    """Registre Core des plugins : catalogue + état persistant."""

    def __init__(self, store: CoreRecordStore, tool_registry: Any | None = None) -> None:
        self._store = store
        self._tool_registry = tool_registry

    # ── Lecture ────────────────────────────────────────────────────────

    async def list_plugins(self) -> list[dict[str, Any]]:
        """Vue fusionnée catalogue + état, ordre stable, legacy préservé.

        Les enregistrements inconnus du catalogue (plugins custom ou
        historiques) sont conservés tels quels (source=custom).
        """
        records = {
            r.get("id"): r for r in await self._store.list(_DOMAIN) if r.get("id")
        }
        seen: set[str] = set()
        result: list[dict[str, Any]] = []

        for manifest in BUILTIN_PLUGINS:
            plugin_id = manifest.id
            seen.add(plugin_id)
            state = records.get(plugin_id)
            view = manifest.to_dict()
            if state is None:
                view.update(self._default_state(plugin_id, manifest))
            else:
                view.update(self._merge_state(state))
            result.append(view)

        # Enregistrements legacy/custom hors catalogue.
        for plugin_id, record in records.items():
            if plugin_id in seen:
                continue
            legacy = dict(record)
            legacy.setdefault("status", STATUS_INACTIVE)
            legacy.setdefault("version", "0.1.0")
            legacy.setdefault("source", "custom")
            legacy["installed"] = True
            legacy.setdefault("capabilities", [])
            legacy.setdefault("permissions", [])
            result.append(legacy)

        return result

    async def get(self, plugin_id: str) -> dict[str, Any] | None:
        for plugin in await self.list_plugins():
            if plugin["id"] == plugin_id:
                return plugin
        return None

    async def categories(self) -> list[dict[str, str]]:
        return catalogue_categories()

    async def permissions(self, plugin_id: str) -> dict[str, Any] | None:
        plugin = await self.get(plugin_id)
        if plugin is None:
            return None
        declared = list(plugin.get("permissions", []))
        effective = self._effective_tool_permissions(plugin)
        usable = self._is_usable(plugin)
        return {
            "plugin_id": plugin_id,
            "declared": declared,
            "effective_from_tools": effective,
            "granted": list(plugin.get("granted_permissions", declared if usable else [])),
            "authentication": plugin.get("authentication", {}),
        }

    async def capabilities(self, plugin_id: str) -> dict[str, Any] | None:
        plugin = await self.get(plugin_id)
        if plugin is None:
            return None
        return {
            "plugin_id": plugin_id,
            "capabilities": list(plugin.get("capabilities", [])),
            "tools": self._resolve_tools(plugin),
            "skills": list(plugin.get("skills", [])),
            "mcp": list(plugin.get("mcp", [])),
        }

    # ── Cycle de vie ───────────────────────────────────────────────────

    async def install(self, plugin_id: str) -> dict[str, Any] | None:
        """Installe un plugin du catalogue (état initial : inactive)."""
        manifest = find_manifest(plugin_id)
        if manifest is None:
            return None
        record = await self._store.get(_DOMAIN, plugin_id)
        if record is None:
            record = self._default_state(plugin_id, manifest)
            record["installed"] = True
            record["status"] = STATUS_INACTIVE
            record["installed_at"] = _now()
        else:
            record["installed"] = True
            record["manifest_version"] = manifest.version
        record["id"] = plugin_id
        await self._store.save(_DOMAIN, plugin_id, record)
        return await self.get(plugin_id)

    async def install_custom(self, name: str, plugin_id: str | None = None) -> dict[str, Any]:
        """Enregistre un plugin custom (compatibilité historique : {name})."""
        custom_id = plugin_id or str(uuid4())
        record = {
            "id": custom_id,
            "name": name or "Unknown Plugin",
            "status": STATUS_INACTIVE,
            "version": "0.1.0",
            "source": "custom",
            "installed": True,
            "capabilities": [],
            "permissions": [],
            "installed_at": _now(),
        }
        await self._store.save(_DOMAIN, custom_id, record)
        return deepcopy(record)

    async def enable(self, plugin_id: str) -> dict[str, Any] | None:
        return await self._set_status(plugin_id, STATUS_ACTIVE)

    async def disable(self, plugin_id: str) -> dict[str, Any] | None:
        return await self._set_status(plugin_id, STATUS_INACTIVE)

    async def toggle(self, plugin_id: str) -> dict[str, Any] | None:
        plugin = await self.get(plugin_id)
        if plugin is None:
            return None
        target = STATUS_INACTIVE if plugin.get("status") == STATUS_ACTIVE else STATUS_ACTIVE
        return await self._set_status(plugin_id, target)

    async def connect(
        self, plugin_id: str, config: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Enregistre l'état « connecté » d'un plugin.

        Aucun secret n'est accepté ni stocké ici : les champs marqués
        `secret` doivent être fournis via la couche secret manager (env/
        Vault).  La connexion n'est validée que si la configuration non
        secrète requise est présente.
        """
        plugin = await self.get(plugin_id)
        if plugin is None:
            return None
        if plugin.get("installed") is not True:
            return None
        record = await self._store.get(_DOMAIN, plugin_id) or {}
        non_secret = {
            f["key"]: f
            for f in plugin.get("configuration", [])
            if not f.get("secret") and f.get("required")
        }
        incoming = dict(config or {})
        missing = [key for key in non_secret if key not in incoming]
        if missing:
            return {
                "connected": False,
                "missing_configuration": missing,
                "authentication": plugin.get("authentication", {}),
                "message": (
                    "Configuration incomplète. Les secrets doivent être "
                    "fournis via la couche secret manager (jamais via l'API "
                    "WebUI)."
                ),
            }
        merged = dict(record.get("configuration") or {})
        for key in non_secret:
            if key in incoming:
                merged[key] = incoming[key]
        record["id"] = plugin_id
        record["connected"] = True
        record["configuration"] = merged
        record["connected_at"] = _now()
        await self._store.save(_DOMAIN, plugin_id, record)
        return await self.get(plugin_id)

    async def disconnect(self, plugin_id: str) -> dict[str, Any] | None:
        plugin = await self.get(plugin_id)
        if plugin is None:
            return None
        record = await self._store.get(_DOMAIN, plugin_id) or {"id": plugin_id}
        record["id"] = plugin_id
        record["connected"] = False
        record["connected_at"] = None
        await self._store.save(_DOMAIN, plugin_id, record)
        return await self.get(plugin_id)

    # ── Helpers ────────────────────────────────────────────────────────

    def _default_state(self, plugin_id: str, manifest: PluginManifest) -> dict[str, Any]:
        return {
            "id": plugin_id,
            "name": manifest.name,
            "status": STATUS_AVAILABLE,
            "version": manifest.version,
            "installed": False,
            "connected": False,
            "last_used_at": None,
        }

    def _merge_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Fusionne un record d'état (parfois legacy minimal) dans la vue."""
        status = state.get("status")
        if status not in (STATUS_ACTIVE, STATUS_INACTIVE):
            status = STATUS_INACTIVE
        return {
            "status": status,
            "installed": bool(state.get("installed", True)),
            "connected": bool(state.get("connected", False)),
            "configuration": state.get("configuration") or {},
            "granted_permissions": state.get("granted_permissions") or [],
            "last_used_at": state.get("last_used_at"),
            "installed_at": state.get("installed_at"),
        }

    def _is_usable(self, plugin: dict[str, Any]) -> bool:
        return plugin.get("status") == STATUS_ACTIVE and plugin.get("installed") is True

    def _resolve_tools(self, plugin: dict[str, Any]) -> list[dict[str, Any]]:
        """Résout les tools référencés contre la ToolRegistry réelle."""
        resolved: list[dict[str, Any]] = []
        registry = self._tool_registry
        for tool_id in plugin.get("tools", []):
            tool = None
            if registry is not None:
                tool = registry.get_tool(tool_id)
            if tool is not None:
                resolved.append(
                    {
                        "id": tool_id,
                        "name": getattr(tool, "name", tool_id),
                        "available": True,
                        "risk_level": str(getattr(tool, "risk_level", "low")),
                    }
                )
            else:
                resolved.append({"id": tool_id, "name": tool_id, "available": False})
        return resolved

    def _effective_tool_permissions(self, plugin: dict[str, Any]) -> list[str]:
        """Permissions réellement requises par les tools référencés."""
        effective: set[str] = set()
        registry = self._tool_registry
        if registry is None:
            return []
        for tool_id in plugin.get("tools", []):
            tool = registry.get_tool(tool_id)
            if tool is None:
                continue
            for permission in getattr(tool, "required_permissions", []) or []:
                effective.add(str(permission))
        return sorted(effective)

    async def _set_status(self, plugin_id: str, status: str) -> dict[str, Any] | None:
        plugin = await self.get(plugin_id)
        if plugin is None:
            return None
        record = await self._store.get(_DOMAIN, plugin_id) or {}
        record["id"] = plugin_id
        record["status"] = status
        record["installed"] = True
        await self._store.save(_DOMAIN, plugin_id, record)
        return await self.get(plugin_id)


# ── Accessor module-level (composition root API) ──────────────────────

_registry: PluginRegistry | None = None


def set_plugin_registry(registry: PluginRegistry | None) -> None:
    global _registry
    _registry = registry


def get_plugin_registry() -> PluginRegistry:
    if _registry is None:
        raise RuntimeError("PluginRegistry not initialized — call set_plugin_registry()")
    return _registry


__all__ = ["PluginRegistry", "set_plugin_registry", "get_plugin_registry"]


