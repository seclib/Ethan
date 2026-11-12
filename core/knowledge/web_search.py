"""Recherche web multi-moteurs — pipeline contrôlé (Core-owned).

Pipeline : query → moteur(s) configuré(s) → résultats normalisés
(title, url, snippet, rang, moteur source) → réponse structurée.

Règles d'architecture (AGENTS.md) :
- toute la logique vit dans le Core : elle doit fonctionner sans aucune
  interface (l'API et la WebUI ne font que configurer, contrôler et
  visualiser) ;
- aucun moteur ni clé API n'est imposé : DuckDuckGo fonctionne sans clé
  (via ``ddgs``), Bing et Yandex sont récupérés de façon « best-effort » en
  lecture seule ;
- les résultats sont des métadonnées publiques : les URLs renvoyées doivent
  être validées par les composants d'ingestion en aval (SSRF, robots.txt)
  avant toute récupération de contenu ;
- politesse : timeout borné, nombre de résultats borné, aucun retry
  automatique agressif.

Limites d'accès respectées (aucun contournement technique) :
- aucun proxy n'est requis par défaut ; ``ProxyConfig`` permet d'utiliser un
  proxy/VPN explicite (url, username, password) sans stockage de secret ;
- les erreurs réseau sont journalisées au niveau warning et remontées dans
  ``metadata`` de la réponse (best-effort).
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from core.network import DEFAULT_NETWORK_PROFILES, NetworkProfileManager

logger = logging.getLogger(__name__)

# Plafonds durs : les valeurs demandées par l'utilisateur sont bornées.
# MAX_RESULTS_HARD_CAP est une valeur ABSOLUE : une demande supérieure est
# refusée (ValueError), jamais silencieusement tronquée.
MAX_RESULTS_HARD_CAP = 50
MIN_RESULTS = 1
DEFAULT_MAX_RESULTS = 10
DEFAULT_REQUEST_TIMEOUT = 10.0

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 ETHAN-WebSearch/1.0"
)


# ── Helpers URL ────────────────────────────────────────────────────────────


def _extract_domain(url: str) -> str:
    """Domaine normalisé d'une URL (minuscule, sans préfixe ``www.``).

    Best-effort : une URL non parsable retourne une chaîne vide (le Core ne
    lève jamais pour une donnée fournie par un tiers).
    """
    try:
        host = (urlsplit(url).hostname or "").lower().strip(".")
    except ValueError:  # IPv6 malformée, etc.
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host[:253]


def _dedup_key(url: str) -> str:
    """Cle de deduction stable d'une URL.

    Deux URLs pointant vers la meme ressource sont considerees identiques si
    elles ne diferent que par la casse de l'hote, le prefixe ``www.``, une
    barre oblique finale, le fragment (``#ancre``) ou le scheme (http/https
    canonise vers https).

    Le nettoyage ne s'applique qu'a la cle : l'URL retournee dans le resultat
    reste l'original du moteur.
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parts.path.rstrip("/")
    scheme = parts.scheme.lower()
    if scheme in ("http", "https"):
        scheme = "https"
    return urlunsplit((scheme, netloc, path, parts.query, ""))


# ─ Validation du nombre de résultats ───────────────────────────────────────


# Clés réservées des items bruts (non exposées comme métadonnées).
_RESULT_RESERVED_KEYS = frozenset({"title", "url", "href", "snippet", "body", "rank"})


def _coerce_max_results(value: Any) -> int:
    """Convertit une valeur brute en entier, ou lève ``ValueError``.

    Accepte ``int`` et chaîne numérique (formulaires/JSON tolérants) ; refuse
    explicitement ``bool``, ``float``, ``None`` et toute chaîne non numérique.
    """
    if isinstance(value, bool):
        raise ValueError("max_results invalide : valeur booléenne non acceptée")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        digits = text[1:] if text.startswith(("-", "+")) else text
        if digits and digits.isdigit():
            return int(text)
        raise ValueError(f"max_results invalide : {value!r} n'est pas un entier")
    raise ValueError(f"max_results invalide : type {type(value).__name__} non accepté")


def validate_max_results(value: Any) -> int:
    """Valide le nombre de résultats demandé (refus strict, jamais de clamp).

    Règles :
    - entier (ou chaîne numérique) requis ;
    - ``value >= MIN_RESULTS`` ;
    - ``value <= MAX_RESULTS_HARD_CAP`` (plafond absolu de 50 pages).

    Raises:
        ValueError: valeur invalide, négative/nulle ou supérieure au plafond.
    """
    number = _coerce_max_results(value)
    if number < MIN_RESULTS:
        raise ValueError(f"max_results={number} refusé : minimum = {MIN_RESULTS}")
    if number > MAX_RESULTS_HARD_CAP:
        raise ValueError(
            f"max_results={number} refusé : plafond absolu = "
            f"{MAX_RESULTS_HARD_CAP} pages par recherche"
        )
    return number


# ── Providers de recherche (abstraction extensible) ───────────────────────


class SearchProvider(ABC):
    """Backend de recherche web (un moteur = un provider).

    Contrat :
    - ``id``    : identifiant stable, minuscule (ex: ``duckduckgo``) ;
    - ``label`` : libellé d'affichage (les interfaces affichent, elles ne
      définissent pas la logique) ;
    - ``fetch`` : récupère des items BRUTS (``title``/``url``/``snippet``) ;
      la normalisation, la déduplication et les bornes restent la
      responsabilité du ``WebSearchManager`` (source de vérité unique).

    Aucun provider ne télécharge le contenu des pages : seules les métadonnées
    de résultats (titre, URL, extrait) sont collectées à ce stade.
    """

    id: str = ""
    label: str = ""

    @abstractmethod
    async def fetch(
        self,
        manager: "WebSearchManager",
        query: str,
        max_results: int,
        proxy: "ProxyConfig | None" = None,
    ) -> list[dict[str, Any]]:
        """Retourne des items bruts (best-effort ; peut lever, géré en amont)."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Disponibilité du backend (dépendances présentes, etc.)."""
        return True


class _DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo via ``ddgs`` (aucune clé API requise)."""

    id = "duckduckgo"
    label = "DuckDuckGo"

    async def fetch(self, manager, query, max_results, proxy=None):
        return await manager._search_duckduckgo(query, max_results, proxy)

    def is_available(self) -> bool:
        try:
            import ddgs  # noqa: F401
        except ImportError:
            return False
        return True


class _BingProvider(SearchProvider):
    """Bing : page de résultats HTML, best-effort (sans clé API)."""

    id = "bing"
    label = "Bing"

    async def fetch(self, manager, query, max_results, proxy=None):
        return await manager._search_bing(query, max_results, proxy)


class _YandexProvider(SearchProvider):
    """Yandex : page de résultats HTML, best-effort (sans clé API)."""

    id = "yandex"
    label = "Yandex"

    async def fetch(self, manager, query, max_results, proxy=None):
        return await manager._search_yandex(query, max_results, proxy)


class SearchProviderRegistry:
    """Registre extensible des providers de recherche.

    Permet d'ajouter un moteur ultérieurement sans modifier
    ``WebSearchManager`` : ``registry.register(MonProvider())``.
    """

    def __init__(self) -> None:
        self._providers: dict[str, SearchProvider] = {}

    def register(self, provider: SearchProvider, *, override: bool = False) -> None:
        """Enregistre un provider (id unique, minuscule).

        Raises:
            ValueError: id vide ou déjà enregistré (sans ``override``).
        """
        provider_id = (getattr(provider, "id", "") or "").strip().lower()
        if not provider_id:
            raise ValueError("Un provider de recherche doit définir un 'id' non vide")
        if provider_id in self._providers and not override:
            raise ValueError(f"Provider déjà enregistré : {provider_id!r}")
        self._providers[provider_id] = provider

    def unregister(self, provider_id: str) -> bool:
        """Retire un provider ; retourne True s'il existait."""
        key = (provider_id or "").strip().lower()
        return self._providers.pop(key, None) is not None

    def get(self, provider_id: str) -> SearchProvider | None:
        """Retourne le provider (ou ``None`` s'il est inconnu)."""
        return self._providers.get((provider_id or "").strip().lower())

    def ids(self) -> list[str]:
        """Identifiants des providers enregistrés (ordre d'enregistrement)."""
        return list(self._providers)

    def catalog(self) -> list[dict[str, str]]:
        """Catalogue affichable : ``[{"id": ..., "label": ...}]``."""
        return [
            {"id": provider_id, "label": provider.label}
            for provider_id, provider in self._providers.items()
        ]

    def __contains__(self, provider_id: object) -> bool:
        if not isinstance(provider_id, str):
            return False
        return provider_id.strip().lower() in self._providers

    def __len__(self) -> int:
        return len(self._providers)


# Registre par défaut : DuckDuckGo, Bing, Yandex (aucune clé API requise).
DEFAULT_PROVIDER_REGISTRY = SearchProviderRegistry()
for _builtin_provider in (_DuckDuckGoProvider(), _BingProvider(), _YandexProvider()):
    DEFAULT_PROVIDER_REGISTRY.register(_builtin_provider)

# Compat : miroir id → libellé du registre par défaut (catalogue affichable).
_ENGINES: dict[str, str] = {
    entry["id"]: entry["label"] for entry in DEFAULT_PROVIDER_REGISTRY.catalog()
}


def register_search_provider(
    provider: SearchProvider,
    *,
    registry: SearchProviderRegistry | None = None,
    override: bool = False,
) -> None:
    """Point d'extension Core : ajoute un moteur de recherche.

    Args:
        provider: Instance de ``SearchProvider``.
        registry: Registre cible (défaut : registre global du Core).
        override: Remplacer un provider existant du même id.
    """
    target = registry if registry is not None else DEFAULT_PROVIDER_REGISTRY
    target.register(provider, override=override)
    if target is DEFAULT_PROVIDER_REGISTRY:
        _ENGINES.clear()
        _ENGINES.update({entry["id"]: entry["label"] for entry in target.catalog()})


@dataclass
class ProxyConfig:
    """Configuration de proxy/VPN optionnelle (secrets en couche dédiée).

    ``timeout`` (optionnel, secondes) surcharge le timeout du manager pour
    la requête concernée : c'est ainsi que le timeout d'un profil réseau
    (``core/network``) transite jusqu'aux backends HTTP sans modifier le
    protocole des providers.
    """

    url: str | None = None
    username: str | None = None
    password: str | None = None
    timeout: float | None = None

    @property
    def auth(self) -> tuple[str, str] | None:
        """Auth httpx (username, password) si les deux sont fournis."""
        if self.username and self.password is not None:
            return (self.username, self.password)
        return None

    def apply(self, client: Any) -> None:
        """Applique la configuration à un client httpx.AsyncClient."""
        if not self.url:
            return
        setattr(client, "proxies", {"http://": self.url, "https://": self.url})
        auth = self.auth
        if auth:
            setattr(client, "auth", auth)


@dataclass
class SearchResult:
    """Un résultat de recherche normalisé (indépendant du moteur source)."""

    title: str
    url: str
    snippet: str = ""
    source_engine: str = ""
    rank: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    domain: str = ""

    # Bornes par champ : le Core ne produit jamais de réponse démesurée.
    _TITLE_MAX = 300
    _URL_MAX = 2000
    _SNIPPET_MAX = 600
    _DOMAIN_MAX = 253

    def __post_init__(self) -> None:
        self.title = self.title[: self._TITLE_MAX]
        self.url = self.url[: self._URL_MAX]
        self.snippet = self.snippet[: self._SNIPPET_MAX]
        self.rank = max(0, int(self.rank))
        if not isinstance(self.metadata, dict):
            self.metadata = {}
        if not self.domain:
            self.domain = _extract_domain(self.url)
        self.domain = self.domain[: self._DOMAIN_MAX]

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le résultat pour l'API / la WebUI.

        Expose le contrat stable : titre, url, domaine, extrait, moteur, rang
        et métadonnées disponibles.
        """
        return {
            "title": self.title,
            "url": self.url,
            "domain": self.domain,
            "snippet": self.snippet,
            "source_engine": self.source_engine,
            "rank": self.rank,
            "metadata": self.metadata,
        }

    @property
    def hostname(self) -> str:
        parts = urlsplit(self.url)
        return parts.hostname or ""


@dataclass
class SearchResponse:
    """Réponse structurée d'une recherche (un moteur)."""

    query: str
    engine: str
    results: list[SearchResult] = field(default_factory=list)
    total_found: int = 0
    search_time_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Sérialise la réponse pour l'API / la WebUI."""
        return {
            "query": self.query,
            "engine": self.engine,
            "total_found": self.total_found,
            "search_time_ms": self.search_time_ms,
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata,
        }


def _proxy_url_with_auth(proxy: "ProxyConfig | None") -> str | None:
    """URL de proxy prête à l'emploi (credentials injectés, scheme préservé).

    Injecte ``username:password`` dans le netloc SANS altérer le scheme : un
    proxy ``socks5://`` (Tor/VPN) doit rester ``socks5://``, un ``http://``
    reste ``http://``. Les credentials sont percent-encodés (jamais journalisés).
    """
    if proxy is None or not proxy.url:
        return None
    if not (proxy.username and proxy.password is not None):
        return proxy.url
    parts = urlsplit(proxy.url)
    userinfo = f"{quote(proxy.username, safe='')}:{quote(proxy.password, safe='')}"
    netloc = f"{userinfo}@{parts.netloc}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, ""))


class _SearchResultParser(HTMLParser):
    """Extraction d'items de résultats depuis le HTML d'un moteur.

    Heuristique générique et robuste :
    - un résultat commence par un ``<a href="...">texte</a>`` porteur de
      texte (lien http(s) avec un contenu visible) ;
    - le snippet d'un résultat = tout le texte non-lien rencontré après lui
      et avant le lien suivant (contenu script/style/noscript/iframe exclu) ;
    - la structure exacte des moteurs (li.b_algo, li.serp-item, ...) n'est
      pas requise : seule la balise ``<li>`` sert de frontière forte de
      clôture de snippet.
    """

    _SKIP_TAGS = frozenset({"script", "style", "noscript", "iframe"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self._skip_depth = 0
        self._in_anchor = False
        self._href: str | None = None
        self._anchor_text: list[str] = []
        self._pending_snippet: list[str] = []

    # ── helpers ────────────────────────────────────────────────────────

    def _flush_snippet(self) -> None:
        """Finalise le snippet du dernier résultat accumulé (s'il est vide)."""
        if not self.results:
            self._pending_snippet = []
            return
        snippet = " ".join(" ".join(self._pending_snippet).split())
        if snippet and not self.results[-1]["snippet"]:
            self.results[-1]["snippet"] = snippet[:600]
        self._pending_snippet = []

    # ── handlers HTMLParser ───────────────────────────────────────────

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href")
            if href and href.startswith(("http://", "https://")):
                # Nouveau candidat résultat : on clôt le snippet précédent.
                self._flush_snippet()
                self._in_anchor = True
                self._href = href
                self._anchor_text = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_anchor:
            self._anchor_text.append(data)
        else:
            stripped = " ".join(data.split())
            if stripped:
                self._pending_snippet.append(stripped)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag == "a" and self._in_anchor:
            text = " ".join(" ".join(self._anchor_text).split())
            if text:
                self.results.append({"title": text[:300], "url": self._href or "", "snippet": ""})
                self._pending_snippet = []
            self._in_anchor = False
            self._href = None
            self._anchor_text = []
        elif tag == "li":
            # Frontière forte : clôt le snippet du dernier résultat.
            self._flush_snippet()


def _extract_metadata(item: dict[str, Any]) -> dict[str, Any]:
    """Métadonnées additionnelles exposées par un provider (best-effort).

    Seules les valeurs scalaires sérialisables sont conservées : jamais de
    structure opaque dans la réponse du Core.
    """
    extra: dict[str, Any] = {}
    for key, value in item.items():
        if key in _RESULT_RESERVED_KEYS or value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            extra[str(key)] = value
    return extra


def _normalize(
    query: str,
    engine: str,
    raw_items: list[dict[str, Any]],
    limit: int = DEFAULT_MAX_RESULTS,
) -> list[SearchResult]:
    """Normalise des items bruts en résultats dédupliqués et ordonnés.

    Responsabilités (source de vérité unique du Core) :
    - ignorer les résultats invalides (entrée non-dict, URL non http(s)) ;
    - dédupliquer les URLs via ``_dedup_key`` (hôte, ``www.``, ``/`` final,
      fragment ignorés) ;
    - renseigner ``domain`` et les métadonnées disponibles ;
    - borner strictement le nombre de résultats à ``limit`` (valeur déjà
      validée en amont, plafond absolu ``MAX_RESULTS_HARD_CAP``).
    """
    cap = min(max(MIN_RESULTS, int(limit)), MAX_RESULTS_HARD_CAP)
    seen: set[str] = set()
    results: list[SearchResult] = []
    for item in raw_items or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("href") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        key = _dedup_key(url)
        if key in seen:
            continue
        seen.add(key)
        title = str(item.get("title") or "").strip()
        snippet = str(item.get("snippet") or item.get("body") or "").strip()
        if not title:
            title = url[:120]
        results.append(
            SearchResult(
                title=title,
                url=url,
                snippet=snippet,
                source_engine=engine,
                rank=len(results) + 1,
                metadata=_extract_metadata(item),
            )
        )
        if len(results) >= cap:
            break
    return results


class WebSearchManager:
    """Moteur de recherche web multi-backends, propriete exclusive du Core.

    Aucune interface ne doit en dependre pour exister : ce module fonctionne
    en autonomie complete (aucune dependance a l'API, la WebUI ou le CLI).

    Extensibilite : un moteur supplementaire s'ajoute via
    ``register_search_provider()`` (ou ``WebSearchManager(registry=...)``) en
    implementant ``SearchProvider`` -- aucune modification du manager n'est
    requise. La logique de normalisation et de borne reste centree ici.
    """

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_results: int = DEFAULT_MAX_RESULTS,
        registry: SearchProviderRegistry | None = None,
        network_profiles: NetworkProfileManager | None = None,
    ) -> None:
        self._timeout = timeout
        # Refus strict au-dela du plafond absolu (jamais de troncature muette).
        self._max_results = validate_max_results(max_results)
        self._registry = registry if registry is not None else DEFAULT_PROVIDER_REGISTRY
        # Profils réseau (core/network) : les interfaces ne transmettent que
        # l'identifiant ; la résolution (credentials inclus) reste Core-only.
        self._network_profiles = (
            network_profiles if network_profiles is not None else DEFAULT_NETWORK_PROFILES
        )

    @property
    def network_profiles(self) -> NetworkProfileManager:
        """Registre des profils réseau utilisé par ce manager."""
        return self._network_profiles

    def _coerce_proxy(self, proxy: ProxyConfig | str | None) -> ProxyConfig | None:
        """Résout un identifiant de profil réseau (str) en ``ProxyConfig``.

        Le Core (et donc toute interface) ne transmet qu'un identifiant :
        les credentials sont lus depuis l'environnement au moment de la
        résolution et ne transitent JAMAIS dans les payloads d'API.

        Raises:
            ValueError: profil inconnu, désactivé, VPN non intégré (point
                d'intégration documenté) ou credential d'environnement
                absent/vide — via ``NetworkProfileError`` (ValueError).
        """
        if proxy is None or isinstance(proxy, ProxyConfig):
            return proxy
        if isinstance(proxy, str):
            resolved = self._network_profiles.resolve(proxy.strip())
            return ProxyConfig(
                url=resolved.proxy_url,
                username=resolved.username,
                password=resolved.password,
                timeout=resolved.timeout_seconds,
            )
        raise ValueError("proxy : ProxyConfig ou identifiant de profil réseau (str) attendu")

    # -- Catalogue / registre de providers --------------------------------------

    @property
    def registry(self) -> SearchProviderRegistry:
        """Registre des providers de recherche utilise par ce manager."""
        return self._registry

    def list_engines(self) -> list[dict[str, str]]:
        """Retourne le catalogue des moteurs disponibles (id + libelle)."""
        return self._registry.catalog()

    def available_engines(self) -> list[str]:
        """Moteurs dont le backend est effectivement disponible (best-effort)."""
        return [pid for pid in self._registry.ids() if self._is_available(pid)]

    def _is_available(self, provider_id: str) -> bool:
        provider = self._registry.get(provider_id)
        if provider is None:
            return False
        try:
            return bool(provider.is_available())
        except Exception as exc:  # noqa: BLE001 -- best-effort
            logger.warning("Provider %s: is_available() a echoue: %s", provider_id, exc)
            return False

    # -- API publique -----------------------------------------------------------

    async def search(
        self,
        query: str,
        engine: str = "duckduckgo",
        max_results: int | None = None,
        proxy: ProxyConfig | str | None = None,
    ) -> SearchResponse:
        """Effectue une recherche sur un moteur donne.

        Args:
            query: Termes de recherche.
            engine: Identifiant de moteur (voir ``list_engines``).
            max_results: Nombre de resultats souhaite (borne a 50 max ; refus
                strict au-dela). ``None`` => defaut du manager.
            proxy: Configuration proxy/VPN optionnelle, ou identifiant de
                profil réseau (``core/network``) résolu par le Core
                (credentials depuis l'environnement, jamais en payload).

        Returns:
            SearchResponse normalisee (jamais une exception reseau --
            best-effort, l'erreur est portee dans ``metadata``).

        Raises:
            ValueError: moteur inconnu, query vide ou max_results invalide
                (notamment > MAX_RESULTS_HARD_CAP, type incorrect, < MIN_RESULTS).
        """
        query = query.strip()
        if not query:
            raise ValueError("Query de recherche vide")
        engine_key = (engine or "").strip().lower()
        provider = self._registry.get(engine_key)
        if provider is None:
            raise ValueError(
                f"Moteur inconnu : {engine!r} (disponibles : {', '.join(self._registry.ids())})"
            )
        # Validation stricte : une valeur > MAX_RESULTS_HARD_CAP est refusee.
        limit = self._max_results if max_results is None else validate_max_results(max_results)
        # Le proxy peut être un identifiant de profil réseau (str) : le Core
        # le résout en configuration interne (ValueError si profil inconnu,
        # désactivé, VPN non intégré ou credential d'environnement absent).
        proxy = self._coerce_proxy(proxy)

        started = time.monotonic()

        # Provider indisponible (dependance absente, backend HS) : reponse
        # valide mais vide ; l'erreur est portee dans ``metadata``.
        if not self._is_available(engine_key):
            return SearchResponse(
                query=query,
                engine=engine_key,
                results=[],
                total_found=0,
                search_time_ms=int((time.monotonic() - started) * 1000),
                metadata={
                    "error": f"Provider indisponible : {engine_key}",
                    "provider_unavailable": True,
                },
            )

        raw_items: list[dict[str, Any]] = []
        error: str | None = None
        try:
            raw_items = await provider.fetch(self, query, limit, proxy)
        except Exception as exc:  # noqa: BLE001 -- best-effort, remonte en metadata
            logger.warning("WebSearch %s failed: %r", query[:80], exc)
            error = str(exc)

        results = _normalize(query, engine_key, raw_items, limit=limit)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return SearchResponse(
            query=query,
            engine=engine_key,
            results=results,
            total_found=len(results),
            search_time_ms=elapsed_ms,
            metadata={"error": error} if error else {},
        )

    async def search_multiple(
        self,
        query: str,
        engines: list[str] | None = None,
        max_results_per_engine: int = 5,
        proxy: ProxyConfig | str | None = None,
    ) -> dict[str, SearchResponse]:
        """Recherche sur plusieurs moteurs en parallele.

        Un moteur en echec ne fait pas echouer les autres : chaque reponse
        porte son erreur eventuelle dans ``metadata``.

        Raises:
            ValueError: query vide, moteur inconnu ou max_results invalide.
        """
        query = query.strip()
        if not query:
            raise ValueError("Query de recherche vide")
        selected = [
            (e or "").strip().lower()
            for e in (engines if engines is not None else self._registry.ids())
        ]
        unknown = [e for e in selected if e not in self._registry]
        if unknown:
            raise ValueError(
                f"Moteurs inconnus : {', '.join(unknown)} "
                f"(disponibles : {', '.join(self._registry.ids())})"
            )
        # Validation stricte par moteur (refus de toute valeur > plafond).
        limit = validate_max_results(max_results_per_engine)
        # Résolution unique du profil réseau pour tous les moteurs.
        proxy = self._coerce_proxy(proxy)
        responses = await asyncio.gather(
            *[self.search(query, engine=e, max_results=limit, proxy=proxy) for e in selected]
        )
        return {resp.engine: resp for resp in responses}

    async def _search_duckduckgo(
        self, query: str, max_results: int, proxy: ProxyConfig | None
    ) -> list[dict[str, Any]]:
        """DuckDuckGo via ``ddgs`` (aucune clé API). Exécuté dans un thread."""
        try:
            from ddgs import DDGS
        except ImportError as exc:  # pragma: no cover - dépendance optionnelle
            raise RuntimeError("ddgs n'est pas installé (pip install ddgs)") from exc

        def _run() -> tuple[list[dict[str, Any]], str | None]:
            try:
                # Le proxy se passe au CONSTRUCTEUR ``DDGS(proxy=...)`` (API
                # ddgs >= 9) : le kwarg de ``text()`` serait ignoré.
                proxy_url = _proxy_url_with_auth(proxy)
                ddgs_kwargs: dict[str, Any] = {}
                if proxy_url:
                    ddgs_kwargs["proxy"] = proxy_url
                profile_timeout = proxy.timeout if proxy is not None else None
                if profile_timeout:
                    ddgs_kwargs["timeout"] = profile_timeout
                try:
                    ddgs = DDGS(**ddgs_kwargs) if ddgs_kwargs else DDGS()
                except TypeError:
                    # ddgs sans support ``timeout`` : repli sûr (proxy seul).
                    ddgs_kwargs.pop("timeout", None)
                    ddgs = DDGS(**ddgs_kwargs) if ddgs_kwargs else DDGS()
                results = ddgs.text(query, max_results=max_results)
                return [
                    {
                        "title": str(r.get("title", "")),
                        "url": str(r.get("href", "")),
                        "snippet": str(r.get("body", "")),
                    }
                    for r in (results or [])
                    if isinstance(r, dict)
                ], None
            except Exception as exc:  # noqa: BLE001 - remonté au caller
                return [], str(exc)

        items, error = await asyncio.to_thread(_run)
        if error:
            logger.warning("DuckDuckGo search failed: %s", error)
        return items

    async def _search_bing(
        self, query: str, max_results: int, proxy: ProxyConfig | None
    ) -> list[dict[str, Any]]:
        """Bing : récupération « best-effort » de la page de résultats."""
        return await self._fetch_engine_html(
            ("https://www.bing.com/search?" + urlencode({"q": query, "count": max_results})),
            proxy,
        )

    async def _search_yandex(
        self, query: str, max_results: int, proxy: ProxyConfig | None
    ) -> list[dict[str, Any]]:
        """Yandex : récupération « best-effort » de la page de résultats."""
        return await self._fetch_engine_html(
            "https://yandex.com/search/?" + urlencode({"text": query}),
            proxy,
        )

    async def _fetch_engine_html(self, url: str, proxy: ProxyConfig | None) -> list[dict[str, Any]]:
        """Fetch + parse d'une page de résultats (parser générique)."""
        import httpx

        async def _fetch() -> tuple[list[dict[str, Any]], str | None]:
            try:
                # httpx >= 0.26 : le transport est construit à partir du proxy
                # passé au constructeur. Assigner ``client.proxies`` après
                # coup est SANS EFFET (transport figé) — bug historique corrigé.
                proxy_kwargs: dict[str, Any] = {}
                if proxy and proxy.url:
                    proxy_kwargs["proxy"] = proxy.url
                    auth = proxy.auth
                    if auth:
                        proxy_kwargs["auth"] = auth
                async with httpx.AsyncClient(
                    timeout=(
                        proxy.timeout if proxy is not None and proxy.timeout else self._timeout
                    ),
                    follow_redirects=True,
                    headers={"User-Agent": USER_AGENT},
                    **proxy_kwargs,
                ) as client:
                    response = await client.get(url)
                    if response.status_code != 200:
                        return [], f"HTTP {response.status_code}"
                    parser = _SearchResultParser()
                    parser.feed(response.text)
                    return list(parser.results), None
            except Exception as exc:  # noqa: BLE001 - best-effort
                logger.warning("Engine fetch failed (%s): %s", url[:60], exc)
                return [], str(exc)

        items, error = await _fetch()
        if error:
            logger.warning("Search engine fetch error: %s", error)
        return items


__all__ = [
    "DEFAULT_MAX_RESULTS",
    "DEFAULT_PROVIDER_REGISTRY",
    "DEFAULT_REQUEST_TIMEOUT",
    "MAX_RESULTS_HARD_CAP",
    "MIN_RESULTS",
    "ProxyConfig",
    "SearchProvider",
    "SearchProviderRegistry",
    "SearchResult",
    "SearchResponse",
    "WebSearchManager",
    "register_search_provider",
    "validate_max_results",
]
