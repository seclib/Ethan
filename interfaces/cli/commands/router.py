"""CLI command: ethan router <task> — Router LLM.

Usage:
    ethan router reasoning       # GPT / Claude (complexe)
    ethan router code           # Claude / GPT (code)
    ethan router fast           # Modèle rapide
    ethan router local          # Modèle local hors-ligne

Le routage est une décision métier du Core : la commande ne fait qu'il
lui demander le modèle retenu via l'API (`/model-routers`), en passant la
liste des modèles réellement publiés par le Core (`/models`). Aucune règle de
sélection n'est réimplémentée ici, et aucun catalogue de modèles n'est
figé dans le CLI.
"""

from __future__ import annotations

from typing import Any

from interfaces.cli.core import colors as clr
from interfaces.cli.core.api import api_get, api_post
from interfaces.cli.core.errors import CLIError
from interfaces.cli.registry import register


#: Catégories annoncées par défaut si l'API ne répond pas (usage seul).
FALLBACK_CATEGORIES: tuple[str, ...] = ("reasoning", "code", "fast", "local")


def _categories() -> list[str]:
    """Catégories de routage publiées par le Core."""
    try:
        payload = api_get("/model-routers")
    except CLIError:
        return list(FALLBACK_CATEGORIES)
    if isinstance(payload, dict):
        cats = payload.get("categories")
        if isinstance(cats, list):
            return [str(item) for item in cats]
    return list(FALLBACK_CATEGORIES)


def _available_models() -> list[dict[str, Any]]:
    """Modèles publiés par le Core (source unique de vérité)."""
    payload = api_get("/models")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("models", "items"):
            items = payload.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


@register(
    "router",
    group="core",
    description="Route LLM — choisit le meilleur modèle pour une tâche",
    usage="ethan router <reasoning|code|fast|local>",
)
def cmd_router(args: list[str]) -> int:
    """Affiche le meilleur modèle pour une catégorie de tâche.

    Args:
        args: [category]

    Returns:
        0 si succès, 1 si erreur
    """
    categories = _categories()

    if not args:
        print(f"\n  {clr.C.CYAN}Usage:{clr.C.RESET} ethan router <task>")
        print(f"  {clr.C.CYAN}Tasks:{clr.C.RESET}  {', '.join(categories)}")
        print()
        return 0

    task = args[0].lower()
    if task not in categories:
        print(f"\n  {clr.C.CYAN}Unknown task:{clr.C.RESET} {task}")
        print(f"  {clr.C.CYAN}Tasks:{clr.C.RESET}  {', '.join(categories)}")
        print()
        return 1

    models = _available_models()
    if not models:
        print(f"\n  {clr.C.YELLOW}No model published by the Core — nothing to route.{clr.C.RESET}")
        print()
        return 0

    payload = api_post("/model-routers/route", {"task": task, "available_models": models})
    selected = ""
    if isinstance(payload, dict):
        selected = str(payload.get("selected_model_name") or payload.get("selected_model_id") or "")

    if not selected:
        print(f"\n  {clr.C.YELLOW}No model matched task '{task}'.{clr.C.RESET}")
        print()
        return 0

    print(selected)
    return 0
