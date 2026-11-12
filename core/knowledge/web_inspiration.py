"""Web Inspiration — orchestration Core de recherche web enrichie (Core-owned).

Réutilise exclusivement les capacités existantes du Core, aucune infrastructure
nouvelle :
- ``WebSearchManager``  (core.knowledge.web_search)  : recherche multi-moteurs ;
- ``WebIngestionManager`` (core.knowledge.web_ingest) : crawl contrôlé (robots,
  SSRF, bornes) et extraction de contenu ;
- ``ProviderManager`` optionnel (core.llm)           : synthèse LLM des sources.

Règles d'architecture (AGENTS.md) :
- le moteur vit dans le Core : il doit fonctionner sans WebUI/API/CLI ;
- aucune interface ne définit la logique : elles affichent le résultat ;
- best-effort : un moteur en échec n'empêche pas la réponse.

Le pipeline ``inspire()`` :
1. recherche multi-moteurs de la requête (snippets + URLs) ;
2. crawl ciblé des meilleures URLs (preview transient, jamais persisté) ;
3. synthèse optionnelle par LLM (si un provider_manager est fourni).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Bornes : le pipeline reste léger et politesse envers les sites cibles.
DEFAULT_MAX_SOURCES = 6
DEFAULT_CRAWL_PAGES_PER_URL = 1
DEFAULT_DEPTH = 1
MAX_SEARCH_PER_MOTEUR = 5
MAX_SOURCES_HARD_CAP = 15


class WebInspirationEngine:
    """Orchestrateur de recherche web enrichie — propriété exclusive du Core."""

    def __init__(
        self,
        *,
        web_search: Any,
        web_ingest: Any,
        provider_manager: Any | None = None,
        max_sources: int = DEFAULT_MAX_SOURCES,
        synthesize: bool = True,
    ) -> None:
        """Args:
        web_search: Instance de ``WebSearchManager`` (Core).
        web_ingest: Instance de ``WebIngestionManager`` (Core).
        provider_manager: ``ProviderManager`` optionnel pour la synthèse LLM.
        max_sources: Nombre maximal de sources retenues pour le crawl.
        synthesize: Valeur par défaut de la synthèse LLM dans ``inspire``.
        """
        self._search = web_search
        self._ingest = web_ingest
        self._providers = provider_manager
        self._max_sources = min(max(1, int(max_sources)), MAX_SOURCES_HARD_CAP)
        self._synthesize = bool(synthesize)

    def set_provider_manager(self, provider_manager: Any | None) -> None:
        """Injecte le ProviderManager (synthèse LLM) — appelé au startup.

        Le moteur est créé avant le ProviderManager (ordre d'initialisation de
        l'API) : cette méthode permet de le brancher a posteriori, comme le
        fait le ChatPipeline.
        """
        self._providers = provider_manager

    # ── Pipeline public ─────────────────────────────────────────────────────

    async def inspire(
        self,
        topic: str,
        engines: list[str] | None = None,
        max_sources: int | None = None,
        synthesize: bool | None = None,
    ) -> dict[str, Any]:
        """Recherche enrichie : sources crawlées + synthèse (optionnelle).

        Returns:
            dict avec :
            - ``topic`` : requête normalisée ;
            - ``sources`` : sources retenues (url, title, snippet, error,
              pages du crawl) ;
            - ``summary`` : synthèse LLM si activée et disponible ;
            - ``stats`` : moteurs interrogés, temps, erreurs.
        """
        import time

        topic = (topic or "").strip()
        if not topic:
            raise ValueError("Topic de recherche vide")

        limit = min(
            self._max_sources if max_sources is None else int(max_sources),
            MAX_SOURCES_HARD_CAP,
        )
        started = time.monotonic()

        # 1. Recherche multi-moteurs (best-effort, peut retourner vide).
        engines = (engines or ["duckduckgo", "bing"])[:2]
        responses = await self._search.search_multiple(
            topic,
            engines=engines,
            max_results_per_engine=MAX_SEARCH_PER_MOTEUR,
        )
        seen: dict[str, dict[str, Any]] = {}
        for engine, resp in responses.items():
            if resp.metadata.get("error"):
                logger.warning(
                    "WebInspiration: moteur %s en échec: %s",
                    engine,
                    resp.metadata["error"],
                )
            for result in resp.results:
                if result.url and result.url not in seen:
                    seen[result.url] = {
                        "url": result.url,
                        "title": result.title,
                        "snippet": result.snippet,
                        "engine": engine,
                        "pages": [],
                        "error": None,
                    }
                if len(seen) >= limit:
                    break
            if len(seen) >= limit:
                break

        sources = list(seen.values())

        # 2. Crawl ciblé des sources (preview transient, jamais persisté).
        for source in sources:
            pages, error = await self._crawl_source(source["url"])
            source["pages"] = pages
            source["error"] = error

        # 3. Synthèse LLM optionnelle.
        summary = ""
        want_synthesis = self._synthesize if synthesize is None else bool(synthesize)
        if want_synthesis and self._providers is not None and sources:
            summary = await self._summarize(topic, sources)

        return {
            "topic": topic,
            "sources": sources,
            "summary": summary,
            "stats": {
                "engines": list(responses.keys()),
                "search_time_ms": int((time.monotonic() - started) * 1000),
                "sources_found": len(sources),
                "errors": [s["error"] for s in sources if s["error"]],
            },
        }

    # ── Étapes internes ─────────────────────────────────────────────────────

    async def _crawl_source(self, url: str) -> tuple[list[dict[str, Any]], str | None]:
        """Crawl contrôlé d'une URL (preview transient ; jamais persisté)."""
        try:
            preview = await self._ingest.scan(
                url,
                max_pages=DEFAULT_CRAWL_PAGES_PER_URL,
                max_depth=DEFAULT_DEPTH,
            )
            pages = [
                {
                    "url": p.get("url"),
                    "title": p.get("title"),
                    "status": p.get("status"),
                    "text": (p.get("text") or "")[:2000],
                }
                for p in preview.get("pages", [])
                if p.get("status") == "ok"
            ]
            return pages, None
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("WebInspiration: crawl échoué pour %s: %s", url, exc)
            return [], str(exc)

    async def _summarize(self, topic: str, sources: list[dict[str, Any]]) -> str:
        """Synthèse markdown sourcée (LLM) — best-effort."""
        try:
            from core.llm.types import ChatMessage

            corpus = "\n\n".join(
                f"[{i + 1}] {s['title']}\n{s['snippet'][:400]}" for i, s in enumerate(sources)
            )
            if not corpus:
                return ""
            default = await self._providers.get_default_provider()
            pid = default.get("provider_id") if isinstance(default, dict) else None
            provider = self._providers._registry.get_provider(pid or "ollama")
            model = await self._providers.get_active_model(pid or "ollama")
            response = await provider.chat(
                [
                    ChatMessage(
                        role="system",
                        content=(
                            "Tu es un analyste d'inspiration. Rédige un texte court "
                            "en markdown (150-300 mots) qui synthétise la veille et "
                            "propose des pistes d'exploration, en citant les sources "
                            "[n]. Termine par une section 'Sources'."
                        ),
                    ),
                    ChatMessage(role="user", content=f"Thème : {topic}\n\nSources :\n{corpus}"),
                ],
                model=model,
                temperature=0.4,
            )
            if isinstance(response, str):
                return response
            content = getattr(response, "content", None)
            if content:
                return str(content)
            message = getattr(response, "message", None)
            if message:
                return str(getattr(message, "content", "") or "")
            return ""
        except Exception as exc:  # noqa: BLE001 — la synthèse est best-effort
            logger.warning("WebInspiration: synthèse LLM échouée: %s", exc)
            return ""

    # ── Capabilité lightweight ──────────────────────────────────────────────

    async def search_only(self, topic: str, engines: list[str] | None = None) -> dict[str, Any]:
        """Recherche seule (sans crawl ni synthèse) — pour les interfaces."""
        responses = await self._search.search_multiple(
            (topic or "").strip(),
            engines=engines or ["duckduckgo", "bing"],
            max_results_per_engine=MAX_SEARCH_PER_MOTEUR,
        )
        return {
            "topic": (topic or "").strip(),
            "engines": {engine: resp.to_dict() for engine, resp in responses.items()},
        }


__all__ = [
    "DEFAULT_MAX_SOURCES",
    "MAX_SOURCES_HARD_CAP",
    "WebInspirationEngine",
]
