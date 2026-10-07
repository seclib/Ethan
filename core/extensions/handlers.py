"""Adaptateurs de type — le point de contact avec chaque système d'origine.

Règle structurante : le gestionnaire unifié ne réimplémente JAMAIS la
sémantique d'un type. Chaque adaptateur délègue au système existant
(`CapabilityManager`, `PluginRegistry`, `CookbookManager`) et se contente de :

1. traduire le vocabulaire de l'API unifiée vers celui du système ;
2. fournir une description uniforme au gestionnaire commun.

C'est ce qui permet de mutualiser installation / lifecycle / persistence /
erreurs sans dissoudre les différences réelles entre un composant Docker et une
recette de Cookbook.
"""

from __future__ import annotations

import logging
from typing import Any

from core.extensions.types import ExtensionKind, ExtensionSpec, ExtensionState

logger = logging.getLogger(__name__)

# Domaine de persistance des plugins (meme source de verite que
# `core.plugins.registry._DOMAIN`) : eviter que les deux couches divergent.
_PLUGIN_DOMAIN = "webui_plugins"


class ExtensionHandler:
    """Interface commune à tout type d'extension.

    Le gestionnaire commun n'appelle que ces méthodes ; il ne connaît jamais le
    système sous-jacent.
    """

    kind: str = ""

    # ── Catalogue ────────────────────────────────────────────────────────
    async def discover(self) -> list[ExtensionSpec]:
        """Toutes les extensions connues de ce type, quel que soit leur état."""
        raise NotImplementedError

    # ── Cycle de vie ─────────────────────────────────────────────────────
    async def install(self, ext_id: str, config: dict[str, Any]) -> str:
        """Lance l'installation. Retourne un `operation_id` (jamais bloqué)."""
        raise NotImplementedError

    async def uninstall(self, ext_id: str, delete_data: bool) -> str:
        raise NotImplementedError

    async def enable(self, ext_id: str) -> None:
        raise NotImplementedError

    async def disable(self, ext_id: str) -> None:
        raise NotImplementedError

    async def configure(self, ext_id: str, config: dict[str, Any]) -> None:
        raise NotImplementedError

    # ── Observabilité ────────────────────────────────────────────────────
    async def status(self, ext_id: str) -> dict[str, Any]:
        """État brut du système d'origine (source de vérité)."""
        raise NotImplementedError

    async def logs(self, ext_id: str, tail: int = 200) -> dict[str, Any]:
        raise NotImplementedError


# ── Capability ───────────────────────────────────────────────────────────────


class CapabilityHandler(ExtensionHandler):
    """Délègue au `CapabilityManager` — seul type avec un vrai runtime.

    Le CapabilityManager garde la maîtrise de son propre cycle de vie (backend,
    santé, machine à états détaillée) ; l'adaptateur ne fait que mapper son
    vocabulaire vers les états unifiés. Aucune logique d'installation n'est
    dupliquée ici.
    """

    kind = ExtensionKind.CAPABILITY

    # Mapping CapabilityState (12 états, riches) → ExtensionState (10 états).
    _STATE_MAP = {
        "SUPPORTED": ExtensionState.AVAILABLE,
        "NOT_INSTALLED": ExtensionState.AVAILABLE,
        "INSTALLING": ExtensionState.INSTALLING,
        "INSTALLED": ExtensionState.INSTALLED,
        "STARTING": ExtensionState.ENABLING,
        "RUNNING": ExtensionState.ENABLED,
        "READY": ExtensionState.ENABLED,
        "STOPPED": ExtensionState.DISABLED,
        "UNHEALTHY": ExtensionState.ERROR,
        "CONFIGURATION_REQUIRED": ExtensionState.INSTALLED,
        "UNINSTALLING": ExtensionState.UNINSTALLING,
        "ERROR": ExtensionState.ERROR,
    }

    def __init__(self, manager: Any) -> None:
        self._manager = manager

    @classmethod
    def state_map(cls) -> dict[str, str]:
        """Mapping `CapabilityState` → `ExtensionState` (source de vérité : Core).

        Exposé pour que le gestionnaire unifié ne duplique pas la table : une
        capacité reste décrite par SON vocabulaire, jamais réécrit ici.
        """
        return dict(cls._STATE_MAP)

    def _to_unified(self, raw: dict[str, Any]) -> str:
        return self._STATE_MAP.get(str(raw.get("state", "")), ExtensionState.AVAILABLE)

    async def discover(self) -> list[ExtensionSpec]:
        specs = []
        for status in await self._manager.status_all():
            spec = status.get("spec") or {}
            cap_type = spec.get("type", "service")
            specs.append(
                ExtensionSpec(
                    id=str(spec.get("id") or status.get("id")),
                    kind=self.kind,
                    name=str(spec.get("name") or status.get("id")),
                    version=str(spec.get("version") or "0.0.0"),
                    description=str(spec.get("description") or ""),
                    source="builtin",
                    icon="Server",
                    categories=(str(cap_type),),
                    updatable=True,
                    plannable=True,
                    payload=spec,
                )
            )
        return specs

    async def install(self, ext_id: str, config: dict[str, Any]) -> str:
        return str(await self._manager.install(ext_id, config or {}))

    async def uninstall(self, ext_id: str, delete_data: bool) -> str:
        return str(await self._manager.uninstall(ext_id, delete_data=delete_data))

    async def enable(self, ext_id: str) -> None:
        await self._manager.enable(ext_id)

    async def disable(self, ext_id: str) -> None:
        await self._manager.disable(ext_id)

    async def configure(self, ext_id: str, config: dict[str, Any]) -> None:
        await self._manager.configure(ext_id, config)

    async def status(self, ext_id: str) -> dict[str, Any]:
        return dict(await self._manager.status(ext_id))

    async def logs(self, ext_id: str, tail: int = 200) -> dict[str, Any]:
        return dict(await self._manager.logs(ext_id, tail=tail))

    async def get_operation(self, op_id: str) -> dict[str, Any] | None:
        return await self._manager.get_operation(op_id)

    async def cancel_operation(self, op_id: str) -> bool:
        return bool(await self._manager.cancel_operation(op_id))

    async def plan(self, ext_id: str, uninstall: bool = False) -> dict[str, Any] | None:
        """Plan de mutation, quand le type sait en produire un."""
        try:
            if uninstall:
                plan = await self._manager.plan_uninstall(ext_id)
            else:
                plan = await self._manager.plan_install(ext_id)
        except Exception as exc:  # noqa: BLE001 — un plan absent n'est pas bloquant
            logger.debug("Capability %s: plan indisponible (%s)", ext_id, exc)
            return None
        return plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)


# ── Plugin ───────────────────────────────────────────────────────────────────


class PluginHandler(ExtensionHandler):
    """Délègue au `PluginRegistry` — manifeste déclaratif, sans runtime.

    Le plugin n'installe rien : il *référence* des outils / skills / MCP déjà
    présents. Son « installation » consiste donc à créer un enregistrement
    persisté. L'adaptateur MUST NOT inventer de runtime pour ce type.

    Le registre ne produisant pas d'`operation_id` (opération synchrone),
    l'adaptateur renvoie une chaîne vide : le gestionnaire unifié reconnaît
    alors l'opération comme « déjà terminée » et n'attend rien du client.
    """

    kind = ExtensionKind.PLUGIN

    def __init__(self, registry: Any) -> None:
        self._registry = registry

    async def discover(self) -> list[ExtensionSpec]:
        specs = []
        for plugin in await self._registry.list_plugins():
            specs.append(
                ExtensionSpec(
                    id=str(plugin.get("id")),
                    kind=self.kind,
                    name=str(plugin.get("name") or plugin.get("id")),
                    version=str(plugin.get("version") or "0.0.0"),
                    description=str(plugin.get("description") or ""),
                    source=str(plugin.get("source") or "builtin"),
                    icon=str(plugin.get("icon") or "Puzzle"),
                    categories=tuple(plugin.get("categories") or ()),
                    updatable=True,
                    plannable=False,
                    payload=plugin,
                )
            )
        return specs

    async def install(self, ext_id: str, config: dict[str, Any]) -> str:
        await self._registry.install(ext_id)
        return ""

    async def uninstall(self, ext_id: str, delete_data: bool) -> str:
        await self._registry.uninstall(ext_id, remove_data=delete_data)
        return ""

    async def enable(self, ext_id: str) -> None:
        await self._registry.enable(ext_id)

    async def disable(self, ext_id: str) -> None:
        await self._registry.disable(ext_id)

    async def configure(self, ext_id: str, config: dict[str, Any]) -> None:
        # Un plugin n'a pas de backend : sa configuration non secrète est
        # fusionnée dans son enregistrement persisté (les secrets restent
        # dans la couche secret manager, jamais ici).
        store = self._registry._store  # noqa: SLF001 — store du Core
        current = await store.get(_PLUGIN_DOMAIN, ext_id) or {}
        merged = {**(current.get("config") or {}), **config}
        await store.save(_PLUGIN_DOMAIN, ext_id, {**current, "config": merged})

    async def status(self, ext_id: str) -> dict[str, Any]:
        for plugin in await self._registry.list_plugins():
            if plugin.get("id") == ext_id:
                return dict(plugin)
        return {}

    async def logs(self, ext_id: str, tail: int = 200) -> dict[str, Any]:
        # Un plugin n'execute rien : pas de logs de runtime a exposer.
        return {
            "logs": "",
            "lines": [],
            "note": "Un plugin declaratif n'execute aucun runtime : aucun log.",
        }

    async def get_operation(self, op_id: str) -> dict[str, Any] | None:
        return None

    async def cancel_operation(self, op_id: str) -> bool:
        return False


# ── Cookbook ─────────────────────────────────────────────────────────────────


class CookbookHandler(ExtensionHandler):
    """Délègue au `CookbookManager` — recette de records, sans runtime.

    Une recette n'exécute jamais de code : elle crée des prompts / skills /
    automations via les managers du Core, avec rollback atomique. L'adaptateur
    préserve cette propriété : aucun runtime n'est introduit, l'état unifié
    reflète uniquement la présence réelle de la recette installée.
    """

    kind = ExtensionKind.COOKBOOK

    def __init__(self, manager: Any) -> None:
        self._manager = manager

    async def discover(self) -> list[ExtensionSpec]:
        installed = {r.get("recipe_id") for r in await self._manager.list_installed()}
        specs = []
        for recipe in self._manager.list_recipes():
            rid = str(recipe.get("id"))
            specs.append(
                ExtensionSpec(
                    id=rid,
                    kind=self.kind,
                    name=str(recipe.get("name") or rid),
                    version=str(recipe.get("version") or "0.0.0"),
                    description=str(recipe.get("description") or ""),
                    source="builtin",
                    icon="ChefHat",
                    categories=("recipe",),
                    updatable=False,
                    plannable=False,
                    payload={"installed": rid in installed},
                )
            )
        return specs

    async def install(self, ext_id: str, config: dict[str, Any]) -> str:
        await self._manager.install(ext_id)
        return ""

    async def uninstall(self, ext_id: str, delete_data: bool) -> str:
        await self._manager.uninstall(ext_id)
        return ""

    async def enable(self, ext_id: str) -> None:
        """Une recette n'a pas d'activation propre : on ne simule rien."""
        raise NotImplementedError("Les recettes Cookbook n'ont pas d'activation")

    async def disable(self, ext_id: str) -> None:
        raise NotImplementedError("Les recettes Cookbook n'ont pas de desactivation")

    async def configure(self, ext_id: str, config: dict[str, Any]) -> None:
        raise NotImplementedError("Les recettes Cookbook n'ont pas de configuration")

    async def status(self, ext_id: str) -> dict[str, Any]:
        for record in await self._manager.list_installed():
            if record.get("recipe_id") == ext_id:
                return dict(record)
        return {}

    async def logs(self, ext_id: str, tail: int = 200) -> dict[str, Any]:
        return {
            "logs": "",
            "lines": [],
            "note": "Une recette n'execute aucun runtime : aucun log.",
        }

    async def get_operation(self, op_id: str) -> dict[str, Any] | None:
        return None

    async def cancel_operation(self, op_id: str) -> bool:
        return False
