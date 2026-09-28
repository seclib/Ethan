"""Connecteur Email — Gmail via Google OAuth2 (API officielle Gmail).

SÉPARATION DES MODES : ce connecteur = API Google (OAuth). Pour une boîte
générique (FAI, auto-hébergé), voir ``email_smtp_imap.py`` — auth par
identifiants IMAP/SMTP, jamais les deux mélangés.

Audit des 8 points :
1. Auth : OAuth2 Google (authorization-code), ``access_type=offline`` +
   ``prompt=consent`` pour obtenir un refresh token.
2. Scopes (granularité Gmail, pas de ``mail.google.com`` complet) :
   ``openid`` + ``userinfo.email`` (identité), ``gmail.readonly``
   (lecture), ``gmail.send`` (envoi — sensible).
3. Credentials : client_id/client_secret OAuth Google via SecretManager.
4. Opérations (Gmail API v1 officielle) : ``get_profile``,
   ``list_messages``, ``get_message``, ``send_message``. Limites : pas de
   gestion des libellés/filtres (non implémenté, moindre privilège), rate
   limits Google (quota project).
5. Test : ``GET /gmail/v1/users/me/profile`` — adresse + compteurs publics.
6. Révocation : API Google documentée ``POST /oauth2.googleapis.com/revoke``
   (token invalide côté Google) — appelée par la déconnexion ETHAN.
7. Erreurs : statut HTTP >= 400 → ``ConnectionError`` avec le corps du
   service ; payload OAuth invalide → erreur explicite.
8. Expiration : ``expires_in`` → ``expires_at`` ; ``refresh_tokens``
   implémente le renouvellement (grant ``refresh_token`` Google).
"""

from __future__ import annotations

import base64
from email.mime.text import MIMEText
from typing import Any

from core.integrations.connections.base import (
    ClientCredentials,
    ConnectionError,
    ConnectionProvider,
    HttpLike,
    OperationSpec,
    ScopeSpec,
    TokenBundle,
)
from core.integrations.connections.oauth import decode_token_response, epoch_in

_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
_GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
_SCOPE_READONLY = "https://www.googleapis.com/auth/gmail.readonly"
_SCOPE_SEND = "https://www.googleapis.com/auth/gmail.send"


class GmailProvider(ConnectionProvider):
    id = "email"
    label = "Email (Gmail)"
    description = "Boîte Gmail : lecture des messages et envoi d'emails (API Google)."
    authorize_url = _AUTHORIZE_URL
    token_url = _TOKEN_URL

    @property
    def scopes(self) -> list[ScopeSpec]:
        return [
            ScopeSpec("openid", "Identifier le compte Google.", False),
            ScopeSpec(
                "https://www.googleapis.com/auth/userinfo.email",
                "Connaître l'adresse du compte.",
                False,
            ),
            ScopeSpec(
                _SCOPE_READONLY,
                "Lire les messages et métadonnées Gmail.",
                False,
            ),
            ScopeSpec(
                _SCOPE_SEND,
                "Envoyer des emails au nom de l'utilisateur.",
                True,
            ),
        ]

    @property
    def operations(self) -> list[OperationSpec]:
        return [
            OperationSpec(
                "get_profile",
                "Profil de la boîte (adresse, compteurs).",
                scope=_SCOPE_READONLY,
            ),
            OperationSpec("list_messages", "Lister les messages récents.", scope=_SCOPE_READONLY),
            OperationSpec("get_message", "Lire un message complet.", scope=_SCOPE_READONLY),
            OperationSpec("send_message", "Envoyer un email.", scope=_SCOPE_SEND, write=True),
        ]

    def extra_authorize_params(self) -> dict[str, str]:
        # Garantit l'obtention d'un refresh_token Google.
        return {"access_type": "offline", "prompt": "consent"}

    def _api_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    async def exchange_code(
        self, http: HttpLike, creds: ClientCredentials, code: str, redirect_uri: str
    ) -> TokenBundle:
        response = await http.post(
            self.token_url,
            data={
                "code": code,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        data = decode_token_response(response, "Google")
        if not data.get("access_token"):
            raise ConnectionError(
                f"Google OAuth exchange failed: {data.get('error_description') or data!r}"
            )
        return TokenBundle(
            access_token=str(data["access_token"]),
            refresh_token=data.get("refresh_token"),
            expires_at=epoch_in(data.get("expires_in")),
            granted_scopes=self.parse_granted_scopes(data.get("scope")),
            token_type=str(data.get("token_type") or "Bearer"),
        )

    async def refresh_tokens(
        self, http: HttpLike, creds: ClientCredentials, refresh_token: str
    ) -> TokenBundle | None:
        response = await http.post(
            self.token_url,
            data={
                "refresh_token": refresh_token,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "grant_type": "refresh_token",
            },
        )
        data = decode_token_response(response, "Google")
        if not data.get("access_token"):
            raise ConnectionError(
                f"Google token refresh failed: {data.get('error_description') or data!r}"
            )
        return TokenBundle(
            access_token=str(data["access_token"]),
            expires_at=epoch_in(data.get("expires_in")),
            granted_scopes=self.parse_granted_scopes(data.get("scope")),
            token_type=str(data.get("token_type") or "Bearer"),
        )

    async def revoke(self, http: HttpLike, creds: ClientCredentials, tokens: TokenBundle) -> bool:
        """Révocation RÉELLE (endpoint Google documenté) : le refresh token
        et les access tokens liés deviennent inutilisables côté Google."""
        response = await http.post(_REVOKE_URL, data={"token": tokens.access_token})
        return response.status_code == 200

    async def test_connection(self, http: HttpLike, tokens: TokenBundle) -> dict[str, Any]:
        data = await self._get_profile(http, tokens.access_token)
        return self.clean_account(
            email=data.get("emailAddress"),
            messages_total=data.get("messagesTotal"),
        )

    async def _get_profile(self, http: HttpLike, access_token: str) -> dict[str, Any]:
        response = await http.get(f"{_GMAIL_API}/profile", headers=self._api_headers(access_token))
        self.raise_if_http_error(response.status_code, "Gmail", response.text)
        return response.json() or {}

    # ── Opérations (Gmail API v1 officielle) ──────────────────────────────

    async def op_get_profile(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._get_profile(http, ctx["access_token"])
        return self.clean_account(
            email=data.get("emailAddress"),
            messages_total=data.get("messagesTotal"),
            threads_total=data.get("threadsTotal"),
        )

    async def op_list_messages(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(params.get("limit", 10)), 100))
        response = await http.get(
            f"{_GMAIL_API}/messages?maxResults={limit}",
            headers=self._api_headers(ctx["access_token"]),
        )
        self.raise_if_http_error(response.status_code, "Gmail", response.text)
        return [
            {"id": m.get("id"), "thread_id": m.get("threadId")}
            for m in ((response.json() or {}).get("messages") or [])
        ]

    async def op_get_message(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        message_id = str(params.get("message_id") or "")
        if not message_id:
            raise ConnectionError("get_message requires 'message_id'")
        response = await http.get(
            f"{_GMAIL_API}/messages/{message_id}?format=full",
            headers=self._api_headers(ctx["access_token"]),
        )
        self.raise_if_http_error(response.status_code, "Gmail", response.text)
        data = response.json() or {}
        headers = {
            str(h.get("name")).lower(): str(h.get("value"))
            for h in (data.get("payload") or {}).get("headers") or []
        }
        return self.clean_account(
            id=data.get("id"),
            thread_id=data.get("threadId"),
            subject=headers.get("subject"),
            sender=headers.get("from"),
            date=headers.get("date"),
            snippet=data.get("snippet"),
        )

    async def op_send_message(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        to = str(params.get("to") or "").strip()
        subject = str(params.get("subject") or "").strip()
        body = str(params.get("body") or "")
        if not to or not subject:
            raise ConnectionError("send_message requires 'to' and 'subject'")
        mime = MIMEText(body, "plain", "utf-8")
        mime["To"] = to
        mime["Subject"] = subject
        if params.get("cc"):
            mime["Cc"] = str(params["cc"])
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("ascii")
        response = await http.post(
            f"{_GMAIL_API}/messages/send",
            headers={
                **self._api_headers(ctx["access_token"]),
                "Content-Type": "application/json",
            },
            json={"raw": raw},
        )
        self.raise_if_http_error(response.status_code, "Gmail", response.text)
        data = response.json() or {}
        return {"id": data.get("id"), "thread_id": data.get("threadId")}
