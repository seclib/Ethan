"""App Integrations — Core-owned integration model (identity + lifecycle).

Une intégration est une connexion déclarée à un service externe (MCP,
web search, storage, automation, developer services, application externe).
Le Core possède toute la logique : identité, configuration, credentials,
capacités, permissions, health et lifecycle connect/disconnect.

Règles de sécurité (repo-wide) :
- Les credentials ne vivent JAMAIS dans le record public, les events ou les
  logs : elles sont stockées dans un domaine dédié (``integration-credentials``)
  et ne sont exposées qu'au Runtime/Core via ``get_credentials``.
- Les réponses publiques ne contiennent que ``credential_keys`` (les noms des
  clés présentes) — jamais de valeurs.
- Chaque intégration déclare les permissions ETHAN requises (mapping sur
  ``core.auth.Permission``) : le Core les valide à l'enregistrement, et le
  Runtime les applique avant tout appel — une intégration ne peut pas
  contourner les frontières de sécurité ETHAN.

Le WebUI ne gère que la configuration ; il ne consomme jamais les
credentials et n'appelle jamais les services d'intégration directement.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_INTEGRATIONS = "integrations"
_DOMAIN_CREDENTIALS = "integration-credentials"

# Kinds réellement supportés par le socle (chaque kind a un healthcheck).
INTEGRATION_KINDS = (
    "mcp",           # Model Context Protocol servers (délégation ToolServerManager)
    "web-search",    # moteurs de recherche web
    "storage",       # stockage externe (S3, GDrive, ...)
    "automation",    # plateformes d'automatisation (n8n, Zapier, ...)
    "developer",     # services développeur (GitHub, GitLab, CI, ...)
    "external-app",  # application externe générique déclarée
)

# Statuts de connexion du lifecycle.
INTEGRATION_STATUSES = ("disconnected", "connected", "error", "unknown")


class IntegrationError(ValueError):
    """Erreur de validation du modèle d'intégration."""


def _utc_now() -> str:
    return datetime.utcnow().isoformat()


class IntegrationManager:
    """Gestion des intégrations applicatives (Core-owned).

    Args:
        store: CoreRecordStore partagé (PG durable + Redis + fallback mémoire).
        event_bus: Bus d'événements optionnel (mutations publiées sans secrets).
        tool_servers: ToolServerManager optionnel — les intégrations de kind
            ``mcp`` délèguent leur healthcheck au gestionnaire existant.
    """

    def __init__(
        self,
        store: CoreRecordStore | None = None,
        event_bus: EventBus | None = None,
        *,
        tool_servers: Any | None = None,
    ) -> None:
        self._store = store or CoreRecordStore()
        self._bus = event_bus
        self._tool_servers = tool_servers

    # ── Enregistrement / lecture ────────────────────────────────────────

    async def register(
        self,
        name: str,
        kind: str,
        description: str = "",
        config: dict[str, Any] | None = None,
        credentials: dict[str, str] | None = None,
        capabilities: list[str] | None = None,
        required_permissions: list[str] | None = None,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Enregistre une intégration (secret jamais dans le record public).

        Raises:
            IntegrationError: nom dupliqué, kind inconnu, permission invalide.
        """
        name = (name or "").strip()
        if not name:
            raise IntegrationError("Integration name must not be empty")
        if await self._name_exists(name):
            raise IntegrationError(f"Integration name already exists: {name}")
        kind = self._validate_kind(kind)
        perms = self._validate_permissions(required_permissions)

        now = _utc_now()
        integration_id = str(uuid4())
        record = {
            "id": integration_id,
            "name": name,
            "kind": kind,
            "description": description,
            "config": dict(config or {}),
            "capabilities": list(capabilities or []),
            "required_permissions": perms,
            "enabled": bool(enabled),
            "status": "disconnected",
            "health": None,
            "last_connected_at": None,
            "last_checked_at": None,
            "metadata": dict(metadata or {}),
            "created_at": now,
            "updated_at": now,
        }
        await self._store.save(_DOMAIN_INTEGRATIONS, integration_id, record)

        if credentials:
            await self._store_credentials(integration_id, credentials)

        public = self._public(record)
        await self._publish(
            EventType.INTEGRATION_REGISTERED, "integration.registered", public
        )
        return public

    async def list(
        self, kind: str | None = None, enabled: bool | None = None
    ) -> list[dict[str, Any]]:
        """Liste les intégrations (sans secrets), filtrables."""
        integrations = await self._store.list(_DOMAIN_INTEGRATIONS)
        if kind is not None:
            integrations = [i for i in integrations if i.get("kind") == kind]
        if enabled is not None:
            integrations = [i for i in integrations if i.get("enabled") == enabled]
        return [self._public(i) for i in integrations]

    async def get(self, integration_id: str) -> dict[str, Any] | None:
        """Détail d'une intégration (sans secrets)."""
        record = await self._store.get(_DOMAIN_INTEGRATIONS, integration_id)
        return self._public(record) if record else None

    async def update(
        self,
        integration_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Met à jour la configuration d'une intégration.

        Champs acceptés : description, config, credentials (remplacement),
        capabilities, required_permissions, enabled, metadata. Le kind et le
        nom ne sont pas modifiables (identité stable).
        """
        record = await self._store.get(_DOMAIN_INTEGRATIONS, integration_id)
        if record is None:
            return None

        if data.get("description") is not None:
            record["description"] = str(data["description"])
        if data.get("config") is not None:
            if not isinstance(data["config"], dict):
                raise IntegrationError("config must be an object")
            record["config"] = dict(data["config"])
        if data.get("capabilities") is not None:
            record["capabilities"] = list(data["capabilities"])
        if data.get("required_permissions") is not None:
            record["required_permissions"] = self._validate_permissions(
                data["required_permissions"]
            )
        if data.get("enabled") is not None:
            record["enabled"] = bool(data["enabled"])
        if data.get("metadata") is not None:
            record["metadata"] = dict(data["metadata"])

        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_INTEGRATIONS, integration_id, record)

        if data.get("credentials") is not None:
            if not isinstance(data["credentials"], dict):
                raise IntegrationError("credentials must be an object")
            await self._store_credentials(integration_id, data["credentials"])

        public = self._public(record)
        await self._publish(EventType.INTEGRATION_UPDATED, "integration.updated", public)
        return public

    async def delete(self, integration_id: str) -> bool:
        """Supprime une intégration et purge ses credentials."""
        existed = await self._store.delete(_DOMAIN_INTEGRATIONS, integration_id)
        if existed:
            try:
                await self._store.delete(_DOMAIN_CREDENTIALS, integration_id)
            except Exception:
                logger.warning("Failed to purge credentials for %s", integration_id)
            await self._publish(
                EventType.INTEGRATION_DELETED,
                "integration.deleted",
                {"integration_id": integration_id},
            )
        return existed

    # ── Lifecycle connect / disconnect ───────────────────────────────────

    async def connect(self, integration_id: str) -> dict[str, Any]:
        """Connecte l'intégration (healthcheck avant de marquer connected)."""
        record = await self._store.get(_DOMAIN_INTEGRATIONS, integration_id)
        if record is None:
            raise IntegrationError(f"Integration not found: {integration_id}")
        if not record.get("enabled", False):
            raise IntegrationError("Integration is disabled — enable it first")

        health = await self.test_connection(integration_id)
        record["status"] = "connected" if health["connected"] else "error"
        record["health"] = health["message"]
        record["last_checked_at"] = _utc_now()
        if record["status"] == "connected":
            record["last_connected_at"] = _utc_now()
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_INTEGRATIONS, integration_id, record)

        event = (
            EventType.INTEGRATION_CONNECTED
            if record["status"] == "connected"
            else EventType.INTEGRATION_STATUS_CHANGED
        )
        await self._publish(event, "integration.status", self._public(record))
        return self._public(record)

    async def disconnect(self, integration_id: str) -> dict[str, Any] | None:
        """Déconnecte l'intégration (statut disconnected, credentials conservés)."""
        record = await self._store.get(_DOMAIN_INTEGRATIONS, integration_id)
        if record is None:
            return None
        record["status"] = "disconnected"
        record["health"] = None
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_INTEGRATIONS, integration_id, record)
        public = self._public(record)
        await self._publish(EventType.INTEGRATION_DISCONNECTED, "integration.status", public)
        return public

    # ── Healthcheck (dispatch par kind — rien d'arbitraire) ──────────────

    async def test_connection(self, integration_id: str) -> dict[str, Any]:
        """Teste la connexion d'une intégration selon son kind.

        Le socle valide ce qu'il peut valider réellement (config minimale,
        credentials présentes, serveur MCP existant via le ToolServerManager).
        Les intégrations réelles brancheront des vérifications réseau dédiées ;
        le résultat reste un verdict explicite, jamais un mensonge optimiste.
        """
        record = await self._store.get(_DOMAIN_INTEGRATIONS, integration_id)
        if record is None:
            raise IntegrationError(f"Integration not found: {integration_id}")

        kind = record.get("kind")
        checker = getattr(self, f"_check_{kind.replace('-', '_')}", None)
        if checker is None:
            raise IntegrationError(f"No healthcheck for integration kind: {kind}")

        result = await checker(record)
        record["status"] = "connected" if result["connected"] else "error"
        record["health"] = result["message"]
        record["last_checked_at"] = _utc_now()
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_INTEGRATIONS, integration_id, record)
        return result

    async def _check_common(self, record: dict[str, Any]) -> dict[str, Any]:
        """Vérifications communes : config requise + credentials requises."""
        missing: list[str] = []
        meta = record.get("metadata") or {}
        config = record.get("config") or {}
        missing.extend(
            k for k in (meta.get("required_config") or []) if not config.get(k)
        )

        creds = await self._store.get(_DOMAIN_CREDENTIALS, record["id"]) or {}
        missing.extend(
            k for k in (meta.get("required_credentials") or []) if not creds.get(k)
        )

        if missing:
            return {
                "connected": False,
                "status": "error",
                "message": f"Missing configuration: {', '.join(sorted(missing))}",
            }
        return {
            "connected": True,
            "status": "connected",
            "message": "Configuration and credentials present",
        }

    async def _check_mcp(self, record: dict[str, Any]) -> dict[str, Any]:
        """Healthcheck MCP : délégation au ToolServerManager existant.

        Une intégration MCP référence un serveur via ``config.server_id`` ;
        on vérifie son existence au lieu de dupliquer la logique MCP.
        """
        base = await self._check_common(record)
        if not base["connected"]:
            return base

        server_id = (record.get("config") or {}).get("server_id")
        if not server_id or self._tool_servers is None:
            return {
                "connected": True,
                "status": "connected",
                "message": "Configuration valid (no MCP server bound yet)",
            }
        server = await self._tool_servers.get(str(server_id))
        if server is None:
            return {
                "connected": False,
                "status": "error",
                "message": f"Bound MCP server not found: {server_id}",
            }
        return {
            "connected": True,
            "status": "connected",
            "message": (
                f"MCP server '{server.get('name')}' bound "
                f"(status: {server.get('status')})"
            ),
        }

    # Kinds sans healthcheck réseau dédié (fondation) → chemin commun :
    _check_web_search = _check_common
    _check_storage = _check_common
    _check_automation = _check_common
    _check_developer = _check_common
    _check_external_app = _check_common

    # ── Credentials (usage interne Core/Runtime uniquement) ──────────────

    async def _store_credentials(
        self, integration_id: str, credentials: dict[str, str]
    ) -> None:
        """Persiste les credentials dans le domaine dédié (jamais le record)."""
        payload = {k: str(v) for k, v in credentials.items() if v is not None}
        await self._store.save(_DOMAIN_CREDENTIALS, integration_id, payload)

    async def get_credentials(self, integration_id: str) -> dict[str, str]:
        """Retourne les credentials d'une intégration.

        ⚠️ Usage interne Core/Runtime uniquement (exécution réelle).
        JAMAIS exposé via l'API, les events ou les logs.
        """
        creds = await self._store.get(_DOMAIN_CREDENTIALS, integration_id)
        return dict(creds or {})

    async def credential_keys(self, integration_id: str) -> list[str]:
        """Noms des clés de credentials présentes (safe pour l'affichage)."""
        creds = await self._store.get(_DOMAIN_CREDENTIALS, integration_id)
        return sorted((creds or {}).keys())

    # ── Internals ────────────────────────────────────────────────────────

    @staticmethod
    def _public(record: dict[str, Any]) -> dict[str, Any]:
        """Version publique sans secrets (le record n'en contient jamais)."""
        return dict(record)

    async def _name_exists(self, name: str) -> bool:
        for record in await self._store.list(_DOMAIN_INTEGRATIONS):
            if record.get("name", "").strip().lower() == name.strip().lower():
                return True
        return False

    @staticmethod
    def _validate_kind(kind: str) -> str:
        candidate = str(kind or "").strip().lower()
        if candidate not in INTEGRATION_KINDS:
            raise IntegrationError(
                f"Unknown integration kind: {kind!r} "
                f"(supported: {', '.join(INTEGRATION_KINDS)})"
            )
        return candidate

    @staticmethod
    def _validate_permissions(perms: list[str] | None) -> list[str]:
        """Valide les permissions ETHAN requises contre le Permission enum."""
        from core.auth import Permission

        if not perms:
            return []
        valid = {p.value for p in Permission}
        normalized: list[str] = []
        for perm in perms:
            candidate = str(perm).strip().lower()
            if candidate not in valid:
                raise IntegrationError(
                    f"Unknown ETHAN permission: {perm!r} "
                    f"(valid: {', '.join(sorted(valid))})"
                )
            if candidate not in normalized:
                normalized.append(candidate)
        return normalized

    async def _publish(
        self, event_type: EventType, subject: str, payload: dict[str, Any]
    ) -> None:
        if self._bus is None:
            return
        await self._bus.publish(
            subject,
            Event(type=event_type, source="integrations", payload=payload),
        )


__all__ = [
    "IntegrationManager",
    "IntegrationError",
    "INTEGRATION_KINDS",
    "INTEGRATION_STATUSES",
]
