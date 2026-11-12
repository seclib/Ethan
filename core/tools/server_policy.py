"""Politique de sûreté des serveurs d'outils (MCP) — Core-owned, fail-closed.

Un serveur MCP / tool server est une **extension non fiable par défaut** :
il exécute des outils au nom d'ETHAN et peut atteindre le réseau interne.
Cette politique est donc appliquée dans le Core, avant tout enregistrement
et avant toute connexion (``ToolServerManager``), jamais dans une interface.

Règles (fail-closed) :

- **Identity** : ``name`` non vide et borné ; ``auth_type`` dans une
  allowlist (``none`` / ``bearer`` / ``oauth``) ;
- **Transport** : allowlist (``http`` / ``streamable_http`` / ``stdio``) —
  tout autre transport est refusé ;
- **stdio** (processus local) : ``command`` doit être un **chemin absolu
  présent dans l'allowlist d'exploitation** ``ETHAN_MCP_STDIO_ALLOWLIST``
  (liste séparée par des virgules).  Allowlist vide ⇒ stdio désactivé.
  ``args`` = liste de chaînes ; aucune interpolation shell ;
- **http** : destination contrôlée (SSRF) via **la politique d'egress du
  Core** (``core/security/egress.py``, source unique partagée avec les
  providers LLM) — destination **publique** par défaut ;
  ``ETHAN_MCP_ALLOW_PRIVATE_HOSTS=1`` autorise explicitement
  loopback / RFC1918 / ULA (serveurs MCP locaux), mais les adresses
  link-local et les endpoints de métadonnées cloud restent **toujours**
  refusés.  Credentials dans l'URL refusés (les secrets vivent dans la
  couche secret manager, jamais dans un record) ;
- **TLS** : ``verify_ssl=false`` refusé (pas de dégradation silencieuse) ;
- ``env`` / ``cwd`` : non supportés par le chemin Core — refusés s'ils sont
  fournis (rien n'est ignoré silencieusement).
"""

from __future__ import annotations

import os
import re
from typing import Any, Callable

from core.security.egress import validate_egress_url

# ── Allowlists structurelles ────────────────────────────────────────────────

TRUSTED_TRANSPORTS = frozenset({"http", "stdio"})
_TRANSPORT_ALIASES = {"streamable_http": "http", "streamable-http": "http"}
TRUSTED_AUTH_TYPES = frozenset({"none", "bearer", "oauth"})

ENV_ALLOW_PRIVATE_HOSTS = "ETHAN_MCP_ALLOW_PRIVATE_HOSTS"
ENV_STDIO_ALLOWLIST = "ETHAN_MCP_STDIO_ALLOWLIST"

# Les destinations interdites (métadonnées cloud, link-local) sont définies par
# LA politique d'egress du Core : core/security/egress.py.  Ce module ne les
# redéfinit pas (AGENTS.md : une seule politique, pas de doublon).

MAX_NAME_LENGTH = 120
MAX_URL_LENGTH = 2048

_HEADER_KEY_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+.^_`|~-]+$")


class ServerPolicyError(ValueError):
    """Configuration de serveur d'outils refusée par la politique Core."""


def _env_flag(name: str) -> bool:
    """Lit un drapeau d'environnement (``1``/``true``/``yes``/``on``)."""
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def private_hosts_allowed() -> bool:
    """True si l'opérateur a explicitement autorisé les destinations privées."""
    return _env_flag(ENV_ALLOW_PRIVATE_HOSTS)


def stdio_allowlist() -> list[str]:
    """Commandes absolues autorisées pour le transport stdio (env, ordre stable)."""
    raw = os.getenv(ENV_STDIO_ALLOWLIST, "")
    return [entry.strip() for entry in raw.split(",") if entry.strip()]


def _canonical_path(path: str) -> str:
    """Chemin canonique (symlinks résolus) pour comparer à l'allowlist."""
    try:
        return os.path.realpath(path)
    except OSError:  # pragma: no cover - realpath ne lève quasi jamais
        return os.path.abspath(path)


# ── Validation des blocs ────────────────────────────────────────────────────


def _validate_name(name: Any) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ServerPolicyError("name is required (non-empty string)")
    cleaned = name.strip()
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ServerPolicyError(f"name is too long (max {MAX_NAME_LENGTH} characters)")
    return cleaned


def _validate_auth(auth_type: Any, auth_config: Any) -> tuple[str, dict[str, Any]]:
    normalized_type = auth_type if isinstance(auth_type, str) and auth_type else "none"
    normalized_type = normalized_type.strip().lower()
    if normalized_type not in TRUSTED_AUTH_TYPES:
        raise ServerPolicyError(
            f"auth_type {auth_type!r} is not supported "
            f"(allowed: {', '.join(sorted(TRUSTED_AUTH_TYPES))})"
        )
    config = dict(auth_config) if isinstance(auth_config, dict) else {}
    if normalized_type == "bearer":
        token = config.get("token")
        if not isinstance(token, str) or not token.strip():
            raise ServerPolicyError(
                "auth_type 'bearer' requires auth_config.token "
                "(provided via the Core secret layer — never echoed back)"
            )
    return normalized_type, config


def _validate_headers(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    if not isinstance(headers, dict):
        raise ServerPolicyError("metadata.headers must be an object of string values")
    cleaned: dict[str, str] = {}
    for key, value in headers.items():
        if not isinstance(key, str) or not _HEADER_KEY_RE.match(key):
            raise ServerPolicyError(f"metadata.headers has an invalid header name: {key!r}")
        if not isinstance(value, str):
            raise ServerPolicyError(f"metadata.headers[{key!r}] must be a string")
        cleaned[key] = value
    return cleaned


def _validate_http_url(
    url: Any,
    *,
    allow_private: bool | None = None,
    resolver: Callable[[str], list[str]] | None = None,
) -> str:
    """Valide et normalise l'URL d'un serveur MCP (transport http).

    La politique de destination (schéma, credentials inline, métadonnées cloud,
    link-local, public-vs-privé) vit dans ``core/security/egress.py`` : source
    unique de toutes les connexions sortantes du Core.  Ce module n'en conserve
    que ce qui est propre aux serveurs MCP (longueur, enveloppe d'erreur) et
    traduit tout refus en ``ServerPolicyError`` (fail-closed).
    """
    if not isinstance(url, str) or not url.strip():
        raise ServerPolicyError("url is required (non-empty string)")
    raw = url.strip()
    if len(raw) > MAX_URL_LENGTH:
        raise ServerPolicyError(f"url is too long (max {MAX_URL_LENGTH} characters)")

    private_ok = private_hosts_allowed() if allow_private is None else allow_private
    try:
        return validate_egress_url(raw, allow_private=private_ok, resolver=resolver)
    except ValueError as exc:  # ServerPolicyError est un ValueError : fail-closed
        raise ServerPolicyError(str(exc)) from exc


def _validate_stdio(metadata: dict[str, Any]) -> None:
    """Transport stdio : commande absolue et explicitement autorisée."""
    command = metadata.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ServerPolicyError("transport 'stdio' requires metadata.command")
    command = command.strip()
    if not os.path.isabs(command):
        raise ServerPolicyError(
            f"stdio command must be an absolute path (got {command!r}) — "
            "relative names would resolve through PATH"
        )
    allowed = {_canonical_path(entry) for entry in stdio_allowlist()}
    if not allowed:
        raise ServerPolicyError(
            "stdio transport is disabled: set ETHAN_MCP_STDIO_ALLOWLIST to the "
            "absolute paths of the commands you trust (comma separated)"
        )
    if _canonical_path(command) not in allowed:
        raise ServerPolicyError(
            f"stdio command {command!r} is not in ETHAN_MCP_STDIO_ALLOWLIST — "
            "add its absolute path explicitly to allow it"
        )
    args = metadata.get("args") or []
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise ServerPolicyError("metadata.args must be a list of strings (no shell string)")
    for unsupported in ("env", "cwd"):
        if metadata.get(unsupported):
            raise ServerPolicyError(
                f"metadata.{unsupported} is not supported by the Core MCP path "
                "(refused instead of being silently ignored)"
            )


def _validate_metadata(metadata: Any) -> dict[str, Any]:
    """Valide et normalise les métadonnées interprétées par le Core."""
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ServerPolicyError("metadata must be an object")
    cleaned = dict(metadata)

    raw_transport = cleaned.get("transport")
    if raw_transport is None:
        transport = "http"
    elif not isinstance(raw_transport, str):
        raise ServerPolicyError("metadata.transport must be a string")
    else:
        transport = raw_transport.strip().lower()
        transport = _TRANSPORT_ALIASES.get(transport, transport)
    if transport not in TRUSTED_TRANSPORTS:
        raise ServerPolicyError(
            f"transport {raw_transport!r} is not supported "
            f"(allowed: {', '.join(sorted(TRUSTED_TRANSPORTS))})"
        )
    cleaned["transport"] = transport

    if cleaned.get("verify_ssl") is False:
        raise ServerPolicyError(
            "verify_ssl=false is not allowed: TLS verification cannot be disabled"
        )
    cleaned.pop("verify_ssl", None)

    if "headers" in cleaned:
        cleaned["headers"] = _validate_headers(cleaned.get("headers"))

    if transport == "stdio":
        _validate_stdio(cleaned)
        if cleaned.get("headers"):
            raise ServerPolicyError("metadata.headers is not supported for stdio transport")
    else:
        cleaned.pop("command", None)
        cleaned.pop("args", None)

    return cleaned


def validate_server_config(
    *,
    name: Any,
    url: Any,
    auth_type: Any = "none",
    auth_config: Any = None,
    metadata: Any = None,
    allow_private: bool | None = None,
    resolver: Callable[[str], list[str]] | None = None,
) -> dict[str, Any]:
    """Valide et normalise la configuration d'un serveur d'outils (MCP).

    Returns:
        ``{"name", "url", "auth_type", "auth_config", "metadata"}`` normalisé.

    Raises:
        ServerPolicyError: si un élément est refusé par la politique Core.
            Le message ne contient JAMAIS de valeur secrète (token, header).
    """
    cleaned_metadata = _validate_metadata(metadata)
    transport = cleaned_metadata.get("transport", "http")

    auth_type_norm, auth_config_norm = _validate_auth(auth_type, auth_config)

    if transport == "stdio":
        if not isinstance(url, str) or not url.strip():
            raise ServerPolicyError("url is required (non-empty label for stdio servers)")
        normalized_url = url.strip()
    else:
        normalized_url = _validate_http_url(url, allow_private=allow_private, resolver=resolver)

    return {
        "name": _validate_name(name),
        "url": normalized_url,
        "auth_type": auth_type_norm,
        "auth_config": auth_config_norm,
        "metadata": cleaned_metadata,
    }


__all__ = [
    "ENV_ALLOW_PRIVATE_HOSTS",
    "ENV_STDIO_ALLOWLIST",
    "MAX_NAME_LENGTH",
    "ServerPolicyError",
    "TRUSTED_AUTH_TYPES",
    "TRUSTED_TRANSPORTS",
    "private_hosts_allowed",
    "stdio_allowlist",
    "validate_server_config",
]
