"""Core-owned LDAP support — Active Directory integration.

ETHAN Core owns LDAP configuration and authentication.  The WebUI only
renders the login form and sends credentials through the API.
"""

from __future__ import annotations

import logging
from typing import Any

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class LDAPManager:
    """Own LDAP server configuration and user authentication."""

    _DOMAIN = "ldap-config"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def configure(
        self,
        server_url: str,
        bind_dn: str,
        bind_password: str,
        user_search_base: str,
        user_search_filter: str = "(uid={username})",
        tls_enabled: bool = False,
    ) -> dict[str, Any]:
        """Configure the LDAP connection."""
        config = {
            "server_url": server_url,
            "bind_dn": bind_dn,
            "bind_password": bind_password,
            "user_search_base": user_search_base,
            "user_search_filter": user_search_filter,
            "tls_enabled": tls_enabled,
            "enabled": True,
        }
        await self._store.save(self._DOMAIN, "default", config)
        return config

    async def get_config(self) -> dict[str, Any] | None:
        """Retrieve the current LDAP configuration."""
        return await self._store.get(self._DOMAIN, "default")

    async def is_enabled(self) -> bool:
        """Return whether LDAP authentication is enabled."""
        config = await self.get_config()
        return bool(config and config.get("enabled"))