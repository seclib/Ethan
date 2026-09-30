"""Politique de destination sortante (egress) d'ETHAN — Core-owned, fail-closed.

Pourquoi un module séparé
------------------------
Plusieurs surfaces du Core établissent une connexion sortante vers une URL
**fournie comme configuration** : serveurs d'outils MCP
(``core/tools/server_policy``), providers LLM (``core/llm/provider_manager``),
ingestion web (``core/knowledge/web_ingest``).  Chacune tendait à réécrire sa
propre vérification d'adresse — exactement ce qu'AGENTS.md interdit
(« éviter les doublons ») : deux politiques = deux comportements, et la plus
permissive gagne toujours.

Ce module est donc **la** politique d'egress : une seule définition des
destinations interdites, réutilisée par toutes les surfaces.

Niveaux de vérification
-----------------------
1. ``validate_egress_url`` — vérification **complète** avec résolution DNS,
   pour les destinations non fiables (serveurs MCP).  ``allow_private=False``
   impose une destination publique (garde-fou SSRF du Core) ; ``True`` tolère
   loopback / RFC1918 / ULA, uniquement si l'opérateur l'a explicitement
   demandé.
2. ``assert_literal_destination`` — vérification **littérale**, sans DNS, pour
   les endpoints configurés par un rôle authentifié (providers LLM), dont les
   valeurs légitimes sont souvent des noms internes non résolubles (``ollama``,
   ``vllm``, ``host.docker.internal``).  Résoudre ces noms au démarrage ferait
   planter ETHAN ; on bloque donc la classe « toujours interdite » (schéma,
   credentials inline, métadonnées cloud, link-local) sans dépendre du DNS.

Dans les deux niveaux, la classe « toujours interdite » est identique : c'est
précisément l'objet de ce module.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Callable
from urllib.parse import urlsplit, urlunsplit

from core.knowledge.web_ingest import (
    is_safe_public_ip,
    resolve_hostname,
    validate_public_url,
)

# Endpoints de métadonnées cloud : jamais joignables, même en mode privé.
# (Une destination détournée vers ce point de contact obtient les credentials
# de l'instance hôte — c'est l'issue SSRF la plus grave.)
METADATA_IPS = frozenset({"169.254.169.254", "fd00:ec2::254", "100.100.100.200"})
METADATA_HOSTS = frozenset({"metadata.google.internal", "metadata.goog"})

ALLOWED_SCHEMES = frozenset({"http", "https"})

__all__ = [
    "ALLOWED_SCHEMES",
    "METADATA_HOSTS",
    "METADATA_IPS",
    "assert_literal_destination",
    "is_forbidden_address",
    "resolve_destination_addresses",
    "validate_egress_url",
]


def is_forbidden_address(address: str) -> bool:
    """Link-local / métadonnées cloud : interdits même en mode privé autorisé."""
    if address in METADATA_IPS:
        return True
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return True
    if ip.is_link_local:
        return True
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        return ip.ipv4_mapped.is_link_local or str(ip.ipv4_mapped) in METADATA_IPS
    return False


def resolve_destination_addresses(
    host: str, resolver: Callable[[str], list[str]] | None = None
) -> list[str]:
    """Adresses IP d'un host (littéral direct, sinon résolution DNS fail-closed).

    Raises:
        ValueError: résolution impossible ou vide.
    """
    try:
        return [str(ipaddress.ip_address(host))]
    except ValueError:
        pass
    try:
        addresses = (resolver or resolve_hostname)(host)
    except OSError as exc:
        raise ValueError(f"DNS resolution failed for {host!r}") from exc
    if not addresses:
        raise ValueError(f"no address resolved for {host!r}")
    return list(addresses)


def _split_destination(url: str):
    """Contrôles structurels communs aux deux niveaux (schéma, creds, host).

    Raises:
        ValueError: URL inutilisable en tant que destination sortante.
    """
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"url scheme {parts.scheme!r} is not allowed (http/https only)")
    if parts.username or parts.password:
        raise ValueError(
            "credentials in the url are not supported — secrets live in the Core "
            "secret layer, never inline in a url"
        )
    host = (parts.hostname or "").lower()
    if not host:
        raise ValueError("url has no hostname")
    if host in METADATA_HOSTS:
        raise ValueError(f"metadata endpoint is forbidden: {host}")
    return parts


def _normalize(parts) -> str:
    """URL normalisée (host en minuscules, fragment jamais significatif)."""
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", parts.query, ""))


def assert_literal_destination(url: str) -> str:
    """Garde **littéral** (sans DNS) d'une URL de destination configurée.

    Conçu pour les endpoints que **seul** un rôle authentifié configure
    (providers LLM) : la légitimité y inclut des hostname internes non
    résolubles, donc la résolution DNS est volontairement évitée — elle ferait
    échouer le démarrage d'ETHAN.  La classe « toujours interdite » reste
    bloquée.

    Returns:
        L'URL normalisée.

    Raises:
        ValueError: schéma refusé, credentials inline, hôte/adresse de
            métadonnées ou adresse link-local littérale.
    """
    parts = _split_destination(url.strip())
    host = (parts.hostname or "").lower()

    try:
        literal: ipaddress.IPv4Address | ipaddress.IPv6Address | None = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and is_forbidden_address(str(literal)):
        raise ValueError(
            f"destination address is forbidden: {host} — "
            "link-local/metadata endpoints are never reachable"
        )
    return _normalize(parts)


def validate_egress_url(
    url: str,
    *,
    allow_private: bool,
    resolver: Callable[[str], list[str]] | None = None,
) -> str:
    """Garde **complet** (avec résolution DNS) d'une URL de destination non fiable.

    Args:
        url: destination à contrôler.
        allow_private: ``False`` = destination publique uniquement (garde-fou
            SSRF du Core) ; ``True`` = loopback/RFC1918/ULA tolérés, link-local
            et métadonnées toujours refusés.
        resolver: résolveur DNS injectable (tests) ; ``None`` = résolution réelle.

    Returns:
        L'URL normalisée.

    Raises:
        ValueError: destination refusée (message destiné à l'opérateur).
    """
    raw = url.strip()
    parts = _split_destination(raw)
    host = (parts.hostname or "").lower()

    if not allow_private:
        # Destination publique uniquement : source de vérité SSRF du Core.
        return _normalize(urlsplit(validate_public_url(raw, resolver)))

    for address in resolve_destination_addresses(host, resolver):
        if is_forbidden_address(address):
            raise ValueError(
                f"destination address is forbidden: {address} ({host}) — "
                "link-local/metadata endpoints are never reachable"
            )
        ip = ipaddress.ip_address(address)
        if not (ip.is_loopback or ip.is_private) and not is_safe_public_ip(ip):
            raise ValueError(f"destination address is not allowed: {address} ({host})")

    return _normalize(parts)
