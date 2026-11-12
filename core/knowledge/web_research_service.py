"""Web Research Service — Core ETHAN.

Transforme des resultats de recherche Web en ressources Knowledge ETHAN :

    recherche Web -> resultats -> selection de pages -> recuperation du contenu
    -> extraction/nettoyage -> conservation des metadonnees -> ressource
    Knowledge -> pipeline RAG existant.

Ce service appartient au Core : il ne depend d'aucune interface et ne cree PAS
un second pipeline. Il reutilise l'existant :
- ``WebSearchManager`` pour la recherche (DuckDuckGo / Bing / Yandex, extensible) ;
- ``WebIngestionManager`` pour le scan + l'ingestion (robots.txt, SSRF, limite
  de taille, timeouts, extraction/nettoyage, alimentation RAG/Knowledge).

Contraintes appliquees :
- plafond absolu de 50 pages par collection (refus strict au-dela) ;
- l'appelant choisit le nombre de resultats recherches et les pages importees ;
- une page inaccessible ou un echec d'ingestion n'invalide pas la collection ;
- aucun contournement des mecanismes des sites (deja geres par l'ingestion).
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from core.knowledge.web_ingest import WebIngestionManager
from core.knowledge.web_search import (
    MAX_RESULTS_HARD_CAP,
    ProxyConfig,
    WebSearchManager,
    _dedup_key,
    validate_max_results,
)

logger = logging.getLogger(__name__)

#: Plafond absolu de pages importables par collection (aligne sur la recherche).
MAX_PAGES_PER_COLLECTION = MAX_RESULTS_HARD_CAP

DEFAULT_MAX_RESULTS_PER_ENGINE = 10
DEFAULT_TARGET = "knowledge"

STATUS_IMPORTED = "imported"
STATUS_UNREACHABLE = "unreachable"
STATUS_ERROR = "error"

_VALID_TARGETS = ("knowledge", "collection", "project")


def _domain_of(url: str) -> str:
    """Domaine nu d'une URL (prefixe ``www.`` retire), sans jamais lever."""
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def validate_max_pages(value: Any) -> int:
    """Valide un nombre de pages (1..50). Refus strict au-dela du plafond.

    Reutilise la validation du Core de recherche pour garantir une borne
    unique et coherente entre la recherche (pages cherchees) et l'import
    (pages conservees par collection).
    """
    return validate_max_results(value)


def _supported_kwargs(func: Callable[..., Any], candidates: Mapping[str, Any]) -> dict[str, Any]:
    """Ne conserve que les kwargs reellement supportes par ``func``.

    Tolerance d'evolution : si un parametre d'``WebIngestionManager``
    (``scan``/``ingest``) est renomme ou retire, le service continue de
    fonctionner avec la signature disponible plutot que de lever ``TypeError``.
    """
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):  # pragma: no cover - callables sans signature
        return dict(candidates)
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return dict(candidates)
    return {k: v for k, v in candidates.items() if k in params}


def _first_error(errors: Any) -> str:
    """Premier message d'erreur lisible d'un rapport de scan."""
    if not errors:
        return ""
    first = errors[0] if isinstance(errors, Sequence) else errors
    if isinstance(first, Mapping):
        return str(first.get("error") or first.get("message") or first)
    return str(first)


@dataclass
class CollectedPage:
    """Page candidate a l'import Knowledge (resultat de recherche enrichi)."""

    title: str
    url: str
    domain: str
    snippet: str = ""
    source_engine: str = ""
    rank: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "domain": self.domain,
            "snippet": self.snippet,
            "source_engine": self.source_engine,
            "rank": self.rank,
            "metadata": dict(self.metadata),
        }


@dataclass
class ResearchResult:
    """Resultat d'une recherche : pages dedupliquees pretes au choix utilisateur."""

    query: str
    engines: list[str] = field(default_factory=list)
    results: list[CollectedPage] = field(default_factory=list)
    total_found: int = 0
    max_results_per_engine: int = DEFAULT_MAX_RESULTS_PER_ENGINE
    truncated: bool = False
    errors: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "engines": list(self.engines),
            "results": [r.to_dict() for r in self.results],
            "total_found": self.total_found,
            "max_results_per_engine": self.max_results_per_engine,
            "truncated": self.truncated,
            "errors": dict(self.errors),
        }


def _empty_report(target: str) -> dict[str, Any]:
    """Rapport d'import vide (structure stable pour les interfaces)."""
    return {
        "target": target,
        "collection": None,
        "pages": [],
        "imported_count": 0,
        "unreachable_count": 0,
        "failed_count": 0,
        "skipped_duplicates": 0,
        "indexed_count": 0,
    }


class WebResearchService:
    """Recherche Web -> selection -> ressources Knowledge (100 % Core)."""

    def __init__(
        self,
        web_search: WebSearchManager,
        web_ingest: WebIngestionManager,
        *,
        max_results_per_engine: int = DEFAULT_MAX_RESULTS_PER_ENGINE,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._web_search = web_search
        self._web_ingest = web_ingest
        self._max_results_per_engine = validate_max_pages(max_results_per_engine)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def max_pages_per_collection(self) -> int:
        """Plafond absolu de pages importables par collection (50)."""
        return MAX_PAGES_PER_COLLECTION

    # -- 1. Recherche -------------------------------------------------------

    async def collect(
        self,
        query: str,
        engines: Sequence[str] | None = None,
        max_results_per_engine: int | None = None,
        proxy: ProxyConfig | str | None = None,
    ) -> ResearchResult:
        """Recherche un sujet et retourne les pages candidates dedupliquees.

        Raises:
            ValueError: query vide, nombre de resultats invalide (> 50, type
                incorrect, nul ou negatif) ou moteur inconnu.
        """
        query = (query or "").strip()
        if not query:
            raise ValueError("Query de recherche vide")
        limit = validate_max_pages(
            self._max_results_per_engine
            if max_results_per_engine is None
            else max_results_per_engine
        )
        selected = [e.strip().lower() for e in engines if (e or "").strip()] if engines else None
        responses = await self._web_search.search_multiple(
            query=query,
            engines=selected,
            max_results_per_engine=limit,
            proxy=proxy,
        )
        pages, errors = self._merge(responses)
        truncated = len(pages) > MAX_PAGES_PER_COLLECTION
        if truncated:
            logger.info(
                "Web research %r : %d candidats tronques a %d",
                query,
                len(pages),
                MAX_PAGES_PER_COLLECTION,
            )
            pages = pages[:MAX_PAGES_PER_COLLECTION]
        return ResearchResult(
            query=query,
            engines=list(responses.keys()),
            results=pages,
            total_found=len(pages),
            max_results_per_engine=limit,
            truncated=truncated,
            errors=errors,
        )

    @staticmethod
    def _merge(
        responses: Mapping[str, Any],
    ) -> tuple[list[CollectedPage], dict[str, str]]:
        """Fusionne les reponses des moteurs en pages dedupliquees."""
        merged: list[CollectedPage] = []
        errors: dict[str, str] = {}
        seen: set[str] = set()
        for engine, response in responses.items():
            error = (getattr(response, "metadata", None) or {}).get("error")
            if error:
                errors[engine] = str(error)
            for result in getattr(response, "results", None) or []:
                key = _dedup_key(result.url)
                if not key or key in seen:
                    continue
                seen.add(key)
                merged.append(
                    CollectedPage(
                        title=result.title,
                        url=result.url,
                        domain=getattr(result, "domain", "") or _domain_of(result.url),
                        snippet=result.snippet or "",
                        source_engine=result.source_engine or engine,
                        rank=len(merged) + 1,
                        metadata=dict(getattr(result, "metadata", None) or {}),
                    )
                )
        return merged, errors

    # -- 2. Import vers Knowledge ------------------------------------------

    async def import_page(
        self,
        url: str,
        *,
        title: str | None = None,
        domain: str | None = None,
        collection_name: str | None = None,
        target: str = "knowledge",
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Importe **une** page selectionnee comme ressource Knowledge."""
        url = (url or "").strip()
        if not url:
            raise ValueError("URL vide")
        ref = CollectedPage(title=title or url, url=url, domain=domain or _domain_of(url))
        return await self._import_urls(
            [ref],
            target=target,
            collection_name=collection_name,
            collection_id=None,
            project_id=project_id,
            user_id=user_id,
        )

    async def import_selection(
        self,
        pages: Sequence[CollectedPage | str],
        *,
        target: str = "collection",
        collection_name: str | None = None,
        collection_id: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Importe plusieurs pages selectionnees vers la destination choisie."""
        refs = [self._as_ref(page) for page in pages]
        return await self._import_urls(
            refs,
            target=target,
            collection_name=collection_name,
            collection_id=collection_id,
            project_id=project_id,
            user_id=user_id,
        )

    async def preview_page(self, url: str) -> dict[str, Any]:
        """Apercu transient d'une page candidate (scan isole, jamais persiste).

        Utilise par les interfaces pour l'action « Preview » : le Core
        effectue un scan controle (robots.txt, SSRF, bornes) et retourne le
        contenu extrait ; aucune indexation n'a lieu a ce stade.

        Raises:
            ValueError: URL vide ou scheme non http/https.
        """
        url = (url or "").strip()
        if not url.lower().startswith(("http://", "https://")):
            raise ValueError(f"URL invalide : {url!r} (scheme http/https attendu)")
        return await self._scan_one(url)

    async def collect_and_import(
        self,
        query: str,
        selected_urls: Sequence[str] | None = None,
        *,
        engines: Sequence[str] | None = None,
        max_results_per_engine: int | None = None,
        proxy: ProxyConfig | str | None = None,
        target: str | None = None,
        collection_name: str | None = None,
        collection_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Workflow complet : recherche -> selection -> import Knowledge.

        ``selected_urls`` restreint l'import aux pages reellement choisies par
        l'utilisateur ; a defaut, toutes les pages dedupliquees sont importees.
        """
        research = await self.collect(
            query,
            engines=engines,
            max_results_per_engine=max_results_per_engine,
            proxy=proxy,
        )
        chosen = self._select(research.results, selected_urls)
        effective_target = target or ("knowledge" if len(chosen) <= 1 else "collection")
        report = (
            await self._import_urls(
                chosen,
                target=effective_target,
                collection_name=collection_name,
                collection_id=collection_id,
                project_id=project_id,
            )
            if chosen
            else _empty_report(effective_target)
        )
        return {
            "query": research.query,
            "target": effective_target,
            "research": research.to_dict(),
            "import": report,
        }

    @staticmethod
    def _select(
        pages: Sequence[CollectedPage], selected_urls: Sequence[str] | None
    ) -> list[CollectedPage]:
        """Restreint les candidats aux pages choisies (ordre des resultats)."""
        if not selected_urls:
            return list(pages)
        wanted = {_dedup_key(u): u for u in selected_urls if u}
        # L'utilisateur ne peut choisir que parmi les resultats de recherche :
        # les URLs selectionnees absentes des resultats sont ignorees (le
        # rapport de recherche reste la source de verite de la selection).
        chosen = [p for p in pages if _dedup_key(p.url) in wanted]
        if len(chosen) > MAX_PAGES_PER_COLLECTION:
            raise ValueError(
                f"Selection de {len(chosen)} pages refusee : plafond absolu = "
                f"{MAX_PAGES_PER_COLLECTION} pages par collection"
            )
        return chosen

    @staticmethod
    def _as_ref(page: CollectedPage | str) -> CollectedPage:
        if isinstance(page, CollectedPage):
            return page
        url = str(page)
        return CollectedPage(title=url, url=url, domain=_domain_of(url))

    async def _import_urls(
        self,
        refs: Sequence[CollectedPage],
        *,
        target: str,
        collection_name: str | None,
        collection_id: str | None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Importe des pages selectionnees (best-effort, une par une)."""
        target = (target or DEFAULT_TARGET).strip().lower()
        if target not in _VALID_TARGETS:
            raise ValueError(
                f"target invalide : {target!r} (attendu : knowledge|collection|project)"
            )
        if target == "project" and not (project_id or "").strip():
            raise ValueError("Cible project : fournir project_id")
        if len(refs) > MAX_PAGES_PER_COLLECTION:
            raise ValueError(
                f"Import de {len(refs)} pages refuse : plafond absolu = "
                f"{MAX_PAGES_PER_COLLECTION} pages par collection"
            )

        unique: list[CollectedPage] = []
        seen: set[str] = set()
        for ref in refs:
            key = _dedup_key(ref.url)
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(ref)

        report = _empty_report(target)
        report["skipped_duplicates"] = len(refs) - len(unique)
        collection = {"id": collection_id} if collection_id else None
        for ref in unique:
            use_new_name = collection is None and target == "collection"
            outcome = await self._import_one(
                ref,
                target=target,
                collection_id=(collection or {}).get("id"),
                collection_name=collection_name,
                use_new_name=use_new_name,
                project_id=project_id,
                user_id=user_id,
            )
            report["pages"].append(outcome)
            if outcome["status"] == STATUS_IMPORTED:
                report["imported_count"] += 1
                report["indexed_count"] += outcome.get("indexed_count") or 0
                if outcome.get("collection"):
                    collection = outcome["collection"]
            elif outcome["status"] == STATUS_UNREACHABLE:
                report["unreachable_count"] += 1
            else:
                report["failed_count"] += 1
        report["collection"] = collection
        return report

    async def _import_one(
        self,
        ref: CollectedPage,
        *,
        target: str,
        collection_id: str | None,
        collection_name: str | None,
        use_new_name: bool,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Import d'une page : scan isole puis ingestion (erreurs isolees)."""
        base: dict[str, Any] = {
            "url": ref.url,
            "title": ref.title,
            "domain": ref.domain or _domain_of(ref.url),
            "collected_at": self._clock().isoformat(),
            "source_engine": ref.source_engine,
        }
        try:
            scan = await self._scan_one(ref.url)
        except Exception as exc:  # noqa: BLE001 - page isolee, jamais bloquante
            logger.warning("web research : scan %s echoue : %s", ref.url, exc)
            return {
                **base,
                "status": STATUS_UNREACHABLE,
                "error": str(exc),
                "indexed_count": 0,
            }
        page_ids = [
            p.get("page_id")
            for p in (scan.get("pages") or [])
            if isinstance(p, Mapping) and p.get("page_id")
        ]
        if not scan.get("scan_id") or not page_ids:
            return {
                **base,
                "status": STATUS_UNREACHABLE,
                "error": _first_error(scan.get("errors")) or "aucune page exploitable",
                "indexed_count": 0,
            }
        try:
            result = await self._ingest_one(
                scan["scan_id"],
                page_ids,
                target=target,
                collection_id=collection_id,
                collection_name=collection_name if use_new_name else None,
                project_id=project_id,
                user_id=user_id,
            )
        except Exception as exc:  # noqa: BLE001 - echec isole par page
            logger.error("web research : ingest %s echoue : %s", ref.url, exc)
            return {
                **base,
                "status": STATUS_ERROR,
                "error": str(exc),
                "indexed_count": 0,
            }
        indexed = result.get("indexed") or []
        return {
            **base,
            "status": STATUS_IMPORTED,
            "error": None,
            "indexed_count": result.get("indexed_count") or len(indexed),
            "knowledge_ids": [
                i.get("id") for i in indexed if isinstance(i, Mapping) and i.get("id")
            ],
            "collection": result.get("collection"),
        }

    async def _scan_one(self, url: str) -> dict[str, Any]:
        """Scan d'une page unique (aucun crawl du site : profondeur 0)."""
        kwargs = _supported_kwargs(self._web_ingest.scan, {"max_depth": 0, "max_pages": 1})
        result = await self._web_ingest.scan(url, **kwargs)
        return result if isinstance(result, dict) else {}

    async def _ingest_one(
        self,
        scan_id: str,
        page_ids: Sequence[str],
        *,
        target: str,
        collection_id: str | None,
        collection_name: str | None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Ingestion d'un scan vers Knowledge (pipeline existant)."""
        kwargs: dict[str, Any] = {"target": target, "collection_id": collection_id}
        if collection_name:
            kwargs["new_collection_name"] = collection_name
        if target == "project" and project_id:
            kwargs["project_id"] = project_id
        if user_id is not None:
            # Identité du porteur (JWT) : requise pour le contrôle d'accès
            # du projet en destination "project".
            kwargs["user_id"] = user_id
        kwargs = _supported_kwargs(self._web_ingest.ingest, kwargs)
        result = await self._web_ingest.ingest(scan_id=scan_id, page_ids=list(page_ids), **kwargs)
        return result if isinstance(result, dict) else {}


__all__ = [
    "CollectedPage",
    "MAX_PAGES_PER_COLLECTION",
    "ResearchResult",
    "WebResearchService",
    "validate_max_pages",
]
