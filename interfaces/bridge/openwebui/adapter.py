"""Adaptateur API Open WebUI → ETHAN.

Traduit les endpoints Open WebUI vers les endpoints ETHAN Core v1.
Chaque fonction est une passerelle HTTP mince : elle reçoit une requête
Open WebUI, la traduit, appelle ETHAN Core, et retourne la réponse.
"""

from __future__ import annotations

import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EthanAdapter:
    """Client vers l'API Gateway ETHAN (http://api:8000 par défaut)."""

    def __init__(self, base_url: str = "http://api:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ── Modèles (équivalent Open WebUI /api/models) ── #

    async def list_models(self) -> list[dict[str, Any]]:
        """GET /v1/providers/{id}/models → agrégation des modèles ETHAN."""
        client = await self._client()
        # On agrège les modèles depuis tous les providers
        resp = await client.get(f"{self.base_url}/v1/providers")
        resp.raise_for_status()
        providers = resp.json()
        models: list[dict[str, Any]] = []
        for p in providers:
            p_id = p.get("id") or p.get("name")
            if not p_id:
                continue
            try:
                mresp = await client.get(f"{self.base_url}/v1/providers/{p_id}/models")
                mresp.raise_for_status()
                for m in mresp.json():
                    models.append(
                        {
                            "id": m.get("id", m.get("name")),
                            "name": m.get("name", m.get("id")),
                            "provider": p_id,
                            **m,
                        }
                    )
            except Exception as exc:  # noqa: BLE001 — un provider indisponible ne bloque pas
                logger.warning("Impossible de lister les modèles de %s: %s", p_id, exc)
        return models

    # ── Skills (équivalent Open WebUI /api/skills) ── #

    async def list_skills(self) -> list[dict[str, Any]]:
        """GET /v1/skills → liste des skills ETHAN."""
        client = await self._client()
        resp = await client.get(f"{self.base_url}/v1/skills")
        resp.raise_for_status()
        return resp.json()

    # ── Plugins (équivalent Open WebUI /api/plugins) ── #

    async def list_plugins(self) -> list[dict[str, Any]]:
        """GET /v1/plugins → catalogue plugins ETHAN."""
        client = await self._client()
        resp = await client.get(f"{self.base_url}/v1/plugins")
        resp.raise_for_status()
        return resp.json()

    # ── Connaissance (équivalent Open WebUI /api/knowledge) ── #

    async def list_knowledge(self) -> list[dict[str, Any]]:
        """GET /v1/knowledge → nodes connaissance ETHAN."""
        client = await self._client()
        resp = await client.get(f"{self.base_url}/v1/knowledge")
        resp.raise_for_status()
        return resp.json()

    async def search_knowledge(self, q: str) -> list[dict[str, Any]]:
        """GET /v1/knowledge/search?q=… → recherche connaissance."""
        client = await self._client()
        resp = await client.get(f"{self.base_url}/v1/knowledge/search", params={"q": q})
        resp.raise_for_status()
        return resp.json()