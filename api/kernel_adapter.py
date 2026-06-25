"""API Adapter — Adapte l'API REST vers le Kernel.

Remplace la communication NATS directe par des appels HTTP au Kernel.
Fallback vers le mode standalone si le Kernel est inaccessible.
"""

from __future__ import annotations

import logging
from typing import Any

from cli.core.kernel_client import KernelClient
from core.bus.memory import InMemoryBus
from core.types.event import Event, EventType

logger = logging.getLogger(__name__)


class APIAdapter:
    """Adaptateur pour l'API REST.

    En mode distribué : envoie les requêtes au Kernel via HTTP.
    En mode standalone : utilise InMemoryBus directement.
    """

    def __init__(self):
        self._kernel_client: KernelClient | None = None
        self._local_bus = InMemoryBus()
        self._mode = "standalone"  # "distributed" ou "standalone"

    async def init(self) -> None:
        """Initialise l'adaptateur."""
        self._kernel_client = KernelClient()
        connected = await self._kernel_client.connect()

        if connected:
            self._mode = "distributed"
            logger.info("API running in distributed mode (Kernel)")
        else:
            self._mode = "standalone"
            await self._local_bus.connect("api://local")
            logger.info("API running in standalone mode")

    async def close(self) -> None:
        """Ferme les connexions."""
        if self._kernel_client:
            await self._kernel_client.close()
        await self._local_bus.close()

    async def send_message(self, text: str, session_id: str = "default", user_id: str = "anonymous") -> dict[str, Any]:
        """Envoie un message.

        Args:
            text: Message utilisateur
            session_id: ID de session
            user_id: ID utilisateur

        Returns:
            Réponse formatée
        """
        if self._mode == "distributed":
            return await self._send_via_kernel(text, session_id, user_id)
        else:
            return await self._send_local(text, session_id, user_id)

    async def _send_via_kernel(self, text: str, session_id: str, user_id: str) -> dict[str, Any]:
        """Envoie via le Kernel (mode distribué)."""
        try:
            response = await self._kernel_client.chat(text, session_id, user_id)
            return {
                "mode": "distributed",
                "status": response.get("status", "accepted"),
                "message": response.get("message", ""),
                "response": response.get("response", ""),
            }
        except Exception as e:
            logger.error(f"Kernel request failed: {e}")
            # Fallback vers local
            return await self._send_local(text, session_id, user_id)

    async def _send_local(self, text: str, session_id: str, user_id: str) -> dict[str, Any]:
        """Envoie en local (mode standalone)."""
        # Publier l'événement
        event = Event(
            type=EventType.INTERFACE_MESSAGE,
            source="api",
            payload={
                "text": text,
                "session_id": session_id,
                "user_id": user_id,
            },
        )

        await self._local_bus.publish("ethan.interface.message", event)

        # Pour l'instant, retourner un accusé de réception
        # TODO: Implémenter le request/reply pour obtenir la vraie réponse
        return {
            "mode": "standalone",
            "status": "accepted",
            "message": "Message queued for processing",
            "response": f"Echo: {text}",  # MVP
        }

    async def execute_command(self, command: str, args: list[str] = None, meta: dict[str, Any] = None) -> dict[str, Any]:
        """Exécute une commande.

        Args:
            command: Nom de la commande
            args: Arguments
            meta: Métadonnées

        Returns:
            Résultat de la commande
        """
        if self._mode == "distributed":
            try:
                return await self._kernel_client.command(command, args, meta)
            except Exception as e:
                logger.error(f"Kernel command failed: {e}")
                return {"error": str(e)}
        else:
            # Mode local
            event = Event(
                type=EventType.INTERFACE_COMMAND,
                source="api",
                payload={
                    "command": command,
                    "args": args or [],
                    "meta": meta or {},
                },
            )

            await self._local_bus.publish("ethan.interface.command", event)

            return {
                "mode": "standalone",
                "status": "accepted",
                "command": command,
            }

    async def get_status(self) -> dict[str, Any]:
        """Récupère le statut du système.

        Returns:
            Statut formaté
        """
        if self._mode == "distributed":
            try:
                return await self._kernel_client.status()
            except Exception as e:
                logger.error(f"Failed to get status from Kernel: {e}")
                return {"error": str(e), "mode": "distributed"}
        else:
            return {
                "mode": "standalone",
                "status": "running",
                "bus": "InMemoryBus",
            }

    @property
    def mode(self) -> str:
        """Mode actuel (distributed ou standalone)."""
        return self._mode

    @property
    def is_distributed(self) -> bool:
        """Indique si le mode distribué est actif."""
        return self._mode == "distributed"