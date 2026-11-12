"""Synchronisation des utilisateurs Open WebUI vers ETHAN Core.

Open WebUI possède sa propre base d'utilisateurs (SQLite). Ce bridge
permet de créer les utilisateurs correspondants dans ETHAN Core
(CoreWebUIStore / users) pour que les permissions ETHAN s'appliquent.

Aucune donnée sensible (mot de passe, token) n'est transférée.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def sync_user_to_ethan(
    owui_user: dict[str, Any],
    ethan_api_base: str = "http://api:8000",
) -> dict[str, Any] | None:
    """Crée ou met à jour un utilisateur ETHAN depuis un utilisateur Open WebUI.

    Seuls les champs non sensibles sont transférés : id, email, name, role.
    """
    import httpx

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{ethan_api_base}/v1/users",
                json={
                    "email": owui_user.get("email"),
                    "name": owui_user.get("name") or owui_user.get("email"),
                    "role": owui_user.get("role", "user"),
                    "source": "openwebui",
                    "source_id": str(owui_user.get("id")),
                },
            )
            if resp.status_code in (200, 201, 409):  # 409 = déjà existant
                return resp.json() if resp.status_code != 409 else None
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001 — sync non bloquant
            logger.warning("Impossible de synchroniser l'utilisateur %s vers ETHAN: %s",
                          owui_user.get("email"), exc)
            return None