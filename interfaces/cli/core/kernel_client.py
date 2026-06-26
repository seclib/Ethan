"""Kernel Client — Client HTTP pour communiquer avec le Kernel Go.

Permet au CLI et aux autres interfaces de fonctionner en mode distribué.
Fallback automatique vers le mode standalone si le Kernel est inaccessible.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from core.config.loader import ConfigLoader

logger = logging.getLogger(__name__)


class KernelClient:
    """Client HTTP pour le Kernel ETHAN.

    En mode distribué : communique avec le Kernel Go via HTTP.
    En mode standalone : utilise InMemoryBus directement.
    """

    def __init__(self, config=None):
        self._config = config or ConfigLoader().load()
        self._base_url = "http://localhost:8080"
        self._client = httpx.AsyncClient(timeout=30.0)
        self._connected = False

    async def connect(self) -> bool:
        """Tente de se connecter au Kernel.

        Returns:
            True si connecté, False sinon (mode standalone)
        """
        try:
            response = await self._client.get(f"{self._base_url}/health")
            if response.status_code == 200:
                self._connected = True
                logger.info("Connected to ETHAN Kernel")
                return True
        except Exception as e:
            logger.warning(f"Cannot connect to Kernel: {e}")

        self._connected = False
        logger.info("Running in standalone mode")
        return False

    async def close(self) -> None:
        """Ferme le client."""
        await self._client.aclose()

    async def chat(self, text: str, session_id: str = "default", user_id: str = "anonymous") -> dict[str, Any]:
        """Envoie un message au Kernel.

        Args:
            text: Message utilisateur
            session_id: ID de session
            user_id: ID utilisateur

        Returns:
            Réponse du Kernel
        """
        if not self._connected:
            raise RuntimeError("Not connected to Kernel")

        response = await self._client.post(
            f"{self._base_url}/api/v1/chat",
            json={
                "text": text,
                "session_id": session_id,
                "user_id": user_id,
            },
        )

        response.raise_for_status()
        return response.json()

    async def command(self, command: str, args: list[str] = None, meta: dict[str, Any] = None) -> dict[str, Any]:
        """Exécute une commande via le Kernel.

        Args:
            command: Nom de la commande
            args: Arguments
            meta: Métadonnées

        Returns:
            Résultat de la commande
        """
        if not self._connected:
            raise RuntimeError("Not connected to Kernel")

        response = await self._client.post(
            f"{self._base_url}/api/v1/command",
            json={
                "command": command,
                "args": args or [],
                "meta": meta or {},
            },
        )

        response.raise_for_status()
        return response.json()

    async def status(self) -> dict[str, Any]:
        """Récupère le statut du système.

        Returns:
            Statut du Kernel
        """
        if not self._connected:
            raise RuntimeError("Not connected to Kernel")

        response = await self._client.get(f"{self._base_url}/api/v1/status")
        response.raise_for_status()
        return response.json()

    @property
    def is_connected(self) -> bool:
        """Indique si le client est connecté au Kernel."""
        return self._connected