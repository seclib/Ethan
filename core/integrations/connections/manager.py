"""ConnectionManager — lifecycle des connexions externes PAR UTILISATEUR.

Opérations : connecter (start + callback OAuth), reconnecter, tester
(appel API réel), voir les permissions, déconnecter, lister — et
``get_access_token`` : LE point d'entrée pour Chat, Knowledge, Skills et
Missions (abstraction totale des détails OAuth).

Sécurité :
- Les tokens vivent dans le domaine dédié ``connection-tokens`` (même
  mécanisme que ``integration-credentials``) et ne sont JAMAIS retournés.
- Les client_id/client_secret OAuth proviennent du ``SecretManager``
  (env ``ETHAN_CONN_<PROVIDER>_CLIENT_ID`` / ``_CLIENT_SECRET`` ou Vault).
- Le paramètre ``state`` OAuth est émis par le Core, persisté avec un TTL
  de 10 minutes, à usage unique, et vérifié au callback.
- Chaque connexion appartient à un utilisateur ETHAN ; toute opération
  vérifie l'appartenance (pas de fuite d'existence entre utilisateurs).
- Les events publiés ne contiennent jamais de tokens.
"""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import uuid4

from core.config.secrets import SecretManager
from core.ethan_types.event import Event, EventType
from core.integrations.connections.base import (
    ClientCredentials,
    ConnectionError,
    ConnectionProvider,
    TokenBundle,
)
from core.integrations.connections.oauth import utc_now_iso
from core.integrations.connections.providers import get_provider, list_providers
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_CONNECTIONS = "connections"
_DOMAIN_TOKENS = "connection-tokens"
_STATE_TTL_S = 600

# Statuts de la connexion utilisateur.
CONNECTION_STATUSES = ("pending", "connected", "disconnected", "error")


class ConnectionManager:
    """Gestion des connexions utilisateur aux services externes (Core-owned).

    Args:
        store: ``CoreRecordStore`` partagé (PG + Redis + fallback mémoire).
        event_bus: bus optionnel — mutations publiées sans secrets.
        secrets: ``SecretManager`` pour les client secrets OAuth (défaut : env/Vault).
        http_factory: fabrique de clients HTTP (tests ; défaut : httpx.AsyncClient).
        base_url: URL publique de l'API, pour construire les redirect_uri.
    """

    def __init__(
        self,
        store: CoreRecordStore | None = None,
        event_bus: Any | None = None,
        *,
        secrets: SecretManager | None = None,
        http_factory: Any,
        base_url: str = "",
    ) -> None:
        """Args:
        store: ``CoreRecordStore`` partagé (PG + Redis + fallback mémoire).
        event_bus: bus optionnel — mutations publiées sans secrets.
        secrets: ``SecretManager`` pour les client secrets (défaut : env/Vault).
        http_factory: fabrique de clients HTTP (OBLIGATOIRE — ADR-1005 :
            le Core n'importe aucune technologie ; l'adaptateur appelant,
            API ou Runtime, fournit p.ex. ``lambda: httpx.AsyncClient()``).
        base_url: URL publique de l'API, pour construire les redirect_uri.
        """
        self._store = store or CoreRecordStore()
        self._bus = event_bus
        self._secrets = secrets or SecretManager()
        self._http_factory = http_factory
        self._base_url = (base_url or "").rstrip("/")

    # ── Catalogue (aucun secret) ─────────────────────────────────────────

    def catalog(self) -> list[dict[str, Any]]:
        """Connecteurs disponibles : id, libellé, description, scopes."""
        result = []
        for provider in list_providers():
            result.append(
                {
                    "id": provider.id,
                    "label": provider.label,
                    "description": provider.description,
                    "auth_method": provider.auth_method,
                    "scopes": [
                        {
                            "scope": s.scope,
                            "summary": s.summary,
                            "sensitive": s.sensitive,
                        }
                        for s in provider.scopes
                    ],
                    "operations": [
                        {
                            "name": op.name,
                            "summary": op.summary,
                            "scope": op.scope,
                            "write": op.write,
                            "available": op.available,
                        }
                        for op in provider.operations
                    ],
                    # Noms requis UNIQUEMENT — jamais de valeur.
                    "credentials": [
                        {
                            "key": c.key,
                            "summary": c.summary,
                            "secret": c.secret,
                            "required": c.required,
                        }
                        for c in provider.credential_requirements
                    ],
                }
            )
        return result

    # ── Connecter / Reconnecter ──────────────────────────────────────────

    async def start(
        self, user_id: str, provider_id: str, redirect_uri: str | None = None
    ) -> dict[str, Any]:
        """Démarre une connexion : state émis + URL d'autorisation OAuth.

        Retourne ``authorization_url`` (contient ``client_id``, public par
        conception OAuth — jamais ``client_secret``) et le ``state``.
        """
        provider = get_provider(provider_id)
        creds = self._resolve_client(provider)
        redirect = redirect_uri or self._redirect_uri(provider.id)
        state = uuid4().hex
        record = {
            "id": self._connection_id(user_id, provider.id),
            "provider": provider.id,
            "user_id": user_id,
            "status": "pending",
            "state": state,
            "state_expires_at": time.time() + _STATE_TTL_S,
            "scopes_requested": [s.scope for s in provider.scopes],
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        await self._store.save(_DOMAIN_CONNECTIONS, record["id"], record)
        return {
            "connection_id": record["id"],
            "provider": provider.id,
            "authorization_url": provider.build_authorization_url(creds, redirect, state),
            "state": state,
            "scopes_requested": record["scopes_requested"],
        }

    async def reconnect(
        self, user_id: str, provider_id: str, redirect_uri: str | None = None
    ) -> dict[str, Any]:
        """Reconnecter : purge les tokens existants puis relance le flux."""
        connection_id = self._connection_id(user_id, provider_id)
        await self._store.delete(_DOMAIN_TOKENS, connection_id)
        return await self.start(user_id, provider_id, redirect_uri)

    async def callback(
        self, user_id: str, provider_id: str, code: str, state: str
    ) -> dict[str, Any]:
        """Termine le flux OAuth : vérifie le state, échange le code, teste
        réellement les tokens, stocke et publie l'event (sans secrets).
        """
        provider = get_provider(provider_id)
        connection_id = self._connection_id(user_id, provider.id)
        record = await self._require_owned(user_id, provider.id)

        if record.get("status") != "pending":
            raise ConnectionError(f"No pending OAuth flow for {provider.id!r} (run start first)")
        stored_state = record.get("state")
        expires_at = record.get("state_expires_at")
        if not stored_state or state != stored_state:
            raise ConnectionError("OAuth state mismatch — flow rejected")
        if expires_at is not None and time.time() > float(expires_at):
            raise ConnectionError("OAuth state expired — restart the connection")

        creds = self._resolve_client(provider)
        redirect = self._redirect_uri(provider.id)
        async with self._http_factory() as http:
            tokens = await provider.exchange_code(http, creds, code, redirect)
            account = await provider.test_connection(http, tokens)

        await self._store.save(_DOMAIN_TOKENS, connection_id, tokens.to_storage())
        record.update(
            status="connected",
            connected_at=utc_now_iso(),
            updated_at=utc_now_iso(),
            scopes_granted=tokens.granted_scopes,
            token_expires_at=tokens.expires_at,
            account=account,
            state=None,
            state_expires_at=None,
            last_error=None,
        )
        await self._store.save(_DOMAIN_CONNECTIONS, connection_id, record)
        await self._publish(
            EventType.CONNECTION_CONNECTED,
            connection_id,
            {
                "connection_id": connection_id,
                "provider": provider.id,
                "user_id": user_id,
            },
        )
        return self._public(record)

    # ── Tester / Permissions / Déconnecter / Lister ──────────────────────

    async def test(self, user_id: str, provider_id: str) -> dict[str, Any]:
        """Test réel : appel API du service avec les tokens stockés.

        Met à jour le statut (connected/error + last_error) et retourne le
        résultat SANS aucun secret.
        """
        provider = get_provider(provider_id)
        connection_id = self._connection_id(user_id, provider.id)
        record = await self._require_owned(user_id, provider.id)
        tokens = TokenBundle.from_storage(await self._store.get(_DOMAIN_TOKENS, connection_id))
        if tokens is None:
            raise ConnectionError(f"No stored credentials for {provider.id!r} — connect first")
        try:
            async with self._http_factory() as http:
                account = await provider.test_connection(http, tokens)
        except ConnectionError as exc:
            record.update(status="error", last_error=str(exc), updated_at=utc_now_iso())
            await self._store.save(_DOMAIN_CONNECTIONS, connection_id, record)
            await self._publish(
                EventType.CONNECTION_ERROR,
                connection_id,
                {
                    "connection_id": connection_id,
                    "provider": provider.id,
                    "user_id": user_id,
                },
            )
            raise
        record.update(
            status="connected",
            account=account,
            last_error=None,
            updated_at=utc_now_iso(),
        )
        await self._store.save(_DOMAIN_CONNECTIONS, connection_id, record)
        return {
            "connection_id": connection_id,
            "provider": provider.id,
            "status": "connected",
            "account": account,
            "tested_at": utc_now_iso(),
        }

    async def permissions(self, user_id: str, provider_id: str) -> dict[str, Any]:
        """Voir les permissions : scopes demandés vs réellement accordés."""
        provider = get_provider(provider_id)
        connection_id = self._connection_id(user_id, provider.id)
        record = await self._require_owned(user_id, provider.id)
        granted = list(record.get("scopes_granted") or [])
        return {
            "provider": provider.id,
            "connection_id": connection_id,
            "requested": [
                {"scope": s.scope, "summary": s.summary, "sensitive": s.sensitive}
                for s in provider.scopes
            ],
            "granted": granted,
        }

    async def disconnect(self, user_id: str, provider_id: str) -> dict[str, Any]:
        """Déconnecter : purge tokens + state, statut ``disconnected``."""
        provider = get_provider(provider_id)
        connection_id = self._connection_id(user_id, provider.id)
        record = await self._require_owned(user_id, provider.id)
        # Révocation upstream BEST EFFORT (ex. GitHub/Google : le token devient
        # réellement inutilisable côté service). Jamais bloquant : si le
        # service n'expose pas d'API de révocation (Medium, Notion, SMTP/IMAP),
        # la purge locale est la seule action possible — documenté par provider.
        tokens = TokenBundle.from_storage(await self._store.get(_DOMAIN_TOKENS, connection_id))
        if tokens is not None:
            try:
                creds = self._resolve_client(provider)
                async with self._http_factory() as http:
                    if await provider.revoke(http, creds, tokens):
                        logger.info("Token revoked upstream for %s", provider.id)
                    else:
                        logger.info(
                            "No upstream revocation for %s — local purge only "
                            "(no revocation API: revoke server-side if needed)",
                            provider.id,
                        )
            except Exception as exc:  # noqa: BLE001 — révocation non bloquante
                logger.warning("Upstream revocation failed for %s: %s", provider.id, exc)
        await self._store.delete(_DOMAIN_TOKENS, connection_id)
        record.update(
            status="disconnected",
            state=None,
            state_expires_at=None,
            scopes_granted=None,
            token_expires_at=None,
            connected_at=None,
            updated_at=utc_now_iso(),
        )
        await self._store.save(_DOMAIN_CONNECTIONS, connection_id, record)
        await self._publish(
            EventType.CONNECTION_DISCONNECTED,
            connection_id,
            {
                "connection_id": connection_id,
                "provider": provider.id,
                "user_id": user_id,
            },
        )
        return self._public(record)

    async def list(self, user_id: str) -> list[dict[str, Any]]:
        """Connexions de l'utilisateur (sans secret)."""
        result = []
        for record in await self._store.list(_DOMAIN_CONNECTIONS):
            if record.get("user_id") != user_id:
                continue
            result.append(self._public(record))
        return result

    async def get(self, user_id: str, provider_id: str) -> dict[str, Any] | None:
        provider = get_provider(provider_id)
        record = await self._store.get(
            _DOMAIN_CONNECTIONS, self._connection_id(user_id, provider.id)
        )
        if record is None or record.get("user_id") != user_id:
            return None
        return self._public(record)

    # ── Connexion par identifiants (SMTP/IMAP — sans OAuth) ───────────────

    async def connect_password(
        self, user_id: str, provider_id: str, credentials: dict[str, str]
    ) -> dict[str, Any]:
        """Connecte un provider à auth par identifiants (ex. SMTP/IMAP).

        Sécurité : les secrets fournis sont validés par un test RÉEL (login
        IMAP), puis stockés UNIQUEMENT dans le domaine ``connection-tokens``
        — jamais dans le record public, un event ou un log. La réponse ne
        contient aucune valeur secrète.
        """
        provider = get_provider(provider_id)
        if not provider.auth_method.startswith("password"):
            raise ConnectionError(
                f"Provider {provider.id!r} uses {provider.auth_method!r} — "
                "use the OAuth flow (connect), not credentials"
            )
        connection_id = self._connection_id(user_id, provider.id)
        credentials = {str(k): str(v) for k, v in (credentials or {}).items()}
        missing = [
            c.key
            for c in provider.credential_requirements
            if c.required and not credentials.get(c.key)
        ]
        if missing:
            raise ConnectionError(
                f"Missing required credentials for {provider.id!r}: {', '.join(missing)}"
            )

        record = {
            "id": connection_id,
            "provider": provider.id,
            "user_id": user_id,
            "status": "pending",
            "scopes_requested": [s.scope for s in provider.scopes],
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        try:
            # ``test_credentials`` n'utilise pas HTTP (IMAP/SMTP) — le contexte
            # asynchrone reste néanmoins le point d'entrée uniforme du manager.
            async with self._http_factory():
                account = await provider.test_credentials(credentials)  # test réel
        except Exception as exc:
            record.update(status="error", last_error=str(exc), updated_at=utc_now_iso())
            await self._store.save(_DOMAIN_CONNECTIONS, connection_id, record)
            await self._publish(
                EventType.CONNECTION_ERROR,
                connection_id,
                {
                    "connection_id": connection_id,
                    "provider": provider.id,
                    "user_id": user_id,
                },
            )
            raise
        # Secrets UNIQUEMENT dans le domaine dédié (record public sans secret).
        await self._store.save(_DOMAIN_TOKENS, connection_id, {"kind": "password", **credentials})
        record.update(
            status="connected",
            account=account,
            scopes_granted=[s.scope for s in provider.scopes],
            last_error=None,
            connected_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        await self._store.save(_DOMAIN_CONNECTIONS, connection_id, record)
        await self._publish(
            EventType.CONNECTION_CONNECTED,
            connection_id,
            {
                "connection_id": connection_id,
                "provider": provider.id,
                "user_id": user_id,
            },
        )
        return self._public(record)

    # ── Opérations (Chat / Knowledge / Skills / Missions) ────────────────

    async def run_operation(
        self,
        user_id: str,
        provider_id: str,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Exécute une opération DÉCLARÉE sur une connexion existante.

        Garde-fous : opération déclarée + disponible, connexion CONNECTED
        appartenant à l'utilisateur, scope/permission requis présent dans
        les scopes accordés. Le résultat ne contient JAMAIS de token.
        """
        provider = get_provider(provider_id)
        spec = provider.get_operation(operation)
        connection_id = self._connection_id(user_id, provider.id)
        record = await self._require_owned(user_id, provider.id)
        if record.get("status") != "connected":
            raise ConnectionError(f"Connection {provider.id!r} is not connected")
        granted = set(record.get("scopes_granted") or [])
        if spec.scope and spec.scope not in granted:
            raise ConnectionError(
                f"Operation {operation!r} requires scope {spec.scope!r} "
                f"(granted: {', '.join(sorted(granted)) or 'none'})"
            )
        params = dict(params or {})
        if provider.auth_method.startswith("password"):
            secret = await self._store.get(_DOMAIN_TOKENS, connection_id)
            if not secret:
                raise ConnectionError(f"No stored credentials for {provider.id!r}")
            result = await provider.run_operation(
                operation, None, {"credentials": dict(secret)}, params
            )
        else:
            access_token = await self.get_access_token(user_id, provider_id)
            async with self._http_factory() as http:
                result = await provider.run_operation(
                    operation, http, {"access_token": access_token}, params
                )
        return {"provider": provider.id, "operation": operation, "result": result}

    # ── Point d'entrée Chat / Knowledge / Skills / Missions ─────────────

    async def get_access_token(
        self, user_id: str, provider_id: str, *, auto_refresh: bool = True
    ) -> str:
        """Retourne un access token VALIDE pour les capacités ETHAN.

        Seule API à consommer par Chat/Knowledge/Skills/Missions : les
        détails OAuth (refresh, expiration, headers) restent ici. Rafraîchit
        automatiquement si le token est expiré et qu'un refresh_token existe.
        """
        provider = get_provider(provider_id)
        connection_id = self._connection_id(user_id, provider.id)
        record = await self._store.get(_DOMAIN_CONNECTIONS, connection_id)
        if record is None or record.get("user_id") != user_id:
            raise ConnectionError(f"Not connected: {provider.id!r}")
        tokens = TokenBundle.from_storage(await self._store.get(_DOMAIN_TOKENS, connection_id))
        if tokens is None:
            raise ConnectionError(f"No stored credentials for {provider.id!r} — connect first")
        if tokens.is_expired() and auto_refresh and tokens.refresh_token:
            creds = self._resolve_client(provider)
            async with self._http_factory() as http:
                refreshed = await provider.refresh_tokens(http, creds, tokens.refresh_token)
            if refreshed is not None:
                tokens = tokens.with_refresh(refreshed)
                await self._store.save(_DOMAIN_TOKENS, connection_id, tokens.to_storage())
                record.update(token_expires_at=tokens.expires_at, updated_at=utc_now_iso())
                await self._store.save(_DOMAIN_CONNECTIONS, connection_id, record)
        if tokens.is_expired():
            raise ConnectionError(f"Token expired for {provider.id!r} — reconnect required")
        return tokens.access_token

    # ── Internals ────────────────────────────────────────────────────────

    @staticmethod
    def _connection_id(user_id: str, provider_id: str) -> str:
        return f"{user_id}:{provider_id}"

    def _redirect_uri(self, provider_id: str) -> str:
        if not self._base_url:
            raise ConnectionError("Base URL not configured — pass redirect_uri explicitly")
        return f"{self._base_url}/connections/{provider_id}/callback"

    def _resolve_client(self, provider: ConnectionProvider) -> ClientCredentials:
        """Résout client_id/secret depuis le SecretManager (env/Vault).

        ⚠️ Les valeurs ne sont ni loguées ni stockées dans un record.
        """
        env_base = f"CONN_{provider.id.upper().replace('-', '_')}"
        client_id = self._secrets.get_or_none(f"{env_base}_CLIENT_ID")
        client_secret = self._secrets.get_or_none(f"{env_base}_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ConnectionError(
                f"OAuth client not configured for {provider.id!r}: set "
                f"ETHAN_{env_base}_CLIENT_ID and ETHAN_{env_base}_CLIENT_SECRET "
                "(env/Vault) before connecting"
            )
        return ClientCredentials(client_id=client_id, client_secret=client_secret)

    async def _require_owned(self, user_id: str, provider_id: str) -> dict[str, Any]:
        record = await self._store.get(
            _DOMAIN_CONNECTIONS, self._connection_id(user_id, provider_id)
        )
        if record is None or record.get("user_id") != user_id:
            raise ConnectionError(f"Connection not found for provider {provider_id!r}")
        return record

    @staticmethod
    def _public(record: dict[str, Any]) -> dict[str, Any]:
        """Copie sans champ sensible : ni tokens, ni state OAuth."""
        return {k: v for k, v in record.items() if k not in ("state", "state_expires_at")}

    async def _publish(self, event_type: EventType, subject: str, payload: dict[str, Any]) -> None:
        if self._bus is None:
            return
        await self._bus.publish(
            subject, Event(type=event_type, source="connections", payload=payload)
        )


__all__ = ["CONNECTION_STATUSES", "ConnectionManager"]
