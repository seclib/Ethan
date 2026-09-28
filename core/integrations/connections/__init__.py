"""Connections — abstraction commune des connecteurs externes (Core-owned).

Ce paquet implémente l'architecture « Connections » d'ETHAN : chaque
UTILISATEUR peut lier ses comptes de services externes (Email, GitHub,
Medium, Notion, puis GitLab, Google Drive, Slack, Discord, Reddit…), et les
capacités ETHAN (Chat, Knowledge, Skills, Missions) les consomment via une
API unique — sans jamais connaître les détails OAuth de chaque service.

Réutilisation du socle existant (aucun système parallèle) :
- ``CoreRecordStore``  → persistence (PG durable + Redis + fallback mémoire),
  domaine ``connections`` (records publics) et ``connection-tokens`` (tokens,
  jamais exposés — même posture que ``integration-credentials``).
- ``SecretManager``    → client_id/client_secret OAuth résolus depuis
  env/Vault (``ETHAN_CONN_<PROVIDER>_CLIENT_ID`` / ``_CLIENT_SECRET``),
  JAMAIS stockés dans les records ni dans le code.
- ``EventBus``         → mutations publiées sans secrets
  (``ethan.connection.*``).

Règles de sécurité (repo-wide) :
- Les tokens ne vivent JAMAIS dans le record public, les events ou les logs.
- L'API ne retourne jamais un token : seulement statut, scopes et identité
  diste (login/email) renvoyée par le service.
- Chaque connexion est liée à l'utilisateur ETHAN propriétaire (``user_id``)
  ; toute opération vérifie l'appartenance.
- Les scopes/permissions de chaque provider sont définis EXPLICITEMENT dans
  le provider (``ScopeSpec``) et exposés via le catalogue.
"""

from __future__ import annotations

from core.integrations.connections.base import (
    ClientCredentials,
    ConnectionError,
    ConnectionProvider,
    ScopeSpec,
    TokenBundle,
)
from core.integrations.connections.manager import ConnectionManager
from core.integrations.connections.providers import (
    get_provider,
    list_providers,
    provider_ids,
    register_provider,
)

__all__ = [
    "ClientCredentials",
    "ConnectionError",
    "ConnectionProvider",
    "ConnectionManager",
    "ScopeSpec",
    "TokenBundle",
    "get_provider",
    "list_providers",
    "provider_ids",
    "register_provider",
]
