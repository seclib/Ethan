"""Core-owned Deep Research — multi-step search & synthesis. RFC-0002.

Reuses existing ETHAN capabilities only:
  - ProviderManager (default LLM) for query planning and synthesis
  - ToolManager.execute_by_capability('search') for web_search
No new backend service is created.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class DeepResearchEngine:
    """Iterative plan → search → synthesize pipeline owned by Core."""

    def __init__(self, *, provider_manager: Any, tool_manager: Any, max_sources: int = 12) -> None:
        self._providers = provider_manager
        self._tools = tool_manager
        self._max_sources = max_sources

    # ── LLM helper ───────────────────────────────────────────────────────

    async def _chat(self, system: str, user: str) -> str:
        from core.llm.types import ChatMessage

        default = await self._providers.get_default_provider()
        pid = default.get("provider_id") if isinstance(default, dict) else None
        provider = self._providers._registry.get_provider(pid or "ollama")
        model = await self._providers.get_active_model(pid or "ollama")
        response = await provider.chat(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=user),
            ],
            model=model,
            temperature=0.3,
        )
        # ChatResponse (dataclass), dict ou str selon le provider
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            msg = response.get("message") or {}
            return str(msg.get("content") if isinstance(msg, dict) else msg
                       or response.get("content", ""))
        content = getattr(response, "content", None)
        if content:
            return str(content)
        message = getattr(response, "message", None)
        return str(getattr(message, "content", "") or "")

    # ── Search helper ────────────────────────────────────────────────────

    async def _search(self, query: str) -> list[dict[str, Any]]:
        try:
            context = self._make_context()
            result = await self._tools.execute_by_capability("search", {"query": query}, context)
            if getattr(result, "status", "") != "success":
                return []
            data = getattr(result, "result", None) or getattr(result, "data", None) or []
            return self._normalize_sources(data)
        except Exception as exc:  # noqa: BLE001 — la recherche est best-effort
            logger.warning("DeepResearch: search failed for %r: %s", query, exc)
            return []

    @staticmethod
    def _make_context() -> Any:
        from core.tools.types import ToolContext
        try:
            return ToolContext(user_id="deep-research")
        except TypeError:
            return ToolContext()

    @staticmethod
    def _normalize_sources(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                return [{"title": data[:120], "snippet": data, "url": ""}]
        if isinstance(data, dict):
            data = data.get("results", data.get("items", []))
        out: list[dict[str, Any]] = []
        for item in list(data or []):
            if isinstance(item, str):
                out.append({"title": item[:120], "snippet": item, "url": ""})
            elif isinstance(item, dict):
                out.append({
                    "title": str(item.get("title", ""))[:200],
                    "snippet": str(item.get("snippet", item.get("content", "")))[:600],
                    "url": str(item.get("url", item.get("link", ""))),
                })
        return out

    # ── Public pipeline ──────────────────────────────────────────────────

    async def run(self, query: str, depth: int = 2) -> dict[str, Any]:
        depth = max(1, min(int(depth), 4))
        steps: list[dict[str, Any]] = []
        all_sources: dict[str, dict[str, Any]] = {}

        # 1. Plan : générer `depth` sous-questions distinctes
        plan_raw = await self._chat(
            "Tu es un planificateur de recherche. Réponds UNIQUEMENT par une liste "
            "JSON de sous-questions (tableau de chaînes), sans autre texte.",
            f"Question de recherche : {query}\nGénère exactement {depth} sous-queries.",
        )
        subqueries = self._parse_queries(plan_raw, query, depth)

        # 2. Recherche par sous-question
        for sq in subqueries:
            sources = await self._search(sq)
            steps.append({"step": len(steps) + 1, "query": sq, "sources_found": len(sources)})
            for src in sources:
                key = src.get("url") or src.get("title", "")
                if key and key not in all_sources:
                    all_sources[key] = src
                if len(all_sources) >= self._max_sources:
                    break
            if len(all_sources) >= self._max_sources:
                break

        # 3. Synthèse sourcée
        corpus = "\n\n".join(
            f"[{i + 1}] {s['title']}\n{s['snippet']}"
            for i, s in enumerate(list(all_sources.values())[: self._max_sources])
        ) or "(aucune source trouvée)"
        report = await self._chat(
            "Tu es un analyste de recherche. Rédige un rapport structuré en markdown "
            "qui répond à la question en citant les sources sous la forme [n]. "
            "Termine par une section 'Sources'.",
            f"Question : {query}\n\nSources :\n{corpus}",
        )

        return {
            "query": query,
            "depth": depth,
            "steps": steps,
            "sources": list(all_sources.values()),
            "report": report,
        }

    @staticmethod
    def _parse_queries(raw: str, fallback: str, depth: int) -> list[str]:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    queries = [str(q).strip() for q in parsed if str(q).strip()]
                    if queries:
                        return queries[:depth]
            except ValueError:
                pass
        lines = [ln.strip("-•0123456789. ") for ln in raw.splitlines() if ln.strip()]
        queries = [ln for ln in lines if 5 < len(ln) < 300][:depth]
        return queries or [fallback]