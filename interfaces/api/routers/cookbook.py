"""Cookbook API — thin bindings over core.cookbook.manager. RFC-0003."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/cookbook", tags=["cookbook"])

_manager: Any | None = None


def set_cookbook_manager(manager: Any) -> None:
    global _manager
    _manager = manager


def _require() -> Any:
    if _manager is None:
        raise HTTPException(503, "Cookbook manager not initialized")
    return _manager


@router.get("/recipes")
async def list_recipes():
    manager = _require()
    recipes = manager.list_recipes()
    installed = {r.get("recipe_id") for r in await manager.list_installed()}
    for recipe in recipes:
        recipe["installed"] = recipe["id"] in installed
    return recipes


@router.get("/installed")
async def list_installed():
    return await _require().list_installed()


@router.post("/install/{recipe_id}")
async def install_recipe(recipe_id: str):
    try:
        return await _require().install(recipe_id)
    except ValueError as exc:
        raise HTTPException(409 if "already" in str(exc) else 422, str(exc)) from exc


@router.delete("/install/{recipe_id}")
async def uninstall_recipe(recipe_id: str):
    removed = await _require().uninstall(recipe_id)
    if not removed:
        raise HTTPException(404, f"Recipe '{recipe_id}' is not installed")
    return {"status": "uninstalled", "recipe_id": recipe_id}