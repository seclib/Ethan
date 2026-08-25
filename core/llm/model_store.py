"""ModelStore — Persistance des fiches modèles personnalisées.

ETHAN Core possède un catalogue de modèles agrégé (discouvert via les
providers LLM).  Le ``ModelStore`` permet d'enregistrer des **fiches
modèles personnalisées** — des modèles non découverts automatiquement
mais configurés manuellement par l'administrateur (ex: un modèle
déployé sur un provider custom, un modèle local non listé, etc.).

Chaque fiche contient :
- ``model`` : identifiant technique transmis au provider
- ``base_model_id`` : référence au modèle découvert (ex: ``llama3.1``)
- ``params`` : paramètres de génération (temperature, max_tokens, etc.)
- ``meta`` : métadonnées affichées (icône, description, tags)
- ``is_active`` : activé pour la sélection automatique
- ``acl`` : contrôle d'accès (qui peut utiliser ce modèle)

Le store utilise ``CoreRecordStore`` (PostgreSQL + Redis cache + fallback
mémoire) — même pattern que ``SkillStore`` et ``KnowledgeCollectionManager``.
"""

from __future__ import annotations

from copy import deepcopy
import logging
from typing import Any
from uuid import uuid4

from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_MODELS = "llm_models"


class ModelStore:
    """Persistent store for custom model cards.

    Args:
        store: A shared CoreRecordStore instance (PG durable + Redis cache +
            in-memory fallback).  Created once by the API composition root.
    """

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()

    # ── CRUD ──────────────────────────────────────────────────────────

    async def list_models(self) -> list[dict[str, Any]]:
        """List all custom model cards, most recently updated first."""
        return await self._store.list(_DOMAIN_MODELS)

    async def get_model(self, model_id: str) -> dict[str, Any] | None:
        """Retrieve a custom model card by id."""
        return await self._store.get(_DOMAIN_MODELS, model_id)

    async def create_model(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a custom model card.

        Args:
            data: Must contain at least ``name``.  Optional keys:
                ``base_model_id``, ``params``, ``meta``, ``is_active``, ``acl``.

        Returns:
            The created model card (deep copy).
        """
        model_id = str(uuid4())
        now = _utc_now()
        record: dict[str, Any] = {
            "id": model_id,
            "name": data.get("name", "unnamed"),
            "model": data.get("model", data.get("base_model_id", "")),
            "base_model_id": data.get("base_model_id", ""),
            "params": dict(data.get("params", {})),
            "meta": dict(data.get("meta", {})),
            "is_active": bool(data.get("is_active", True)),
            "acl": list(data.get("acl", [])),
            "created_at": now,
            "updated_at": now,
        }
        await self._store.save(_DOMAIN_MODELS, model_id, record)
        return deepcopy(record)

    async def update_model(self, model_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a custom model card.

        Returns the updated record or ``None`` if not found.
        """
        record = await self._store.get(_DOMAIN_MODELS, model_id)
        if record is None:
            return None
        for key in ("name", "model", "base_model_id", "params", "meta", "is_active", "acl"):
            if key in data:
                record[key] = data[key]
        record["id"] = model_id
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_MODELS, model_id, record)
        return deepcopy(record)

    async def delete_model(self, model_id: str) -> bool:
        """Delete a custom model card.

        Returns ``True`` if the record existed and was deleted.
        """
        return await self._store.delete(_DOMAIN_MODELS, model_id)

    async def toggle_model(self, model_id: str) -> dict[str, Any] | None:
        """Toggle the ``is_active`` flag of a custom model card."""
        record = await self._store.get(_DOMAIN_MODELS, model_id)
        if record is None:
            return None
        record["is_active"] = not bool(record.get("is_active", True))
        record["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_MODELS, model_id, record)
        return deepcopy(record)

    # ── Search ────────────────────────────────────────────────────────

    async def search_models(self, q: str) -> list[dict[str, Any]]:
        """Search custom model cards by name, base_model_id or meta tags."""
        q_lower = q.lower()
        models = await self._store.list(_DOMAIN_MODELS)
        return [
            m
            for m in models
            if q_lower in m.get("name", "").lower()
            or q_lower in m.get("base_model_id", "").lower()
            or any(q_lower in str(tag).lower() for tag in m.get("meta", {}).get("tags", []))
        ]


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["ModelStore"]
