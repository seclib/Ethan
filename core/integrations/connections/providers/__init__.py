"""Registry des ConnectionProvider (extensible).

Connecteurs livrés : ``email`` (Gmail OAuth), ``email-smtp-imap``
(IMAP/SMTP générique), ``github``, ``medium``, ``notion``.

Ajouter un connecteur (GitLab, Google Drive, Slack, Discord, Reddit…) :
1. créer ``providers/<service>.py`` implémentant ``ConnectionProvider``
   (scopes explicites via ``ScopeSpec``, échange, refresh si supporté,
   ``test_connection`` réel) ;
2. l'importer et l'enregistrer ci-dessous via ``register_provider``.

Aucun autre endroit du Core n'a besoin d'être modifié : le catalogue, le
manager et l'API découvrent automatiquement les nouveaux connecteurs.
"""

from __future__ import annotations

from core.integrations.connections.base import ConnectionError, ConnectionProvider

_PROVIDERS: dict[str, ConnectionProvider] = {}


def register_provider(provider: ConnectionProvider) -> None:
    """Enregistre un provider (id unique, instance non mutée)."""
    provider_id = getattr(provider, "id", "")
    if not provider_id:
        raise ConnectionError("ConnectionProvider must define an 'id'")
    if provider_id in _PROVIDERS:
        raise ConnectionError(f"Connection provider already registered: {provider_id!r}")
    _PROVIDERS[provider_id] = provider


def get_provider(provider_id: str) -> ConnectionProvider:
    """Retourne le provider demandé ou lève une erreur explicite."""
    provider = _PROVIDERS.get(str(provider_id or "").strip().lower())
    if provider is None:
        raise ConnectionError(
            f"Unknown connection provider: {provider_id!r} "
            f"(available: {', '.join(sorted(_PROVIDERS))})"
        )
    return provider


def list_providers() -> list[ConnectionProvider]:
    """Providers enregistrés, ordre alphabétique stable."""
    return [_PROVIDERS[pid] for pid in sorted(_PROVIDERS)]


def provider_ids() -> list[str]:
    return sorted(_PROVIDERS)


# ── Connecteurs livrés avec ETHAN ────────────────────────────────────────
from core.integrations.connections.providers.email import GmailProvider  # noqa: E402
from core.integrations.connections.providers.email_smtp_imap import (  # noqa: E402
    EmailSmtpImapProvider,
)
from core.integrations.connections.providers.github import GitHubProvider  # noqa: E402
from core.integrations.connections.providers.medium import MediumProvider  # noqa: E402
from core.integrations.connections.providers.notion import NotionProvider  # noqa: E402

register_provider(GitHubProvider())
register_provider(NotionProvider())
register_provider(MediumProvider())
register_provider(GmailProvider())
register_provider(EmailSmtpImapProvider())

__all__ = [
    "get_provider",
    "list_providers",
    "provider_ids",
    "register_provider",
]
