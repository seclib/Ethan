"""Ingestion de connaissances depuis le Web — pipeline contrôlé (Core-owned).

Pipeline : URL → scan contrôlé → découverte des pages → récupération du
contenu autorisé → nettoyage/extraction → déduplication → preview →
sélection utilisateur → destination (dossier, Knowledge ou RAG Collection) →
indexation.

Règles d'architecture (AGENTS.md) :
- le scan et le traitement vivent dans le Core : ils doivent fonctionner sans
  aucune interface (la WebUI ne fait que configurer, contrôler et visualiser) ;
- les ressources créées appartiennent aux managers Core existants (RAG
  pipeline, Knowledge, Collections, Folders) — rien n'est dupliqué ;
- **aucune indexation automatique** : ``scan()`` produit uniquement un preview
  transient (jamais persisté) ; l'indexation n'a lieu que via ``ingest()``
  après validation explicite de l'utilisateur.

Limites d'accès respectées (aucun contournement technique) :
- ``robots.txt`` est récupéré et appliqué à chaque URL (pages, liens et
  sitemap) ; un ``Crawl-delay`` est honoré (plafonné pour la robustesse) ;
- garde-fous SSRF : schémas http/https uniquement, hostnames locaux/privés
  rejetés, résolution DNS vérifiée (fail-closed) ;
- politeness : délai séquentiel entre requêtes, timeout par requête, taille
  maximale de page, plafonds durs sur le nombre de pages et la profondeur.
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import logging
import re
import socket
import time
import uuid
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Awaitable, Callable
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree

from core.knowledge.manager import KnowledgeManager
from core.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

# Plafonds durs : les valeurs demandées par l'utilisateur sont bornées.
MAX_PAGES_HARD_CAP = 50
MAX_DEPTH_HARD_CAP = 5
MAX_PAGE_BYTES = 2_000_000  # 2 Mo par page
DEFAULT_REQUEST_TIMEOUT = 10.0
DEFAULT_REQUEST_DELAY = 0.5  # politeness entre deux requêtes du même scan
MAX_CRAWL_DELAY = 10.0  # plafond du Crawl-delay robots.txt honoré
SCAN_TTL_SECONDS = 3600  # un preview non validé expire (jamais persisté)

USER_AGENT = "ETHAN-WebIngest/1.0 (+knowledge-import; respects robots.txt)"

# Extensions non-HTML : jamais explorées ni ingérées par ce pipeline.
_NON_HTML_EXTENSIONS = (
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".json", ".xml", ".zip", ".gz", ".tar", ".mp3", ".mp4",
    ".woff", ".woff2", ".ttf", ".eot", ".doc", ".docx", ".xls", ".xlsx",
)

_SKIPPED_TAGS = frozenset({"script", "style", "noscript", "template"})


# ── (SUITE) ──────────────────────────────────────────────────────────────────

FetchResult = dict[str, Any]
Fetcher = Callable[[str], Awaitable[FetchResult]]
HostnameResolver = Callable[[str], list[str]]


def _default_resolver(hostname: str) -> list[str]:
    """Résolution DNS par défaut (liste d'adresses IP)."""
    infos = socket.getaddrinfo(hostname, None)
    return [info[4][0] for info in infos]


async def _httpx_fetcher(url: str, timeout: float) -> FetchResult:
    """Fetcher par défaut : httpx, redirects suivis, UA identifiable."""
    import httpx

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        response = await client.get(url)
        return {
            "status": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "body": response.content,
            "final_url": str(response.url),
        }


def _validate_public_url(url: str, resolver: HostnameResolver) -> str:
    """Garde-fou SSRF : schéma et destination contrôlés (fail-closed).

    - schémas http/https uniquement ;
    - hostnames littéralement locaux rejetés ;
    - toutes les adresses résolues doivent être publiques (ipaddress).

    Returns:
        L'URL normalisée (fragment retiré, host en minuscules).

    Raises:
        ValueError: si l'URL n'est pas une destination web publique sûre.
    """
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https"):
        raise ValueError(f"Schéma non autorisé : {parts.scheme!r} (http/https uniquement)")
    host = (parts.hostname or "").lower()
    if not host:
        raise ValueError("URL sans hostname")

    # Hostnames littéralement locaux/privés (avant même la résolution DNS).
    if host in ("localhost", "localhost.localdomain") or host.endswith(".local"):
        raise ValueError(f"Hostname local interdit : {host}")
    try:
        literal = ipaddress.ip_address(host)
        if not literal.is_global:
            raise ValueError(f"Adresse IP non publique interdite : {host}")
    except ValueError as exc:
        if "interdit" in str(exc):
            raise
        # Pas un littéral IP : hostname à résoudre ci-dessous.

    try:
        addresses = resolver(host)
    except OSError as exc:
        raise ValueError(f"Résolution DNS impossible pour {host!r}") from exc
    if not addresses:
        raise ValueError(f"Aucune adresse résolue pour {host!r}")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(f"Adresse non publique interdite : {address} ({host})")

    # Normalisation : fragment retiré (jamais significatif pour le contenu).
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", parts.query, ""))


def _normalize_url(url: str) -> str:
    """Normalise une URL pour la déduplication (fragment retiré, slash final)."""
    parts = urlsplit(url.strip())
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def _is_html_url(url: str) -> bool:
    """True si l'URL peut raisonnablement être une page HTML (extension)."""
    path = urlsplit(url).path.lower()
    return not any(path.endswith(ext) for ext in _NON_HTML_EXTENSIONS)


class _PageParser(HTMLParser):
    """Extraction légère : titre, texte de corps et liens — sans dépendance.

    Le texte du corps exclut ``title``/``script``/``style`` : le titre est une
    métadonnée, jamais dupliquée dans le contenu (dédup fiable par hash).
    """

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self._base = base_url
        self.title = ""
        self.text_parts: list[str] = []
        self._in_title = False
        self._skipped_depth = 0
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIPPED_TAGS or tag == "title":
            self._skipped_depth += 1
            if tag == "title":
                self._in_title = True
            return
        attrs_dict = {k: (v or "") for k, v in attrs}
        if tag == "a":
            href = attrs_dict.get("href", "").strip()
            if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                self.links.append(urljoin(self._base, href))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if (tag in _SKIPPED_TAGS or tag == "title") and self._skipped_depth:
            self._skipped_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
            return
        if self._skipped_depth:
            return
        self.text_parts.append(data)


def _parse_page(html: str, base_url: str) -> tuple[str, list[str], str]:
    """Retourne (titre, liens absolus, texte de corps) d'une page HTML."""
    parser = _PageParser(base_url)
    try:
        parser.feed(html)
    except Exception as exc:  # HTML malformé : on garde ce qui a été parsé
        logger.warning("HTML parse error for %s: %s", base_url, exc)
    text = re.sub(r"\s+", " ", " ".join(parser.text_parts)).strip()
    return parser.title.strip(), parser.links, text


# ── (SUITE 2) ────────────────────────────────────────────────────────────────

class WebIngestionManager:
    """Pipeline d'ingestion web contrôlé (scan → preview → validation → index).

    Args:
        rag: RAGPipeline Core (indexation des pages sélectionnées).
        knowledge: KnowledgeManager Core (cible « Knowledge »).
        collections: KnowledgeCollectionManager Core (cible « RAG Collection »).
        folders: FolderManager Core (dossier de destination, optionnel).
        fetcher: fetcher injectable (défaut : httpx) — retourne
            ``{"status", "content_type", "body"}`` ; utilisé par les tests.
        resolver: résolveur DNS injectable (défaut : ``socket.getaddrinfo``).
        request_delay / request_timeout: politeness et timeout (secondes).
    """

    def __init__(
        self,
        rag: RAGPipeline,
        knowledge: KnowledgeManager,
        collections: Any,
        folders: Any | None = None,
        *,
        fetcher: Fetcher | None = None,
        resolver: HostnameResolver | None = None,
        request_delay: float = DEFAULT_REQUEST_DELAY,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> None:
        self._rag = rag
        self._knowledge = knowledge
        self._collections = collections
        self._folders = folders
        self._resolver = resolver or _default_resolver
        self._request_delay = max(0.0, float(request_delay))
        self._request_timeout = float(request_timeout)

        def _fetch(url: str) -> Awaitable[FetchResult]:
            if fetcher is not None:
                return fetcher(url)
            return _httpx_fetcher(url, self._request_timeout)

        self._fetch = _fetch
        # Previews transient (mémoire uniquement) : aucun contenu web n'est
        # persisté ni indexé avant validation explicite via ``ingest()``.
        self._scans: dict[str, dict[str, Any]] = {}

    # ── Garde-fous ───────────────────────────────────────────────────────

    def _validate_url(self, url: str) -> str:
        return _validate_public_url(url, self._resolver)

    async def _fetch_page(self, url: str) -> tuple[FetchResult | None, str | None]:
        """Fetch borné (timeout + taille max). Retourne (résultat, erreur)."""
        try:
            result = await asyncio.wait_for(
                self._fetch(url), timeout=self._request_timeout + 5.0
            )
        except asyncio.TimeoutError:
            return None, "timeout"
        except Exception as exc:
            return None, str(exc)
        if len(result.get("body", b"")) > MAX_PAGE_BYTES:
            return None, f"page trop volumineuse (> {MAX_PAGE_BYTES} octets)"
        return result, None

    async def _load_robots(self, origin: str) -> dict[str, Any]:
        """Charge et parse ``origin/robots.txt`` (absent ⇒ aucune restriction).

        Ne contourne jamais une interdiction : ``can_fetch`` est appliqué à
        chaque URL (pages, liens et sitemaps) avant toute requête.
        """
        parser = RobotFileParser()
        robots_url = f"{origin}/robots.txt"
        result, error = await self._fetch_page(robots_url)
        if error or result is None or result.get("status") != 200:
            return {
                "exists": False,
                "parser": None,
                "crawl_delay": 0.0,
                "sitemap_urls": [],
                "url": robots_url,
            }
        body = result.get("body", b"").decode("utf-8", errors="replace")
        parser.parse(body.splitlines())
        sitemap_urls: list[str] = []
        for line in body.splitlines():
            match = re.match(r"(?i)sitemap:\s*(\S+)", line.strip())
            if match:
                sitemap_urls.append(match.group(1))
        try:
            crawl_delay = float(parser.crawl_delay("*") or 0.0)
        except (TypeError, ValueError):
            crawl_delay = 0.0
        return {
            "exists": True,
            "parser": parser,
            "crawl_delay": min(crawl_delay, MAX_CRAWL_DELAY),
            "sitemap_urls": sitemap_urls,
            "url": robots_url,
        }

    def _allowed_by_robots(self, robots: dict[str, Any], url: str) -> bool:
        parser = robots.get("parser")
        if parser is None:
            return True
        return parser.can_fetch("*", url)

    # ── (SUITE 3) ────────────────────────────────────────────────────────

    @staticmethod
    def _matches_include(url: str, patterns: list[str]) -> bool:
        """True si aucun pattern d'inclusion, ou si l'URL en matche un."""
        if not patterns:
            return True
        from fnmatch import fnmatch

        return any(fnmatch(url, pattern) for pattern in patterns)

    @staticmethod
    def _matches_exclude(url: str, patterns: list[str]) -> bool:
        """True si l'URL matche un pattern d'exclusion."""
        from fnmatch import fnmatch

        return any(fnmatch(url, pattern) for pattern in patterns)

    async def _load_sitemap_urls(
        self, sitemap_url: str, robots: dict[str, Any], limit: int
    ) -> list[str]:
        """Parse un sitemap (urlset ou index à un niveau) → URLs HTML."""
        urls: list[str] = []
        if not self._allowed_by_robots(robots, sitemap_url):
            return urls
        result, error = await self._fetch_page(sitemap_url)
        if error or result is None or result.get("status") != 200:
            return urls
        try:
            root = ElementTree.fromstring(result.get("body", b""))
        except ElementTree.ParseError:
            return urls
        locs: list[str] = []
        for element in root.iter():
            if element.tag.split("}")[-1] == "loc" and element.text:
                locs.append(element.text.strip())
        is_index = root.tag.split("}")[-1] == "sitemapindex"
        if is_index:
            for child_sitemap in locs:
                if len(urls) >= limit:
                    break
                urls.extend(
                    await self._load_sitemap_urls(
                        child_sitemap, robots, limit - len(urls)
                    )
                )
            return urls
        for loc in locs:
            if len(urls) >= limit:
                break
            normalized = _normalize_url(loc)
            if _is_html_url(normalized):
                urls.append(normalized)
        return urls

    # ── (SUITE 4) ────────────────────────────────────────────────────────

    def _public_view(self, scan: dict[str, Any]) -> dict[str, Any]:
        """Vue API du preview : les textes complets restent en mémoire."""
        pages = [
            {k: v for k, v in page.items() if k != "text"} for page in scan["pages"]
        ]
        view = dict(scan)
        view["pages"] = pages
        return view

    def _purge_expired_scans(self) -> None:
        """Les previews non validés expirent (jamais persistés)."""
        now = time.time()
        for scan_id in [
            sid
            for sid, scan in self._scans.items()
            if now - scan["created_at"] > SCAN_TTL_SECONDS
        ]:
            self._scans.pop(scan_id, None)

    async def _collect_sitemap_candidates(
        self, origin: str, robots: dict[str, Any], max_pages: int
    ) -> list[str]:
        """URLs du/des sitemaps (directive robots.txt ou /sitemap.xml)."""
        sitemap_locs = list(robots.get("sitemap_urls") or [])
        sitemap_locs = (sitemap_locs[:3] if sitemap_locs else [f"{origin}/sitemap.xml"])
        found: list[str] = []
        for sitemap_url in sitemap_locs:
            found.extend(await self._load_sitemap_urls(sitemap_url, robots, max_pages * 2))
        return found

    @staticmethod
    def _page_entry(
        url: str,
        depth: int,
        status: str,
        *,
        title: str = "",
        excerpt: str = "",
        text: str = "",
        content_hash: str | None = None,
        duplicate_of: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        return {
            "page_id": _page_id(url),
            "url": url,
            "depth": depth,
            "status": status,
            "title": title,
            "excerpt": excerpt,
            "text_length": len(text),
            "content_hash": content_hash,
            "duplicate_of": duplicate_of,
            "error": error,
            "text": text,  # interne : consommé par ingest(), jamais exposé
        }

    async def _crawl(
        self,
        queue: list[tuple[str, int]],
        *,
        origin_host: str,
        max_pages: int,
        max_depth: int,
        include: list[str],
        exclude: list[str],
        robots: dict[str, Any],
        delay: float,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        """BFS contrôlé : fetch, extraction, dédup — dans les limites fixées."""
        visited: set[str] = set()
        content_hashes: dict[str, str] = {}  # hash contenu → première page_id
        pages: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        first_request = True

        while queue and len(pages) < max_pages:
            current_url, depth = queue.pop(0)
            if current_url in visited or not _is_html_url(current_url):
                continue
            if depth > max_depth:
                continue  # au-delà de la profondeur autorisée : jamais récupéré
            visited.add(current_url)
            if not self._matches_include(current_url, include):
                continue
            if self._matches_exclude(current_url, exclude):
                continue
            if not self._allowed_by_robots(robots, current_url):
                pages.append(self._page_entry(current_url, depth, "disallowed"))
                continue
            if not first_request and delay > 0:
                await asyncio.sleep(delay)
            first_request = False

            result, fetch_error = await self._fetch_page(current_url)
            if fetch_error or result is None or result.get("status") != 200:
                status_code = result.get("status") if result else None
                error = fetch_error or (f"HTTP {status_code}" if status_code else "erreur")
                errors.append({"url": current_url, "error": error})
                pages.append(self._page_entry(current_url, depth, "error", error=error))
                continue

            content_type = str(result.get("content_type", ""))
            if content_type and not any(
                kind in content_type for kind in ("html", "xml", "text/plain")
            ):
                pages.append(
                    self._page_entry(
                        current_url, depth, "skipped",
                        error=f"contenu non textuel ({content_type})",
                    )
                )
                continue

            html = result.get("body", b"").decode("utf-8", errors="replace")
            title, links, text = _parse_page(html, current_url)
            text = text.strip()
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            duplicate_of = content_hashes.get(content_hash)
            if duplicate_of is None and text:
                content_hashes[content_hash] = _page_id(current_url)

            pages.append(
                self._page_entry(
                    current_url, depth, "ok",
                    title=title or current_url,
                    excerpt=text[:300],
                    text=text,
                    content_hash=content_hash,
                    duplicate_of=duplicate_of,
                )
            )

            if depth < max_depth:
                for link in links:
                    normalized = _normalize_url(link)
                    if urlsplit(normalized).netloc != origin_host:
                        continue  # découverte limitée au même site
                    if normalized in visited:
                        continue
                    queue.append((normalized, depth + 1))

        return pages, errors

    # ── (SUITE 5) ────────────────────────────────────────────────────────

    async def scan(
        self,
        url: str,
        *,
        max_pages: int = 10,
        max_depth: int = 2,
        use_sitemap: bool = True,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Scan contrôlé d'une URL → **preview** (aucune indexation).

        1. Garde-fous SSRF sur l'URL racine ;
        2. ``robots.txt`` chargé (``Crawl-delay`` honoré) ;
        3. découverte : sitemap (si disponible et demandé) + BFS sur les liens
           internes (même origin, profondeur ≤ ``max_depth``, ≤ ``max_pages``) ;
        4. pour chaque page autorisée : récupération bornée, extraction
           (titre + texte via ``core.rag.extract``), déduplication
           (URL normalisée + hash du contenu) ;
        5. preview transient retourné — l'indexation n'a lieu qu'après
           validation utilisateur via ``ingest()``.
        """
        self._purge_expired_scans()
        max_pages = max(1, min(int(max_pages), MAX_PAGES_HARD_CAP))
        max_depth = max(0, min(int(max_depth), MAX_DEPTH_HARD_CAP))
        include = [str(p) for p in (include_patterns or [])]
        exclude = [str(p) for p in (exclude_patterns or [])]

        root = self._validate_url(url)
        parts = urlsplit(root)
        origin = f"{parts.scheme}://{parts.netloc}"

        robots = await self._load_robots(origin)
        delay = max(self._request_delay, robots.get("crawl_delay", 0.0))

        # Candidats : URLs du sitemap d'abord (profondeur 1 : découvertes
        # depuis la racine), puis BFS sur les liens internes.
        candidates: list[tuple[str, int]] = [(root, 0)]
        sitemap_used = False
        if use_sitemap:
            sitemap_page_urls = await self._collect_sitemap_candidates(
                origin, robots, max_pages
            )
            if sitemap_page_urls:
                sitemap_used = True
                known = {root}
                for candidate in sitemap_page_urls:
                    if candidate not in known:
                        candidates.append((candidate, 1))
                        known.add(candidate)

        pages, errors = await self._crawl(
            candidates,
            origin_host=parts.netloc.lower(),
            max_pages=max_pages,
            max_depth=max_depth,
            include=include,
            exclude=exclude,
            robots=robots,
            delay=delay,
        )

        scan_id = uuid.uuid4().hex[:12]
        scan_record = {
            "scan_id": scan_id,
            "root_url": root,
            "created_at": time.time(),
            "config": {
                "max_pages": max_pages,
                "max_depth": max_depth,
                "use_sitemap": use_sitemap,
                "include_patterns": include,
                "exclude_patterns": exclude,
            },
            "sitemap_used": sitemap_used,
            "robots": {
                "exists": robots.get("exists", False),
                "crawl_delay": robots.get("crawl_delay", 0.0),
            },
            "pages": pages,
            "errors": errors,
        }
        self._scans[scan_id] = scan_record
        return self._public_view(scan_record)

    def get_scan(self, scan_id: str) -> dict[str, Any] | None:
        """Retourne le preview d'un scan (ou None si inconnu/expiré)."""
        scan = self._scans.get(scan_id)
        return self._public_view(scan) if scan else None

    # ── (SUITE 6) ────────────────────────────────────────────────────────

    async def _resolve_folder(
        self, folder_id: str | None, new_folder_name: str | None
    ) -> dict[str, Any] | None:
        """Résout le dossier de destination (existant ou créé à la volée)."""
        if new_folder_name and new_folder_name.strip():
            if self._folders is None:
                raise ValueError("FolderManager non branché : impossible de créer un dossier")
            return await self._folders.create_folder(new_folder_name.strip())
        if folder_id:
            if self._folders is None:
                raise ValueError("FolderManager non branché")
            folder = await self._folders.get_folder(folder_id)
            if folder is None:
                raise ValueError(f"Folder {folder_id} not found")
            return folder
        return None

    # ── (SUITE 7) ────────────────────────────────────────────────────────

    async def ingest(
        self,
        scan_id: str,
        page_ids: list[str],
        *,
        folder_id: str | None = None,
        new_folder_name: str | None = None,
        target: str = "collection",
        collection_id: str | None = None,
        new_collection_name: str | None = None,
        retrieval_strategy: str | None = None,
        embedding_model: str | None = None,
        user_id: str = "anonymous",
    ) -> dict[str, Any]:
        """Indexe les pages **sélectionnées par l'utilisateur** d'un preview.

        Étape obligatoirement postérieure au scan (aucune indexation
        automatique) : seules les pages listées dans ``page_ids`` sont
        indexées ; les doublons de contenu sont ignorés (déduplication).

        Args:
            scan_id: Preview concerné (transient, voir ``scan()``).
            page_ids: Pages choisies par l'utilisateur.
            folder_id / new_folder_name: Dossier de destination (existant ou
                créé à la volée) ; optionnel — aucun dossier n'est imposé.
            target: ``"collection"`` (documents RAG) ou ``"knowledge"``
                (nœuds de Knowledge).
            collection_id / new_collection_name: RAG Collection cible
                (existante ou créée) — requis si ``target="collection"``.
            retrieval_strategy: Stratégie RAG appliquée à la collection
                (création ou mise à jour de la collection cible).
            embedding_model: Modèle d'embedding appliqué au moteur RAG
                (config globale du moteur, persistée).
        """
        scan = self._scans.get(scan_id)
        if scan is None:
            raise ValueError(f"Scan {scan_id} introuvable ou expiré — relancez le scan")
        pages_by_id = {page["page_id"]: page for page in scan["pages"]}
        unknown = [pid for pid in page_ids if pid not in pages_by_id]
        if unknown:
            raise ValueError(f"Pages inconnues dans le scan {scan_id}: {unknown}")

        selected: list[dict[str, Any]] = []
        skipped_duplicates: list[dict[str, str]] = []
        for pid in page_ids:
            page = pages_by_id[pid]
            if page["status"] != "ok" or not (page.get("text") or "").strip():
                continue
            if page.get("duplicate_of"):
                skipped_duplicates.append(
                    {"page_id": pid, "url": page["url"], "duplicate_of": page["duplicate_of"]}
                )
                continue
            selected.append(page)

        folder = await self._resolve_folder(folder_id, new_folder_name)
        target_normalized = (target or "").strip().lower()
        if target_normalized not in ("collection", "knowledge"):
            raise ValueError(f"Cible inconnue : {target!r} (collection|knowledge)")

        created_documents: list[dict[str, Any]] = []
        created_nodes: list[dict[str, Any]] = []
        collection: dict[str, Any] | None = None

        # ── (SUITE 8) ────────────────────────────────────────────────────
        if target_normalized == "collection":
            if collection_id:
                collection = await self._collections.get_collection(collection_id)
                if collection is None:
                    raise ValueError(f"Collection {collection_id} not found")
                if retrieval_strategy:
                    collection = await self._collections.update_collection(
                        collection_id, {"retrieval_strategy": retrieval_strategy}
                    )
            elif new_collection_name and new_collection_name.strip():
                collection = await self._collections.create_collection(
                    new_collection_name.strip(),
                    user_id=user_id,
                    retrieval_strategy=retrieval_strategy,
                )
            else:
                raise ValueError(
                    "Cible collection : fournir collection_id ou new_collection_name"
                )

            if embedding_model:
                await self._rag.configure(embedding_model=embedding_model)
                await self._rag.persist_config()

            for page in selected:
                document = await self._rag.ingest(
                    page["text"],
                    title=page.get("title") or page["url"],
                    source=page["url"],
                    metadata={
                        "web_url": page["url"],
                        "content_hash": page.get("content_hash"),
                        "scan_id": scan_id,
                    },
                )
                await self._collections.add_document(collection["id"], document.id)
                created_documents.append(
                    {"document_id": document.id, "url": page["url"], "title": page.get("title")}
                )
            if folder is not None:
                await self._folders.attach_resource(
                    folder["id"], "collection", collection["id"]
                )
        else:
            for page in selected:
                node = await self._knowledge.create(
                    page.get("title") or page["url"],
                    node_type="document",
                    content=page["text"],
                    source=page["url"],
                    metadata={
                        "web_url": page["url"],
                        "content_hash": page.get("content_hash"),
                        "scan_id": scan_id,
                    },
                )
                if folder is not None:
                    await self._folders.attach_resource(folder["id"], "knowledge", node.id)
                created_nodes.append(
                    {"node_id": node.id, "url": page["url"], "title": page.get("title")}
                )

        return {
            "scan_id": scan_id,
            "target": target_normalized,
            "folder": (
                {"id": folder["id"], "name": folder.get("name")} if folder else None
            ),
            "collection": (
                {"id": collection["id"], "name": collection.get("name")}
                if collection
                else None
            ),
            "indexed": created_documents or created_nodes,
            "indexed_count": len(created_documents) or len(created_nodes),
            "skipped_duplicates": skipped_duplicates,
        }


def _page_id(url: str) -> str:
    """Identifiant stable d'une page (hash de l'URL normalisée)."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


__all__ = ["WebIngestionManager"]
