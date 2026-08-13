"""Core-owned SCIM provisioning — automated user/group provisioning.

ETHAN Core owns SCIM.  The WebUI only renders the SCIM status and sends
configuration actions through the API.
"""

from __future__ import annotations

import logging
from typing import Any

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class SCIMManager:
    """Own SCIM provisioning configuration."""

    _DOMAIN = "scim-config"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def configure(
        self,
        enabled: bool,
        base_url: str = "",
        bearer_token: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Configure SCIM provisioning."""
        config = {
            "enabled": enabled,
            "base_url": base_url,
            "bearer_token": bearer_token,
            "metadata": dict(metadata or {}),
        }
        await self._store.save(self._DOMAIN, "default", config)
        return config

    async def get_config(self) -> dict[str, Any] | None:
        """Retrieve the SCIM configuration."""
        return await self._store.get(self._DOMAIN, "default")

    async def is_enabled(self) -> bool:
        """Return whether SCIM provisioning is enabled."""
        config = await self.get_config()
        return bool(config and config.get("enabled"))
