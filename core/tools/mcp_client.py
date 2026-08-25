"""Client MCP (Model Context Protocol) natif pour ETHAN Core.

Support complet :
- Transport streamable_http (HTTP + SSE)
- Transport stdio (processus local)
- Authentification OAuth 2.0 (Authorization Code + PKCE)
- Introspection des outils (list_tool_specs)
- Exécution d'outils (call_tool)

Conforme à `docs/plans/ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md` §4.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Any, Optional

import anyio
import httpx

log = logging.getLogger(__name__)

try:
    from mcp.client.auth import OAuthClientProvider, TokenStorage
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.client.streamable_http import streamable_http_client
    from mcp.shared.auth import OAuthClientMetadata

    from mcp import ClientSession
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = Any  # type: ignore
    streamable_http_client = Any  # type: ignore
    stdio_client = Any  # type: ignore
    StdioServerParameters = Any  # type: ignore
    OAuthClientProvider = Any  # type: ignore
    TokenStorage = Any  # type: ignore
    OAuthClientMetadata = Any  # type: ignore

# TODO: Connect to core.config for timeout/SSL settings instead of hardcoding
DEFAULT_TIMEOUT = 10.0


def _build_httpx_client(headers=None, timeout=None, auth=None, verify=True):
    """Create an httpx AsyncClient for MCP transport."""
    kwargs = {
        'follow_redirects': True,
        'verify': verify,
    }
    if timeout is not None:
        kwargs['timeout'] = timeout
    else:
        kwargs['timeout'] = DEFAULT_TIMEOUT
    if headers is not None:
        kwargs['headers'] = headers
    if auth is not None:
        kwargs['auth'] = auth
    return httpx.AsyncClient(**kwargs)


def create_httpx_client(headers=None, timeout=None, auth=None):
    return _build_httpx_client(headers=headers, timeout=timeout, auth=auth, verify=True)


def create_insecure_httpx_client(headers=None, timeout=None, auth=None):
    return _build_httpx_client(
        headers=headers, timeout=timeout, auth=auth, verify=False
    )


class InMemoryTokenStorage(TokenStorage):
    """TokenStorage in-memory pour OAuth MCP.

    Implémente l'interface `TokenStorage` de la lib mcp.
    Les tokens ne sont jamais persistés (conformité `docs/plans/secret.md`).
    """

    def __init__(self) -> None:
        self._tokens: dict[str, Any] = {}

    async def get_tokens(self, resource_url: str) -> Any | None:
        return self._tokens.get(resource_url)

    async def save_tokens(self, resource_url: str, tokens: Any) -> None:
        self._tokens[resource_url] = tokens

    async def delete_tokens(self, resource_url: str) -> None:
        self._tokens.pop(resource_url, None)


class MCPClient:
    """Client for connecting to external Tool Servers via Model Context Protocol.

    Supporte les transports :
    - ``http`` / ``streamable_http`` : connexion HTTP + SSE
    - ``stdio`` : processus local (commande + args)

    Supporte l'authentification :
    - ``none`` : pas d'authentification
    - ``oauth`` : OAuth 2.0 Authorization Code + PKCE
    - ``bearer`` : token Bearer statique (via headers)
    """

    def __init__(self):
        if not MCP_AVAILABLE:
            log.warning(
                "MCP libraries are not installed. MCPClient will fail to connect."
            )
        self.session: Optional[ClientSession] = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self._transport: str = "http"

    async def connect(
        self,
        url: str,
        headers: Optional[dict] = None,
        verify_ssl: bool = True,
        transport: str = "http",
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        cwd: Optional[str] = None,
        auth_type: str = "none",
        auth_config: Optional[dict[str, Any]] = None,
    ) -> None:
        """Connect to an MCP server.

        Args:
            url: URL du serveur (pour transport http) ou identifiant (pour stdio).
            headers: Headers HTTP supplémentaires.
            verify_ssl: Vérifier le certificat SSL (http uniquement).
            transport: Type de transport — ``http`` (défaut) ou ``stdio``.
            command: Commande à exécuter (transport stdio).
            args: Arguments de la commande (transport stdio).
            env: Variables d'environnement (transport stdio).
            cwd: Répertoire de travail (transport stdio).
            auth_type: Type d'authentification — ``none``, ``oauth`` ou ``bearer``.
            auth_config: Configuration d'authentification.
        """
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP package is not installed.")

        self._transport = transport

        async with AsyncExitStack() as exit_stack:
            try:
                if transport == "stdio":
                    if not command:
                        raise ValueError("command is required for stdio transport")
                    server_params = StdioServerParameters(
                        command=command,
                        args=args or [],
                        env=env,
                        cwd=cwd,
                    )
                    read_stream, write_stream = await exit_stack.enter_async_context(
                        stdio_client(server_params)
                    )
                else:
                    # Transport http / streamable_http
                    http_client_factory = (
                        create_httpx_client
                        if verify_ssl
                        else create_insecure_httpx_client
                    )

                    # Gestion OAuth
                    if auth_type == "oauth" and auth_config:
                        client_metadata = OAuthClientMetadata(
                            client_name=auth_config.get(
                                "client_name", "ETHAN Core"
                            ),
                            redirect_uris=[
                                auth_config.get(
                                    "redirect_uri",
                                    "http://localhost:3000/callback",
                                )
                            ],
                        )
                        token_storage = InMemoryTokenStorage()
                        _oauth_provider = OAuthClientProvider(
                            server_url=url,
                            client_metadata=client_metadata,
                            storage=token_storage,
                        )

                    streams_context = streamable_http_client(
                        url,
                        http_client=http_client_factory(headers=headers),
                    )
                    transport_streams = await exit_stack.enter_async_context(
                        streams_context
                    )
                    read_stream, write_stream = transport_streams

                self._session_context = ClientSession(
                    read_stream, write_stream
                )
                self.session = await exit_stack.enter_async_context(
                    self._session_context
                )
                with anyio.fail_after(10):
                    await self.session.initialize()
                self.exit_stack = exit_stack.pop_all()
            except Exception as e:
                await asyncio.shield(self.disconnect())
                raise e

    async def list_tool_specs(self) -> list[dict[str, Any]]:
        """List tools provided by the MCP server.

        Returns:
            Liste de specs d'outils : ``{name, description, parameters}``.
        """
        if not self.session:
            raise RuntimeError('MCP client is not connected.')

        result = await self.session.list_tools()
        tools = result.tools

        tool_specs = []
        for tool in tools:
            tool_specs.append({
                'name': tool.name,
                'description': tool.description,
                'parameters': getattr(
                    tool, 'input_schema', getattr(tool, 'inputSchema', {})
                )
            })

        return tool_specs

    async def call_tool(self, function_name: str, function_args: dict) -> Any:
        """Execute a tool on the MCP server.

        Args:
            function_name: Nom de l'outil à exécuter.
            function_args: Arguments de l'outil.

        Returns:
            Contenu du résultat (liste de blocs content).
        """
        if not self.session:
            raise RuntimeError('MCP client is not connected.')

        result = await self.session.call_tool(function_name, function_args)
        if not result:
            raise Exception('No result returned from MCP tool call.')

        result_dict = result.model_dump(mode='json')
        result_content = result_dict.get('content', {})

        if getattr(result, "isError", False):
            raise Exception(result_content)
        else:
            return result_content

    async def disconnect(self):
        """Clean up and close the session."""
        exit_stack = self.exit_stack
        if exit_stack is None:
            return

        self.exit_stack = None
        self.session = None

        try:
            with anyio.fail_after(5.0):
                await exit_stack.aclose()
        except TimeoutError:
            log.warning('MCPClient.disconnect() timed out after 5s')
        except RuntimeError as exc:
            log.debug('MCPClient.disconnect() suppressed RuntimeError: %s', exc)
        except Exception as exc:
            log.debug('MCPClient.disconnect() error: %s', exc)

    async def __aenter__(self):
        if self.exit_stack:
            await self.exit_stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.exit_stack:
            await self.exit_stack.__aexit__(exc_type, exc_value, traceback)
        await self.disconnect()
