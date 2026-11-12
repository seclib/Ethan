"""Brouillon de Skill depuis des sources Web (Web Inspiration → Skills).

Capacité Core-only. À partir d'une sélection de sources web (≤ 50), le Core :
1. récupère et analyse chaque source (scan contrôlé via
   ``WebIngestionManager`` — robots.txt, SSRF, bornes ; erreurs isolées
   par source) ;
2. produit un **brouillon** de Skill (prompt structuré) : le LLM
   (``ProviderManager``, optionnel) synthétise et structure le contenu —
   il ne crée jamais la Skill et ne peut pas contourner la validation
   humaine ; en son absence, un brouillon déterministe est assemblé à
   partir des extraits ;
3. retourne le brouillon avec les sources utilisées (URLs conservées).

Règles d'architecture (AGENTS.md) :
- ce service n'écrit JAMAIS dans le ``SkillStore`` : la création effective
  passe par le système de Skills existant (``POST /v1/skills``), uniquement
  sur validation humaine dans l'interface ;
- ``is_active`` est toujours ``False`` dans le contrat du brouillon :
  aucune Skill n'est activée automatiquement après génération ;
- les URLs des sources sont conservées (``meta.web_sources`` côté skill).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Plafond absolu de sources par brouillon (aligné sur le workflow Knowledge).
SKILL_DRAFT_MAX_SOURCES = 50

# Longueur maximale d'un extrait conservé par source.
EXCERPT_MAX_CHARS = 1200

# Statuts de récupération par source (best-effort, erreurs isolées).
STATUS_OK = "ok"
STATUS_UNREACHABLE = "unreachable"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DraftSource:
    """Source Web utilisée pour le brouillon (URL toujours conservée)."""

    url: str
    title: str = ""
    domain: str = ""
    snippet: str = ""
    status: str = STATUS_UNREACHABLE
    excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "domain": self.domain,
            "snippet": self.snippet,
            "status": self.status,
            "excerpt": self.excerpt,
        }


@dataclass
class SkillDraft:
    """Brouillon de Skill — JAMAIS persisté tel quel, jamais activé."""

    topic: str
    name: str
    description: str
    content: str
    sources: list[DraftSource] = field(default_factory=list)
    kind: str = "prompt"
    tags: list[str] = field(default_factory=list)
    llm_used: bool = False
    fallback_used: bool = False
    is_active: bool = False  # invariant : brouillon → jamais actif
    max_sources: int = SKILL_DRAFT_MAX_SOURCES
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "kind": self.kind,
            "tags": list(self.tags),
            "sources": [s.to_dict() for s in self.sources],
            "llm_used": self.llm_used,
            "fallback_used": self.fallback_used,
            "is_active": self.is_active,
            "max_sources": self.max_sources,
            "generated_at": self.generated_at,
        }


class WebSkillDraftService:
    """Génération de brouillons de Skill depuis des sources Web (Core-only).

    Dépendances : ``WebIngestionManager`` (récupération contrôlée) et un
    ``ProviderManager`` optionnel (synthèse LLM). Aucun accès au
    ``SkillStore`` : la persistance relève de la validation humaine.
    """

    def __init__(
        self,
        *,
        web_ingest: Any,
        provider_manager: Any | None = None,
        max_sources: int = SKILL_DRAFT_MAX_SOURCES,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._web_ingest = web_ingest
        self._providers = provider_manager
        self._max_sources = max(1, int(max_sources))
        self._clock = clock or _now_iso

    def set_provider_manager(self, provider_manager: Any | None) -> None:
        """Injecte le ProviderManager (synthèse LLM) — appelé au startup."""
        self._providers = provider_manager

    @property
    def max_sources(self) -> int:
        """Plafond absolu de sources par brouillon."""
        return self._max_sources

    # ── API publique ─────────────────────────────────────────────────────────

    async def draft(
        self,
        topic: str,
        sources: list[dict[str, Any] | str],
        *,
        use_llm: bool = True,
    ) -> SkillDraft:
        """Récupère/analyse les sources puis produit un brouillon de Skill.

        Args:
            topic: Sujet de la recherche (intitulé du brouillon).
            sources: Sélection utilisateur — dict ``{url, title?, snippet?,
                domain?}`` ou URL brute. Les doublons d'URL sont dédupliqués.
            use_llm: Tenter la synthèse LLM (repli déterministe sinon).

        Returns:
            ``SkillDraft`` (jamais persisté, ``is_active=False``).

        Raises:
            ValueError: topic vide, sélection vide ou > ``max_sources``.
        """
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic requis")
        refs = self._normalize_sources(sources)
        if not refs:
            raise ValueError("Au moins une source est requise")
        if len(refs) > self._max_sources:
            raise ValueError(
                f"Sélection de {len(refs)} sources refusée : plafond absolu = "
                f"{self._max_sources} sources par brouillon"
            )

        analyzed = [await self._fetch_source(ref) for ref in refs]

        content = name = description = None
        llm_used = False
        if use_llm and self._providers is not None:
            proposed = await self._llm_draft(topic, analyzed)
            if proposed:
                name = proposed.get("name")
                description = proposed.get("description")
                content = proposed.get("content")
                llm_used = True
        fallback_used = not llm_used
        if fallback_used:
            name, description, content = self._fallback_draft(topic, analyzed)

        draft = SkillDraft(
            topic=topic,
            name=(name or topic)[:120].strip() or topic,
            description=(description or "").strip()
            or f"Brouillon généré depuis {len(analyzed)} source(s) web — « {topic} ».",
            content=(content or "").strip(),
            sources=analyzed,
            tags=["web-inspiration"],
            llm_used=llm_used,
            fallback_used=fallback_used,
            is_active=False,
            max_sources=self._max_sources,
            generated_at=self._clock(),
        )
        logger.info(
            "Brouillon de skill généré : topic=%r sources=%d llm=%s",
            topic,
            len(analyzed),
            llm_used,
        )
        return draft

    # ── Normalisation / récupération ────────────────────────────────────────

    def _normalize_sources(self, sources: list[dict[str, Any] | str]) -> list[DraftSource]:
        """Normalise et déduplique la sélection (URL = identité)."""
        refs: list[DraftSource] = []
        seen: set[str] = set()
        for raw in sources or []:
            if isinstance(raw, str):
                item: dict[str, Any] = {"url": raw}
            elif isinstance(raw, dict):
                item = raw
            else:
                continue
            url = str(item.get("url") or "").strip()
            if not url.lower().startswith(("http://", "https://")):
                continue
            key = url.lower().rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            refs.append(
                DraftSource(
                    url=url,
                    title=str(item.get("title") or "").strip(),
                    domain=str(item.get("domain") or "").strip(),
                    snippet=str(item.get("snippet") or "").strip(),
                )
            )
        return refs

    async def _fetch_source(self, ref: DraftSource) -> DraftSource:
        """Scan contrôlé d'une source (best-effort, erreur isolée)."""
        try:
            kwargs: dict[str, Any] = {"max_depth": 0, "max_pages": 1}
            import inspect

            params = inspect.signature(self._web_ingest.scan).parameters
            kwargs = {k: v for k, v in kwargs.items() if k in params}
            scan = await self._web_ingest.scan(ref.url, **kwargs)
            pages = scan.get("pages") if isinstance(scan, dict) else None
            page = pages[0] if pages else None
            if not page or page.get("status") != "ok":
                ref.status = STATUS_UNREACHABLE
                return ref
            ref.status = STATUS_OK
            ref.excerpt = str(page.get("text") or "")[:EXCERPT_MAX_CHARS]
            if not ref.title:
                ref.title = str(page.get("title") or "")[:200]
        except Exception as exc:  # noqa: BLE001 — source isolée, jamais bloquante
            logger.warning("web skill draft : scan %s échoué : %s", ref.url, exc)
            ref.status = STATUS_UNREACHABLE
        return ref

    # ── Synthèse ─────────────────────────────────────────────────────────────

    async def _llm_draft(self, topic: str, sources: list[DraftSource]) -> dict[str, str] | None:
        """Synthèse LLM (JSON strict) — best-effort, ``None`` si indisponible.

        Le LLM ne produit qu'un TEXTE de brouillon : il n'a aucun accès au
        SkillStore ni à aucun mécanisme d'activation.
        """
        try:
            from core.llm.types import ChatMessage

            usable = [s for s in sources if s.status == STATUS_OK and s.excerpt]
            if not usable:
                return None
            corpus = "\n\n".join(
                f"[{i + 1}] {s.title or s.url} ({s.domain or 'source web'})\n"
                f"URL : {s.url}\n{s.excerpt[:800]}"
                for i, s in enumerate(usable)
            )
            default = await self._providers.get_default_provider()
            pid = default.get("provider_id") if isinstance(default, dict) else None
            provider = self._providers._registry.get_provider(pid or "ollama")
            model = await self._providers.get_active_model(pid or "ollama")
            response = await provider.chat(
                [
                    ChatMessage(
                        role="system",
                        content=(
                            "Tu prépares un BROUILLON de skill pour un humain qui "
                            "le validera. Réponds UNIQUEMENT avec un JSON valide "
                            '{"name": str, "description": str, "content": str}. '
                            "'content' est le prompt de la skill en markdown "
                            "structuré (rôle, étapes, garde-fous), citant les "
                            "sources [n]. Ne propose aucune activation."
                        ),
                    ),
                    ChatMessage(
                        role="user",
                        content=f"Sujet : {topic}\n\nSources :\n{corpus}",
                    ),
                ],
                model=model,
                temperature=0.3,
            )
            raw = (
                response
                if isinstance(response, str)
                else (
                    getattr(response, "content", None)
                    or getattr(getattr(response, "message", None), "content", "")
                    or ""
                )
            )
            return self._parse_llm_json(str(raw))
        except Exception as exc:  # noqa: BLE001 — synthèse best-effort
            logger.warning("web skill draft : synthèse LLM échouée : %s", exc)
            return None

    @staticmethod
    def _parse_llm_json(raw: str) -> dict[str, str] | None:
        """Extrait le JSON du brouillon (tolérant aux blocs ```json)."""
        text = raw.strip()
        if "```" in text:
            for part in text.split("```"):
                candidate = part.strip().removeprefix("json").strip()
                if candidate.startswith("{"):
                    text = candidate
                    break
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(data, dict):
            return None
        out = {k: str(data.get(k) or "").strip() for k in ("name", "description", "content")}
        if not out["content"]:
            return None
        return out

    def _fallback_draft(self, topic: str, sources: list[DraftSource]) -> tuple[str, str, str]:
        """Brouillon déterministe (aucun LLM requis) — toujours disponible."""
        ok = [s for s in sources if s.status == STATUS_OK]
        lines = [
            f"# {topic}",
            "",
            "## Rôle",
            f"Tu aides sur le sujet « {topic} » en t'appuyant sur les sources "
            "web analysées ci-dessous.",
            "",
            "## Étapes",
            "1. Identifier la question de l'utilisateur sur ce sujet.",
            "2. Mobiliser les sources listées (citer [n]).",
            "3. Synthétiser une réponse structurée, signaler les incertitudes.",
            "",
            "## Sources analysées",
        ]
        for i, s in enumerate(sources, 1):
            lines.append(f"[{i}] {s.title or s.url} — {s.url} ({s.status})")
        if ok:
            lines.append("")
            lines.append("## Extraits de référence")
            for i, s in enumerate(ok, 1):
                lines.append(f"[{i}] {s.excerpt[:400]}")
        description = (
            f"Brouillon déterministe depuis {len(ok)}/{len(sources)} source(s) "
            f"web utilisable(s) — « {topic} »."
        )
        return f"Skill — {topic[:60]}", description, "\n".join(lines)


__all__ = [
    "EXCERPT_MAX_CHARS",
    "SKILL_DRAFT_MAX_SOURCES",
    "DraftSource",
    "SkillDraft",
    "WebSkillDraftService",
]
