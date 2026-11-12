"""Skill validation — vérification des outils requis (Core-owned).

Une skill persistée peut déclarer des outils (``required_tools`` et
``steps[].tool_id``).  Ces déclarations sont validées contre le
ToolManager Core **au moment de la sauvegarde** : l'API refuse (422)
toute skill référençant un outil inexistant — aucun lien fantôme.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def collect_unknown_tools(
    required_tools: list[str] | None,
    steps: list[dict[str, Any]] | None,
    tool_manager: Any | None,
) -> list[str]:
    """Retourne les ids d'outils déclarés mais inconnus du ToolManager.

    Args:
        required_tools: ids déclarés au niveau de la skill.
        steps: étapes pipeline (chaque step peut porter ``tool_id``).
        tool_manager: ToolManager Core injecté (peut être None — dans ce
            cas la validation est neutralisée, fail-open, pour ne pas
            bloquer les environnements sans tools).

    Returns:
        Liste triée des ids inconnus (vide si tout est connu).
    """
    if tool_manager is None:
        return []
    try:
        known = {tool.tool_id for tool in tool_manager.list_tools()}
    except Exception as exc:  # pragma: no cover - ToolManager défectueux
        logger.warning("Tool validation skipped (ToolManager error): %s", exc)
        return []

    wanted: set[str] = set()
    for tool_id in required_tools or []:
        if tool_id:
            wanted.add(str(tool_id))
    for step in steps or []:
        if isinstance(step, dict) and step.get("tool_id"):
            wanted.add(str(step["tool_id"]))
    return sorted(w for w in wanted if w not in known)


__all__ = ["collect_unknown_tools"]
