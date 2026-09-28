"""Connecteur GitHub — OAuth2 web application flow.

Audit des 8 points :
1. Auth : OAuth2 authorization-code (token_url GitHub, réponse JSON via
   ``Accept: application/json``).
2. Scopes : ``repo`` (dépôts, issues, PR — sensible), ``read:user``
   (profil public), ``user:email`` (email primaire). Moindre privilège :
   pas de scope admin ni workflow.
3. Credentials : client_id/client_secret de l'app OAuth ETHAN, résolus
   depuis le ``SecretManager`` (env ``ETHAN_CONN_GITHUB_*`` ou Vault).
4. Opérations (officielles, REST v3) : ``get_user``, ``list_repos``,
   ``list_issues`` — lecture seule ; l'écriture (issues, PR) viendra avec
   des opérations dédiées si le besoin est confirmé.
5. Test : ``GET /user`` avec le token — identité publique seule.
6. Révocation : API réelle « Delete a token » —
   ``DELETE /applications/{client_id}/token`` (HTTP Basic
   client_id:client_secret). La déconnexion ETHAN révoque DONC le token
   côté GitHub avant la purge locale.
7. Erreurs : statut HTTP >= 400 → ``ConnectionError`` avec le corps du
   service (jamais avalé) ; payload OAuth invalide → erreur explicite.
8. Expiration : GitHub n'émet PAS de refresh token et ne documente pas de
   TTL fixe → ``refresh_tokens`` suit le contrat de base (``None``) ; en
   cas de token révoqué/expiré (401), l'utilisateur utilise Reconnecter.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

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

_API_BASE = "https://api.github.com"


class GitHubProvider(ConnectionProvider):
    id = "github"
    label = "GitHub"
    description = "Dépôts, issues, pull requests et profil GitHub de l'utilisateur."
    authorize_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"

    @property
    def scopes(self) -> list[ScopeSpec]:
        return [
            ScopeSpec(
                "repo",
                "Accès aux dépôts (code, issues, PR) — sensibilité élevée.",
                True,
            ),
            ScopeSpec("read:user", "Lire le profil public GitHub.", False),
            ScopeSpec("user:email", "Lire l'adresse email primaire.", False),
        ]

    @property
    def operations(self) -> list[OperationSpec]:
        return [
            OperationSpec("get_user", "Profil GitHub autorisé.", scope="read:user"),
            OperationSpec("list_repos", "Dépôts accessibles à l'utilisateur.", scope="repo"),
            OperationSpec("list_issues", "Issues visibles par l'utilisateur.", scope="repo"),
        ]

    def _api_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

    async def exchange_code(
        self, http: HttpLike, creds: ClientCredentials, code: str, redirect_uri: str
    ) -> TokenBundle:
        # GitHub répond en JSON uniquement avec ``Accept: application/json``.
        response = await http.post(
            self.token_url,
            data={
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        data = decode_token_response(response, "GitHub")
        if not data.get("access_token"):
            raise ConnectionError(
                f"GitHub OAuth exchange failed: {data.get('error_description') or data!r}"
            )
        return TokenBundle(
            access_token=str(data["access_token"]),
            granted_scopes=self.parse_granted_scopes(data.get("scope")),
            token_type=str(data.get("token_type") or "bearer"),
        )

    async def test_connection(self, http: HttpLike, tokens: TokenBundle) -> dict[str, Any]:
        response = await http.get(
            f"{_API_BASE}/user", headers=self._api_headers(tokens.access_token)
        )
        self.raise_if_http_error(response.status_code, "GitHub", response.text)
        user = response.json()
        return self.clean_account(
            login=user.get("login"),
            name=user.get("name"),
            email=user.get("email"),
        )

    async def revoke(self, http: HttpLike, creds: ClientCredentials, tokens: TokenBundle) -> bool:
        """Révocation RÉELLE (API OAuth GitHub « Delete a token ») : le token
        devient inutilisable côté GitHub, pas seulement localement."""
        response = await http.delete(
            f"{_API_BASE}/applications/{creds.client_id}/token",
            headers={
                "Authorization": basic_auth_header(creds.client_id, creds.client_secret),
                "Accept": "application/vnd.github+json",
            },
            json={"access_token": tokens.access_token},
        )
        return response.status_code in (200, 204)

    # ── Opérations (REST v3 officielle — lecture) ─────────────────────────

    async def op_get_user(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.test_connection(http, TokenBundle(access_token=ctx["access_token"]))

    async def op_list_repos(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(params.get("limit", 20)), 100))
        response = await http.get(
            f"{_API_BASE}/user/repos?{urlencode({'per_page': limit, 'sort': 'updated'})}",
            headers=self._api_headers(ctx["access_token"]),
        )
        self.raise_if_http_error(response.status_code, "GitHub", response.text)
        return [
            {
                "full_name": r.get("full_name"),
                "private": bool(r.get("private")),
                "html_url": r.get("html_url"),
                "updated_at": r.get("updated_at"),
            }
            for r in (response.json() or [])
        ]

    async def op_list_issues(
        self, http: HttpLike, ctx: dict[str, Any], params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(params.get("limit", 20)), 100))
        state = str(params.get("state", "open"))
        if state not in ("open", "closed", "all"):
            raise ConnectionError(f"Invalid issue state: {state!r} (open|closed|all)")
        response = await http.get(
            f"{_API_BASE}/issues?"
            f"{urlencode({'per_page': limit, 'state': state, 'sort': 'updated'})}",
            headers=self._api_headers(ctx["access_token"]),
        )
        self.raise_if_http_error(response.status_code, "GitHub", response.text)
        return [
            {
                "repository": str(i.get("repository_url") or "").rsplit("/", 2)[-2:],
                "number": i.get("number"),
                "title": i.get("title"),
                "state": i.get("state"),
                "html_url": i.get("html_url"),
            }
            for i in (response.json() or [])
            # ``GET /issues`` renvoie aussi les PR — filtrées (REST GitHub).
            if "pull_request" not in (i or {})
        ]
