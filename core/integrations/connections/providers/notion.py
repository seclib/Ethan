"""Connecteur Notion — OAuth2 (authorization code + HTTP Basic).

Audit des 8 points :
1. Auth : OAuth2 authorization-code, échange en HTTP Basic (officiel).
2. Scopes : Notion n'en définit PAS — l'utilisateur choisit les pages/bases
   partagées AU MOMENT du consentement. La granularité est portée par cette
   sélection, pas par une liste de scopes (documenté, pas un oubli).
3. Credentials : client_id/client_secret de l'intégration, via SecretManager.
4. Opérations (API officielle v1, header ``Notion-Version`` requis) :
   ``search``, ``retrieve_page``, ``create_page`` (écriture),
   ``update_page`` (écriture), ``query_database``. Limites : accès limité
   au contenu partagé à l'intégration ; fichiers stockés hors Notion non
   téléchargeables ; rate limit 3 req/s.
5. Test : ``GET /users/me`` (bot) — nom du bot + workspace, public.
6. Révocation : Notion n'expose PAS d'API de révocation — l'utilisateur
   révoque l'accès depuis Notion (Settings → Connections) ; la déconnexion
   ETHAN purge les tokens locaux (contrat de base : ``revoke → False``).
7. Erreurs : statut HTTP >= 400 → ``ConnectionError`` avec le corps du
   service (les erreurs Notion portent un ``code`` JSON, conservé).
8. Expiration : pas de refresh token — access token long-lived ;
   ``refresh_tokens`` suit le contrat de base (``None``) → Reconnecter.
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
from core.integrations.connections.oauth import basic_auth_header, decode_token_response

_API_BASE = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"


class NotionProvider(ConnectionProvider):
    id = "notion"
    label = "Notion"
    description = (
        "Espace de travail Notion : pages et bases de données sélectionnées "
        "par l'utilisateur lors du consentement."
    )
    authorize_url = "https://api.notion.com/v1/oauth/authorize"
    token_url = "https://api.notion.com/v1/oauth/token"

    @property
    def scopes(self) -> list[ScopeSpec]:
        # Notion ne définit pas de scopes OAuth : la sélection de contenu
        # se fait dans l'écran de consentement du service.
        return []

    @property
    def operations(self) -> list[OperationSpec]:
        # Pas de scope par opération (pas de scopes chez Notion) : la
        # granularité réelle = contenu partagé à l'intégration par l'utilisateur.
        return [
            OperationSpec("search", "Rechercher pages/bases partagées."),
            OperationSpec("retrieve_page", "Lire une page (propriétés)."),
            OperationSpec("create_page", "Créer une page.", write=True),
            OperationSpec("update_page", "Mettre à jour une page.", write=True),
            OperationSpec("query_database", "Interroger une base de données."),
        ]

    def _headers(self, access_token: str | None = None) -> dict[str, str]:
        headers = {"Notion-Version": _NOTION_VERSION}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def exchange_code(
        self, http: HttpLike, creds: ClientCredentials, code: str, redirect_uri: str
    ) -> TokenBundle:
        response = await http.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={
                "Authorization": basic_auth_header(creds.client_id, creds.client_secret),
            },
        )
        data = decode_token_response(response, "Notion")
        if not data.get("access_token"):
            raise ConnectionError(
                f"Notion OAuth exchange failed: {data.get('error_description') or data!r}"
            )
        bot = data.get("bot") or {}
        return TokenBundle(
            access_token=str(data["access_token"]),
            granted_scopes=self.parse_granted_scopes(data.get("scope")),
            token_type="Bearer",
            account={
                "workspace_name": bot.get("workspace_name"),
                "bot_name": data.get("name"),
            },
        )

    async def test_connection(self, http: HttpLike, tokens: TokenBundle) -> dict[str, Any]:
        response = await http.get(
            f"{_API_BASE}/users/me", headers=self._headers(tokens.access_token)
        )
        self.raise_if_http_error(response.status_code, "Notion", response.text)
        data = response.json()
        bot = data.get("bot") or {}
        return self.clean_account(
            name=data.get("name"),
            workspace_name=bot.get("workspace_name"),
        )

    # ── Opérations (API officielle v1) ────────────────────────────────────

    async def op_search(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"page_size": max(1, min(int(params.get("limit", 20)), 100))}
        if params.get("query"):
            payload["query"] = str(params["query"])
        response = await http.post(
            f"{_API_BASE}/search",
            headers=self._headers(ctx["access_token"]),
            json=payload,
        )
        self.raise_if_http_error(response.status_code, "Notion", response.text)
        return [
            {
                "id": r.get("id"),
                "type": r.get("object"),
                "title": self._title_of(r),
                "url": r.get("url"),
            }
            for r in ((response.json() or {}).get("results") or [])
        ]

    async def op_retrieve_page(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        page_id = str(params.get("page_id") or "")
        if not page_id:
            raise ConnectionError("retrieve_page requires 'page_id'")
        response = await http.get(
            f"{_API_BASE}/pages/{page_id}",
            headers=self._headers(ctx["access_token"]),
        )
        self.raise_if_http_error(response.status_code, "Notion", response.text)
        page = response.json()
        return {
            "id": page.get("id"),
            "title": self._title_of(page),
            "url": page.get("url"),
            "archived": bool(page.get("archived")),
        }

    async def op_create_page(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        parent = params.get("parent")
        properties = params.get("properties")
        if not isinstance(parent, dict) or not parent:
            raise ConnectionError(
                "create_page requires 'parent' ({'page_id': ...} or {'database_id': ...})"
            )
        if not isinstance(properties, dict) or not properties:
            raise ConnectionError("create_page requires 'properties' (Notion schema)")
        payload: dict[str, Any] = {"parent": parent, "properties": properties}
        if isinstance(params.get("children"), list):
            payload["children"] = params["children"]
        response = await http.post(
            f"{_API_BASE}/pages",
            headers=self._headers(ctx["access_token"]),
            json=payload,
        )
        self.raise_if_http_error(response.status_code, "Notion", response.text)
        page = response.json()
        return {"id": page.get("id"), "url": page.get("url")}

    async def op_update_page(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        page_id = str(params.get("page_id") or "")
        properties = params.get("properties")
        if not page_id or not isinstance(properties, dict):
            raise ConnectionError("update_page requires 'page_id' and 'properties'")
        payload: dict[str, Any] = {"properties": properties}
        if isinstance(params.get("archived"), bool):
            payload["archived"] = params["archived"]
        response = await http.patch(
            f"{_API_BASE}/pages/{page_id}",
            headers=self._headers(ctx["access_token"]),
            json=payload,
        )
        self.raise_if_http_error(response.status_code, "Notion", response.text)
        page = response.json()
        return {
            "id": page.get("id"),
            "url": page.get("url"),
            "archived": page.get("archived"),
        }

    async def op_query_database(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        database_id = str(params.get("database_id") or "")
        if not database_id:
            raise ConnectionError("query_database requires 'database_id'")
        payload: dict[str, Any] = {"page_size": max(1, min(int(params.get("limit", 20)), 100))}
        if isinstance(params.get("filter"), dict):
            payload["filter"] = params["filter"]
        response = await http.post(
            f"{_API_BASE}/databases/{database_id}/query",
            headers=self._headers(ctx["access_token"]),
            json=payload,
        )
        self.raise_if_http_error(response.status_code, "Notion", response.text)
        return [
            {"id": r.get("id"), "title": self._title_of(r), "url": r.get("url")}
            for r in ((response.json() or {}).get("results") or [])
        ]

    @staticmethod
    def _title_of(result: dict[str, Any]) -> str | None:
        props = result.get("properties") or {}
        for value in props.values():
            if isinstance(value, dict) and value.get("type") == "title":
                parts = value.get("title") or []
                text = "".join(str(p.get("plain_text") or "") for p in parts)
                if text:
                    return text
        return result.get("title") if isinstance(result.get("title"), str) else None
