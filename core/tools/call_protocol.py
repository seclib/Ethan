"""Protocole d'appel d'outils balisé — Core-owned.

Le LLM émet, lorsque des outils sont sélectionnés :

    <tool name="nom_outil">{"parametre": "valeur"}</tool>

Le parsing appartient au Core (AGENTS.md : la logique métier n'appartient
jamais à une interface). Ce module est la SOURCE UNIQUE partagée par :

- ``interfaces/api/routers/v1.py``     : boucle de streaming du chat ;
- ``core/chat/pipeline.py``            : exécution via ToolManager ;
- ``core/agents/executor.py``          : boucle d'outils des agents.

(Un doublon de regex ici serait un doublon de protocole — interdit.)
"""

from __future__ import annotations

import json
import re
from typing import Any

TOOL_CALL_RE = re.compile(
    r'<tool\s+name=["\']([^"\']+)["\']\s*>\s*(.*?)\s*</tool>',
    re.DOTALL,
)


def parse_tool_calls(content: str) -> list[dict[str, Any]]:
    """Extrait les appels d'outils balisés d'une réponse LLM.

    Returns:
        Liste de ``{"name": ..., "params": {...}}`` — un entry par bloc
        ``<tool>``. Un payload non-JSON devient ``{"raw": ...}`` (jamais
        d'exception propagée vers la boucle de génération).
    """
    calls: list[dict[str, Any]] = []
    for match in TOOL_CALL_RE.finditer(content or ""):
        raw = (match.group(2) or "{}").strip() or "{}"
        try:
            params = json.loads(raw)
            if not isinstance(params, dict):
                params = {"value": params}
        except Exception:
            params = {"raw": raw}
        calls.append({"name": match.group(1), "params": params})
    return calls


def strip_tool_blocks(content: str, note_by_name: dict[str, str] | None = None) -> str:
    """Retire les blocs ``<tool>`` du contenu affiché, avec une note par appel."""

    def _repl(match: re.Match[str]) -> str:
        name = match.group(1)
        note = (note_by_name or {}).get(name, f"_[Outil « {name} » exécuté]_")
        return f"\n\n{note}\n\n"

    return TOOL_CALL_RE.sub(_repl, content or "")


__all__ = ["TOOL_CALL_RE", "parse_tool_calls", "strip_tool_blocks"]
