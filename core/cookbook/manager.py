"""Core-owned Cookbook — recipe manifests that install ETHAN records.

A recipe NEVER executes code: it only creates validated records
(prompts / skills / automations) through the existing Core managers.
RFC-0003.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_ALLOWED_INSTALL_KEYS = {"prompt", "skill", "automation"}
_KNOWN_REQUIRE_KEYS = {"skill", "tool", "mcp", "model", "knowledge"}


class CookbookError(ValueError):
    """Invalid recipe manifest."""


class CookbookManager:
    """Load, validate, install and uninstall workflow recipes."""

    _INSTALLED_DOMAIN = "cookbook-installed"

    def __init__(
        self,
        *,
        recipes_dir: str,
        skill_store: Any,
        prompt_manager: Any,
        automation_manager: Any,
        store: CoreRecordStore | None = None,
    ) -> None:
        self._recipes_dir = recipes_dir
        self._skills = skill_store
        self._prompts = prompt_manager
        self._automations = automation_manager
        self._store = store or CoreRecordStore()

    # ── Manifests ────────────────────────────────────────────────────────

    def _load_manifest(self, recipe_id: str) -> dict[str, Any]:
        path = os.path.join(self._recipes_dir, f"{recipe_id}.json")
        if not os.path.isfile(path):
            raise CookbookError(f"Recipe '{recipe_id}' not found")
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        self._validate(manifest)
        return manifest

    def list_recipes(self) -> list[dict[str, Any]]:
        recipes: list[dict[str, Any]] = []
        if not os.path.isdir(self._recipes_dir):
            return recipes
        for filename in sorted(os.listdir(self._recipes_dir)):
            if not filename.endswith(".json"):
                continue
            try:
                with open(os.path.join(self._recipes_dir, filename), encoding="utf-8") as fh:
                    manifest = json.load(fh)
                self._validate(manifest)
                recipes.append(self._summarize(manifest))
            except Exception as exc:  # noqa: BLE001 — one bad file must not break the gallery
                logger.warning("Cookbook: skipping invalid recipe %s: %s", filename, exc)
        return recipes

    @staticmethod
    def _validate(manifest: dict[str, Any]) -> None:
        for key in ("id", "name", "version", "installs"):
            if not manifest.get(key):
                raise CookbookError(f"Manifest missing key '{key}'")
        installs = manifest["installs"]
        if not isinstance(installs, dict) or not installs:
            raise CookbookError("'installs' must be a non-empty object")
        unknown = set(installs) - _ALLOWED_INSTALL_KEYS
        if unknown:
            raise CookbookError(f"Unsupported install kinds: {sorted(unknown)}")
        requires = manifest.get("requires", {})
        if not isinstance(requires, dict):
            raise CookbookError("'requires' must be an object")
        unknown_req = set(requires) - _KNOWN_REQUIRE_KEYS
        if unknown_req:
            raise CookbookError(f"Unsupported requirement kinds: {sorted(unknown_req)}")

    def get_recipe(self, recipe_id: str) -> dict[str, Any]:
        """Full recipe detail: metadata, requires and the complete install plan."""
        manifest = self._load_manifest(recipe_id)
        detail = self._summarize(manifest)
        # Tags agrégés depuis les prompts installés (métadonnées de galerie).
        tags = {
            tag
            for item in manifest["installs"].get("prompt", [])
            for tag in item.get("tags", [])
        }
        detail["tags"] = sorted(tags)
        detail["installs"] = manifest["installs"]
        return detail

    @staticmethod
    def _summarize(manifest: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": manifest["id"],
            "name": manifest["name"],
            "version": manifest["version"],
            "description": manifest.get("description", ""),
            "requires": manifest.get("requires", {}),
            "installs_summary": {k: len(v) for k, v in manifest["installs"].items()},
        }

    # ── Installed registry ───────────────────────────────────────────────

    async def list_installed(self) -> list[dict[str, Any]]:
        return await self._store.list(self._INSTALLED_DOMAIN)

    async def _installed_record(self, recipe_id: str) -> dict[str, Any] | None:
        try:
            return await self._store.get(self._INSTALLED_DOMAIN, recipe_id)
        except Exception:  # noqa: BLE001
            return None

    # ── Install / uninstall ──────────────────────────────────────────────

    async def install(self, recipe_id: str) -> dict[str, Any]:
        manifest = self._load_manifest(recipe_id)
        existing = await self._installed_record(recipe_id)
        if existing:
            raise CookbookError(f"Recipe '{recipe_id}' is already installed")

        created: list[tuple[str, Any]] = []  # (kind, record_id)
        try:
            for item in manifest["installs"].get("prompt", []):
                rec = await self._prompts.create(
                    name=item.get("name", "recipe-prompt"),
                    text=item.get("text", ""),
                    description=item.get("description", ""),
                    tags=list(item.get("tags", [])) + [f"cookbook:{recipe_id}"],
                )
                created.append(("prompt", rec["id"]))

            for item in manifest["installs"].get("skill", []):
                rec = await self._skills.create_skill({
                    "name": item.get("name", "recipe-skill"),
                    "description": item.get("description", ""),
                    "content": item.get("content", ""),
                    "version": item.get("version", "1.0.0"),
                    "metadata": {"cookbook_recipe": recipe_id},
                })
                created.append(("skill", rec["id"]))

            for item in manifest["installs"].get("automation", []):
                rec = await self._automations.create(
                    name=item.get("name", "recipe-automation"),
                    trigger=dict(item.get("trigger", {})),
                    actions=list(item.get("actions", [])),
                    description=item.get("description", ""),
                )
                created.append(("automation", rec["id"]))

        except Exception as exc:
            # Rollback atomique : supprimer ce qui a déjà été créé
            for kind, record_id in reversed(created):
                try:
                    if kind == "prompt":
                        await self._prompts.delete(record_id)
                    elif kind == "skill":
                        await self._skills.delete_skill(record_id)
                    elif kind == "automation":
                        await self._automations.delete(record_id)
                except Exception:  # noqa: BLE001
                    logger.exception("Cookbook rollback failed for %s/%s", kind, record_id)
            raise CookbookError(f"Install failed, rolled back: {exc}") from exc

        record = {
            "recipe_id": recipe_id,
            "version": manifest["version"],
            "created": [{"kind": k, "id": i} for k, i in created],
        }
        await self._store.save(self._INSTALLED_DOMAIN, recipe_id, record)
        logger.info("Cookbook: installed recipe '%s' (%d records)", recipe_id, len(created))
        return record

    async def uninstall(self, recipe_id: str) -> bool:
        record = await self._installed_record(recipe_id)
        if not record:
            return False
        for item in record.get("created", []):
            kind, record_id = item.get("kind"), item.get("id")
            try:
                if kind == "prompt":
                    await self._prompts.delete(record_id)
                elif kind == "skill":
                    await self._skills.delete_skill(record_id)
                elif kind == "automation":
                    await self._automations.delete(record_id)
            except Exception:  # noqa: BLE001 — l'enregistrement a peut-être été supprimé à la main
                logger.warning("Cookbook uninstall: could not remove %s/%s", kind, record_id)
        await self._store.delete(self._INSTALLED_DOMAIN, recipe_id)
        logger.info("Cookbook: uninstalled recipe '%s'", recipe_id)
        return True