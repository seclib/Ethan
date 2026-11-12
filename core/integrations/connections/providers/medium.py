"""Connecteur Medium — OAuth2 (publication de contenu).

Audit des 8 points :
1. Auth : OAuth2 authorization-code (endpoint officiel ``medium.com/m/oauth``).
2. Scopes : ``basicProfile`` (profil), ``listPublications`` (publications),
   ``publishPost`` (publier — sensible). ``uploadImage`` n'est PAS demandé :
   l'upload d'image n'est pas implémenté (moindre privilège).
3. Credentials : client_id/client_secret de l'intégration Medium, résolus
   depuis le ``SecretManager``.
4. Opérations (API officielle v1) : ``get_me``, ``list_publications``,
   ``create_post``. LIMITES DOCUMENTÉES de l'API Medium : accès en bêta
   limitée, publication uniquement (pas de lecture d'articles tiers),
   ``content_format`` html ou markdown, ``publish_status`` draft/published/
   unlisted, tags limités à 5, images par URL uniquement.
5. Test : ``GET /v1/me`` avec le token — identité publique seule.
6. Révocation : Medium n'expose AUCUNE API de révocation — l'utilisateur
   révoque l'intégration depuis ses paramètres Medium ; la déconnexion
   ETHAN purge les tokens locaux (contrat de base : ``revoke → False``).
7. Erreurs : statut HTTP >= 400 → ``ConnectionError`` avec le corps du
   service ; payload invalide → erreur explicite.
8. Expiration : Medium n'émet PAS de refresh token documenté — le token
   est long-lived ; ``refresh_tokens`` suit le contrat de base (``None``).
   On ne fabrique PAS d'endpoint de refresh inexistant : en cas d'échec
   401, l'utilisateur utilise Reconnecter.
"""

from __future__ import annotations

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

_API_BASE = "https://api.medium.com/v1"
_PUBLISH_STATUSES = ("draft", "published", "unlisted")


class MediumProvider(ConnectionProvider):
    id = "medium"
    label = "Medium"
    description = "Publication et gestion des articles Medium de l'utilisateur."
    authorize_url = "https://medium.com/m/oauth/authorize"
    token_url = "https://api.medium.com/v1/tokens"

    @property
    def scopes(self) -> list[ScopeSpec]:
        return [
            ScopeSpec("basicProfile", "Lire le profil public Medium.", False),
            ScopeSpec("listPublications", "Lister les publications suivies.", False),
            ScopeSpec("publishPost", "Publier des articles au nom de l'utilisateur.", True),
        ]

    @property
    def operations(self) -> list[OperationSpec]:
        return [
            OperationSpec("get_me", "Profil Medium autorisé.", scope="basicProfile"),
            OperationSpec(
                "list_publications",
                "Publications de l'auteur.",
                scope="listPublications",
            ),
            OperationSpec(
                "create_post",
                "Créer un article (brouillon, publié ou non listé).",
                scope="publishPost",
                write=True,
            ),
        ]

    def _headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def exchange_code(
        self, http: HttpLike, creds: ClientCredentials, code: str, redirect_uri: str
    ) -> TokenBundle:
        response = await http.post(
            self.token_url,
            data={
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        data = decode_token_response(response, "Medium")
        if not data.get("access_token"):
            raise ConnectionError(
                f"Medium OAuth exchange failed: {data.get('error_description') or data!r}"
            )
        return TokenBundle(
            access_token=str(data["access_token"]),
            # Stocké si Medium en émet un — AUCUN endpoint de refresh documenté
            # pour l'utiliser (voir docstring, point 8).
            refresh_token=data.get("refresh_token"),
            expires_at=epoch_in(data.get("expires_in")),
            granted_scopes=self.parse_granted_scopes(data.get("scope")),
            token_type="Bearer",
        )

    async def test_connection(self, http: HttpLike, tokens: TokenBundle) -> dict[str, Any]:
        data = await self._get_me(http, tokens.access_token)
        return self.clean_account(
            id=data.get("id"),
            username=data.get("username"),
            name=data.get("name"),
        )

    async def _get_me(self, http: HttpLike, access_token: str) -> dict[str, Any]:
        response = await http.get(f"{_API_BASE}/me", headers=self._headers(access_token))
        self.raise_if_http_error(response.status_code, "Medium", response.text)
        return (response.json() or {}).get("data") or {}

    # ── Opérations (API officielle v1) ────────────────────────────────────

    async def op_get_me(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._get_me(http, ctx["access_token"])
        return self.clean_account(
            id=data.get("id"),
            username=data.get("username"),
            name=data.get("name"),
            url=data.get("url"),
        )

    async def op_list_publications(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        me = await self._get_me(http, ctx["access_token"])
        author_id = me.get("id")
        if not author_id:
            raise ConnectionError("Medium: cannot resolve author id from /me")
        response = await http.get(
            f"{_API_BASE}/users/{author_id}/publications",
            headers=self._headers(ctx["access_token"]),
        )
        self.raise_if_http_error(response.status_code, "Medium", response.text)
        return [
            {"id": p.get("id"), "name": p.get("name"), "url": p.get("url")}
            for p in ((response.json() or {}).get("data") or [])
        ]

    async def op_create_post(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        title = str(params.get("title") or "").strip()
        content = str(params.get("content") or "").strip()
        if not title or not content:
            raise ConnectionError("Medium create_post requires 'title' and 'content'")
        content_format = str(params.get("content_format", "html"))
        if content_format not in ("html", "markdown"):
            raise ConnectionError("content_format must be 'html' or 'markdown'")
        publish_status = str(params.get("publish_status", "draft"))
        if publish_status not in _PUBLISH_STATUSES:
            raise ConnectionError(f"publish_status must be one of {', '.join(_PUBLISH_STATUSES)}")
        me = await self._get_me(http, ctx["access_token"])
        author_id = me.get("id")
        if not author_id:
            raise ConnectionError("Medium: cannot resolve author id from /me")
        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "contentFormat": content_format,
            "publishStatus": publish_status,
        }
        tags = params.get("tags")
        if tags:
            payload["tags"] = [str(t) for t in tags][:5]  # limite officielle
        if params.get("canonical_url"):
            payload["canonicalUrl"] = str(params["canonical_url"])
        response = await http.post(
            f"{_API_BASE}/users/{author_id}/posts",
            headers=self._headers(ctx["access_token"]),
            json=payload,
        )
        self.raise_if_http_error(response.status_code, "Medium", response.text)
        data = (response.json() or {}).get("data") or {}
        return {
            "id": data.get("id"),
            "url": data.get("url"),
            "publish_status": data.get("publishStatus"),
        }
