"""Validation des sources d'installation MCP — acquisition non exécutable.

Ce module centralise les contrôles de sûreté appliqués AVANT toute lecture de
métadonnées réseau ou clone : schéma, hôte, SSRF (destinations privées,
link-local, métadonnées cloud), credentials inline et bornes de taille.

Les refus sont explicites (``McpSourceValidationError``) : jamais de
contournement silencieux. Aucune valeur secrète n'est incluse dans les
messages d'erreur.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from core.security.egress import (
    is_forbidden_address,
    resolve_destination_addresses,
    validate_egress_url,
)
from core.tools.server_policy import private_hosts_allowed

_MAX_SOURCE_LENGTH = 2048
_MAX_NPM_STDOUT = 1_000_000  # 1 Mo — borne lecture seule de `npm view`
_NPM_NAME_RE = re.compile(
    r"^(?:@[a-z0-9][a-z0-9._-]{0,213}/)?[a-z0-9][a-z0-9._-]{0,213}$"
)
_GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})


class McpSourceValidationError(ValueError):
    """Source refusée : invalide, non supportée ou dangereuse."""

    def __init__(self, message: str, *, code: str = "MCP-SOURCE-INVALID") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ValidatedSource:
    """Source normalisée et validée (jamais exécutée)."""

    original: str
    normalized: str
    kind: str


def validate_source_text(source: str) -> str:
    """Borne et normalise la chaîne source fournie par un client."""
    if not isinstance(source, str):
        raise McpSourceValidationError("la source doit être une chaîne")
    normalized = source.strip()
    if not normalized:
        raise McpSourceValidationError("une source est requise", code="MCP-SOURCE")
    if len(normalized) > _MAX_SOURCE_LENGTH:
        raise McpSourceValidationError(
            f"source trop longue (max {_MAX_SOURCE_LENGTH})", code="MCP-SOURCE"
        )
    # Aucun caractère de contrôle : une source est une URL, un nom ou une
    # commande/argv sérialisée, jamais un flux binaire.
    if any(ord(ch) < 32 and ch not in "\t" for ch in normalized):
        raise McpSourceValidationError("la source contient des caractères de contrôle")
    return normalized


def validate_npm_package_name(package: str) -> str:
    """Valide un nom de package npm (sans exécuter npm)."""
    name = (package or "").strip()
    if not name:
        raise McpSourceValidationError("nom de package npm requis")
    if not _NPM_NAME_RE.match(name):
        raise McpSourceValidationError(
            f"nom de package npm invalide: {name!r}", code="MCP-SOURCE-INVALID"
        )
    return name


def validate_github_url(url: str) -> str:
    """Valide une URL de dépôt GitHub (clone en lecture seule uniquement).

    Contrôles : https, hôte github.com, pas de credentials inline, pas de
    destination privée/link-local/métadonnées (y compris si le nom résout vers
    une adresse interdite). Les redirections git ne sont pas suivies ici mais
    le clone est borné (timeout/profondeur) et le code cloné n'est jamais
    exécuté par la phase d'analyse.
    """
    raw = validate_source_text(url)
    parts = urlsplit(raw)
    if parts.scheme != "https":
        raise McpSourceValidationError(
            "les dépôts GitHub doivent utiliser https", code="MCP-SOURCE-INVALID"
        )
    if parts.username or parts.password:
        raise McpSourceValidationError(
            "les credentials inline dans l'URL sont interdits",
            code="MCP-SOURCE-INVALID",
        )
    host = (parts.hostname or "").lower()
    if host not in _GITHUB_HOSTS:
        raise McpSourceValidationError(
            "seul github.com est accepté comme source de dépôt",
            code="MCP-SOURCE-UNSUPPORTED",
        )
    # SSRF : même si le nom est github.com, on refuse toute résolution vers une
    # adresse interdite (défense en profondeur contre DNS rebinding local).
    try:
        addresses = resolve_destination_addresses(host)
    except ValueError as exc:
        raise McpSourceValidationError(
            f"résolution DNS impossible pour {host}: {exc}", code="MCP-SOURCE-INVALID"
        ) from exc
    for address in addresses:
        if is_forbidden_address(address):
            raise McpSourceValidationError(
                f"destination interdite pour {host}", code="MCP-SSRF"
            )
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise McpSourceValidationError(
                f"adresse résolue invalide pour {host}", code="MCP-SSRF"
            ) from exc
        if ip.is_loopback or ip.is_link_local or ip.is_private or ip.is_reserved:
            # github.com doit résoudre vers du public ; une résolution privée est
            # un signal SSRF/rebinding.
            raise McpSourceValidationError(
                f"destination privée/interdite pour {host}", code="MCP-SSRF"
            )
    # Chemin minimal /owner/repo
    segments = [seg for seg in (parts.path or "").split("/") if seg]
    if len(segments) < 2:
        raise McpSourceValidationError(
            "URL GitHub invalide: attendu https://github.com/<owner>/<repo>",
            code="MCP-SOURCE-INVALID",
        )
    return raw


def validate_remote_http_url(url: str) -> str:
    """Valide une URL d'endpoint MCP distant (politique d'egress du Core).

    Réutilise la politique unique d'egress (schéma, credentials, métadonnées,
    link-local, public/privé selon configuration opérateur) — aucun doublon.
    """
    raw = validate_source_text(url)
    try:
        return validate_egress_url(raw, allow_private=private_hosts_allowed())
    except ValueError as exc:
        message = str(exc)
        lowered = message.lower()
        is_ssrf = (
            "forbidden" in lowered
            or "not allowed" in lowered
            or "metadata" in lowered
            or "private" in lowered
            or "link-local" in lowered
        )
        code = "MCP-SSRF" if is_ssrf else "MCP-SOURCE-INVALID"
        raise McpSourceValidationError(message, code=code) from exc


def bounded_stdout(raw: str | bytes | None, limit: int = _MAX_NPM_STDOUT) -> str:
    """Retourne une sortie texte bornée (lecture seule, sans exécution)."""
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = raw
    if len(text) > limit:
        raise McpSourceValidationError(
            f"réponse de métadonnées trop volumineuse (>{limit} octets)",
            code="MCP-SOURCE-TOO-LARGE",
        )
    return text
