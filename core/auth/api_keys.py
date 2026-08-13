"""Core-owned API key management.

ETHAN Core owns API keys.  The WebUI only renders the key list and sends
creation/revocation actions through the API.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Own API key issuance, validation and revocation."""

    _DOMAIN = "api-keys"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def create_key(
        self,
        user_id: str,
        name: str = "default",
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Issue a new API key. Returns the plaintext key only once."""
        raw_key = f"ethan_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "name": name,
            "key_hash": key_hash,
            "scopes": list(scopes or []),
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
            "revoked_at": None,
        }
        await self._store.save(self._DOMAIN, record["id"], record)
        return {**record, "key": raw_key}

    async def validate_key(self, raw_key: str) -> dict[str, Any] | None:
        """Validate a raw API key and return its record if active."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        for key in await self._store.list(self._DOMAIN):
            if key.get("key_hash") == key_hash and key.get("active"):
                return key
        return None

    async def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        key = await self._store.get(self._DOMAIN, key_id)
        if key is None:
            return False
        key["active"] = False
        key["revoked_at"] = datetime.utcnow().isoformat()
        await self._store.save(self._DOMAIN, key_id, key)
        return True

    async def list_keys(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List API keys, optionally for one user."""
        keys = await self._store.list(self._DOMAIN)
        if user_id is not None:
            keys = [k for k in keys if k.get("user_id") == user_id]
        return keys