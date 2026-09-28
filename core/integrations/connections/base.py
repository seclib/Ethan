"""Contrat commun ``ConnectionProvider`` — le cœur de l'abstraction.

Chaque service externe implémente ce contrat. Les consommateurs ETHAN
(Chat, Knowledge, Skills, Missions) passent par ``ConnectionManager`` et ne
connaissent JAMAIS les détails OAuth d'un service : URLs, séparateurs de
scopes, formats d'échange, refresh et headers API restent dans le provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol


class ConnectionError(ValueError):
    """Erreur du domaine Connections (config, OAuth, test, usage)."""


@dataclass(frozen=True)
class ScopeSpec:
    """Scope OAuth défini EXPLICITEMENT par le provider.

    Attributes:
        scope: Chaîne scope exacte envoyée au provider (ex. ``repo``).
        summary: Explication utilisateur (affichée par « Voir les permissions »).
        sensitive: True si le scope permet d'écrire/publier des données.
    """

    scope: str
    summary: str
    sensitive: bool = False


@dataclass(frozen=True)
class OperationSpec:
    """Opération exposée par un connecteur — déclarée EXPLICITEMENT.

    Attributes:
        name: identifiant d'opération (ex. ``list_repos``) — exécutée via
            ``run_operation`` qui refuse tout ce qui n'est pas déclaré.
        summary: description utilisateur.
        scope: scope/permission requis (``None`` = aucune exigence).
        write: True si l'opération modifie des données distantes.
        available: False = l'API officielle du service ne la permet PAS ;
            déclaré pour transparence, refusé à l'exécution.
    """

    name: str
    summary: str
    scope: str | None = None
    write: bool = False
    available: bool = True


@dataclass(frozen=True)
class CredentialRequirement:
    """Credential requis par un connecteur (déclaration explicite).

    ``secret=True`` → la valeur ne doit JAMAIS apparaître dans un record
    public, un event, un log ou une réponse API ; elle vit uniquement dans
    le domaine dédié ``connection-tokens`` (store secrets Core/Runtime).
    """

    key: str
    summary: str
    secret: bool = True
    required: bool = True


@dataclass(frozen=True)
class ClientCredentials:
    """Identifiants OAuth de l'APPLICATION ETHAN auprès du provider.

    Résolus depuis le ``SecretManager`` (env/Vault) au moment du flux —
    jamais sérialisés dans les records, les events ou les réponses API.
    Le ``repr`` masque le secret : un log accidentel ne fuit jamais.
    """

    client_id: str
    client_secret: str

    def __repr__(self) -> str:
        return f"ClientCredentials(client_id={self.client_id!r}, client_secret=***)"


@dataclass
class TokenBundle:
    """Résultat d'un échange/refresh OAuth (usage interne Core uniquement).

    Ne JAMAIS exposer via l'API : ``to_storage()`` alimente le domaine
    dédié ``connection-tokens`` ; ``account`` (identité diste non secrète)
    part dans le record public.
    """

    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None
    granted_scopes: list[str] = field(default_factory=list)
    token_type: str = "Bearer"
    account: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, margin_s: int = 30, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        import time

        current = now if now is not None else time.time()
        return current >= self.expires_at - margin_s

    def to_storage(self) -> dict[str, Any]:
        """Payload du domaine ``connection-tokens`` (sans ``account``)."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "granted_scopes": list(self.granted_scopes),
            "token_type": self.token_type,
        }

    @classmethod
    def from_storage(cls, data: dict[str, Any] | None) -> TokenBundle | None:
        if not data or not data.get("access_token"):
            return None
        return cls(
            access_token=str(data["access_token"]),
            refresh_token=data.get("refresh_token"),
            expires_at=data.get("expires_at"),
            granted_scopes=list(data.get("granted_scopes") or []),
            token_type=str(data.get("token_type") or "Bearer"),
        )

    def with_refresh(self, refreshed: TokenBundle) -> TokenBundle:
        """Fusionne un refresh : le refresh_token peut ne pas être renvoyé."""
        return TokenBundle(
            access_token=refreshed.access_token,
            refresh_token=refreshed.refresh_token or self.refresh_token,
            expires_at=refreshed.expires_at,
            granted_scopes=refreshed.granted_scopes or self.granted_scopes,
            token_type=refreshed.token_type or self.token_type,
            account=self.account,
        )


class HttpLike(Protocol):
    """Sous-ensemble de ``httpx.AsyncClient`` utilisé par les providers."""

    async def get(self, url: str, **kwargs: Any) -> Any: ...

    async def post(self, url: str, **kwargs: Any) -> Any: ...

    async def patch(self, url: str, **kwargs: Any) -> Any: ...

    async def delete(self, url: str, **kwargs: Any) -> Any: ...


class ConnectionProvider(ABC):
    """Contrat qu'implémente chaque connecteur externe.

    Attributes de classe à définir :
        id: identifiant stable (ex. ``github``) — clé du registry.
        label / description: affichage utilisateur.
        authorize_url / token_url: endpoints OAuth du service.
    """

    id: str
    label: str
    description: str
    authorize_url: str
    token_url: str

    @property
    @abstractmethod
    def scopes(self) -> list[ScopeSpec]:
        """Scopes demandés — définis EXPLICITEMENT (peut être vide, ex. Notion)."""

    def extra_authorize_params(self) -> dict[str, str]:
        """Paramètres additionnels d'autorisation (ex. Google offline)."""
        return {}

    def scope_separator(self) -> str:
        """Séparateur de scopes dans l'URL d'autorisation (défaut : espace)."""
        return " "

    # ── Flux OAuth ───────────────────────────────────────────────────────

    def build_authorization_url(
        self,
        creds: ClientCredentials,
        redirect_uri: str,
        state: str,
        extra: dict[str, str] | None = None,
    ) -> str:
        """URL d'autorisation. ``client_secret`` n'apparaît JAMAIS ici
        (public par conception OAuth) ; ``client_id`` si.
        """
        from urllib.parse import urlencode

        params: dict[str, str] = {
            "client_id": creds.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
        }
        scopes = [s.scope for s in self.scopes]
        if scopes:
            params["scope"] = self.scope_separator().join(scopes)
        params.update(self.extra_authorize_params())
        params.update(extra or {})
        return f"{self.authorize_url}?{urlencode(params)}"

    @abstractmethod
    async def exchange_code(
        self,
        http: HttpLike,
        creds: ClientCredentials,
        code: str,
        redirect_uri: str,
    ) -> TokenBundle:
        """Échange ``code`` contre des tokens (appel HTTP réel)."""

    async def refresh_tokens(
        self, http: HttpLike, creds: ClientCredentials, refresh_token: str
    ) -> TokenBundle | None:
        """Rafraîchit les tokens. ``None`` si le service n'émet pas de
        refresh token (ex. GitHub, Notion) — ``get_access_token`` le gère.
        """
        return None

    # ── Déclaration explicite (les 8 points d'audit, par connecteur) ─────

    auth_method: str = "oauth2-authorization-code"

    @property
    def credential_requirements(self) -> list[CredentialRequirement]:
        """Credentials requis (défaut OAuth : client_id/secret SecretManager)."""
        return [
            CredentialRequirement(
                "client_id", "ID client OAuth (SecretManager env/Vault).", secret=False
            ),
            CredentialRequirement(
                "client_secret", "Secret client OAuth (SecretManager env/Vault)."
            ),
        ]

    @property
    @abstractmethod
    def operations(self) -> list[OperationSpec]:
        """Opérations exposées — déclarées EXPLICITEMENT (peut être vide)."""

    def get_operation(self, name: str) -> OperationSpec:
        """Opération déclarée (refuse l'inconnu et l'indisponible, explicitement)."""
        for spec in self.operations:
            if spec.name == name:
                if not spec.available:
                    raise ConnectionError(
                        f"Operation {name!r} is not supported by the {self.label} "
                        "official API (declared unavailable for transparency)"
                    )
                return spec
        raise ConnectionError(f"Unknown operation {name!r} for provider {self.id!r}")

    async def run_operation(
        self,
        name: str,
        http: HttpLike | None,
        ctx: dict[str, Any],
        params: dict[str, Any],
    ) -> Any:
        """Exécute une opération déclarée — dispatch ``op_<name>``.

        ``ctx`` contient ``access_token`` (OAuth) ou ``credentials``
        (auth par identifiants). Le dispatch passe par le provider : les
        consommateurs ETHAN ne connaissent JAMAIS les détails du service.
        """
        self.get_operation(name)
        handler = getattr(self, f"op_{name}", None)
        if handler is None:
            raise ConnectionError(
                f"Operation {name!r} is declared but not implemented for {self.id!r}"
            )
        return await handler(http, ctx, params)

    async def revoke(self, http: HttpLike, creds: ClientCredentials, tokens: TokenBundle) -> bool:
        """Révoque le token auprès du service (best effort, non bloquant).

        ``False`` = le service n'expose PAS d'API de révocation : la
        déconnexion ETHAN purge les tokens locaux ; la révocation côté
        service reste à la charge de l'utilisateur (documenté par provider).
        """
        return False

    # ── Vérification réelle ──────────────────────────────────────────────

    @abstractmethod
    async def test_connection(self, http: HttpLike, tokens: TokenBundle) -> dict[str, Any]:
        """Appel API RÉEL avec les tokens : prouve qu'ils fonctionnent.

        Retourne une identité diste NON SECRÈTE (login, email, workspace).
        Lève ``ConnectionError`` en cas d'échec (statut HTTP, payload).
        """

    # ── Helpers ──────────────────────────────────────────────────────────

    def parse_granted_scopes(self, raw: str | None) -> list[str]:
        """Parse le champ ``scope`` de la réponse token (séparateurs variables)."""
        import re

        return [s for s in re.split(r"[,\s]+", raw or "") if s]

    @staticmethod
    def raise_if_http_error(status_code: int, service: str, body: Any = None) -> None:
        if status_code >= 400:
            raise ConnectionError(f"{service} request failed (HTTP {status_code}): {body!r}")

    @staticmethod
    def clean_account(**parts: Any) -> dict[str, Any]:
        """Identité diste publique : supprime les champs ``None``."""
        return {k: v for k, v in parts.items() if v is not None}
