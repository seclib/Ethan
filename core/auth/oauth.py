"""Core-owned OAuth support — Google, GitHub, Microsoft, etc.

ETHAN Core owns OAuth configuration and token exchange.  The WebUI only
renders the login buttons and redirects through the API.
"""

from __future__ import annotations

import logging
from typing import Any

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class OAuthManager:
    """Own OAuth provider configuration and token exchange."""

    _DOMAIN = "oauth-providers"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def register_provider(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        userinfo_url: str,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Register an OAuth provider."""
        provider = {
            "id": name,
            "name": name,
            "client_id": client_id,
            "client_secret": client_secret,
            "authorize_url": authorize_url,
            "token_url": token_url,
            "userinfo_url": userinfo_url,
            "scopes": list(scopes or ["openid", "email", "profile"]),
            "enabled": True,
        }
        await self._store.save(self._DOMAIN, name, provider)
        return provider

    async def list_providers(self) -> list[dict[str, Any]]:
        """List registered OAuth providers."""
        return await self._store.list(self._DOMAIN)

    async def get_provider(self, name: str) -> dict[str, Any] | None:
        """Retrieve an OAuth provider by name."""
        return await self._store.get(self._DOMAIN, name)

    async def disable_provider(self, name: str) -> dict[str, Any] | None:
        """Disable an OAuth provider."""
        provider = await self.get_provider(name)
        if provider is None:
            return None
        provider["enabled"] = False
        await self._store.save(self._DOMAIN, name, provider)
        return provider