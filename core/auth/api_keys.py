"""Core-owned API key management.

ETHAN Core owns API keys.  The WebUI only renders the key list and sends
creation/revocation/rotation actions through the API.

Capacités réelles (implémentées ici) :
  - création avec expiration optionnelle (`expires_at`, ISO-8601) ;
  - validation avec enforcement des scopes (`require_scopes`) et expiration ;
  - rotation (`rotate_key` = révocation + recréation avec mêmes métadonnées) ;
  - révocation soft (`active=False` + `revoked_at`).

Règle « secret once » : le plaintext n'est retourné que par create_key/rotate_key ;
seul le SHA-256 hash est stocké — jamais récupérable ensuite.

"

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


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _is_expired(record: dict) -> bool:
    """Fail-closed : un expires_at mal formé est traité comme expiré."""
    expires_at = record.get("expires_at")
    if not expires_at:
        return False
    try:
        exp = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        now = datetime.utcnow()
        if exp.tzinfo is not None:
            now = now.replace(tzinfo=exp.tzinfo)
        return now > exp
    except ValueError:
        return True  # mal formé → refus


class APIKeyManager:
    """Own API key issuance, validation, rotation and revocation."""

    _DOMAIN = "api-keys"

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    async def create_key(
        self,
        user_id: str,
        name: str = "default",
        scopes: list[str] | None = None,
        expires_at: str | None = None,
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
            "created_at": _now_iso(),
            "revoked_at": None,
            "expires_at": expires_at or None,
        }
        await self._store.save(self._DOMAIN, record["id"], record)
        return {**record, "key": raw_key}

    async def validate_key(
        self, raw_key: str, require_scopes: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Valide une clé : active, non expirée, scopes requis couverts."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        for key in await self._store.list(self._DOMAIN):
            if key.get("key_hash") != key_hash:
                continue
            if not key.get("active"):
                return None
            if _is_expired(key):
                return None
            if require_scopes:
                allowed = set(key.get("scopes") or [])
                if not allowed.issuperset(require_scopes):
                    return None
            return key
        return None

    async def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key (soft-revoke.")"""
        key = await self._store.get(self._DOMAIN, key_id)
        if key is None:
            return False
        key["active"] = False
        key["revoked_at"] = _now_iso()
        await self._store.save(self._DOMAIN, key_id, key)
        return True

    async def rotate_key(self, key_id: str) -> dict[str, Any] | None:
        """Rotation = révocation + recréation (mêmes métadonnées.



        Retourne la NOUVELLE clé avec son plaintext (:une seule fois:).


        Retourne None si la clé n'existe pas ou n'est pas active.`


        """
        key = await self._store.get(self._DOMAIN, key_id)
        if key is None or not key.get("active"):
            return None
        # Révocation de l'ancienne
        key["active"] = False
        key["revoked_at"] = _now_iso()
        await self._store.save(self._DOMAIN, key_id, key)
        # Recréation avec mêmes métadonnées
        return await self.create_key(
            user_id=key.get("user_id", ""),
            name=key.get("name", "default"),
            scopes=key.get("scopes"),
            expires_at=key.get("expires_at"),
        )

    async def list_keys(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List API keys, optionally for one user."""
        keys = await self._store.list(self._DOMAIN)
        if user_id is not None:
            keys = [k for k in keys if k.get("user_id") == user_id]
        return keys