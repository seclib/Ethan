"""WhatsApp Adapter — Connecteur WhatsApp pour MessagingGateway.

Utilise whatsapp-python (wrapper Baileys) ou whatsapp-web.js.
Ici : abstraction avec fallback console pour dev.
"""

from __future__ import annotations

import logging
from typing import Any

from interfaces.channels.base import ChannelAdapter, IncomingMessage, MessageTarget, Platform

logger = logging.getLogger(__name__)


class WhatsAppAdapter(ChannelAdapter):
    """Adaptateur WhatsApp."""

    def __init__(self, session_name: str = "ethan-whatsapp") -> None:
        self._session_name = session_name
        self._client: Any = None
        self._dispatch_cb: Any = None

    @property
    def platform(self) -> Platform:
        return Platform.WHATSAPP

    async def start(self) -> None:
        try:
            # Tentative d'import de whatsapp-python (Baileys wrapper)
            from whatsapp import WhatsAppClient
        except ImportError:
            logger.warning(
                "WhatsAppAdapter: whatsapp-python non installé, mode simulation"
            )
            WhatsAppClient = None

        if WhatsAppClient is not None:
            self._client = WhatsAppClient(session_name=self._session_name)
            await self._client.connect()
            logger.info("WhatsAppAdapter: connecté")
        else:
            # Fallback : mode simulation (console)
            logger.info("WhatsAppAdapter: mode simulation (pas de client réel)")
            self._client = None

    async def stop(self) -> None:
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception as e:
                logger.warning("WhatsAppAdapter: erreur déconnexion: %s", e)
            logger.info("WhatsAppAdapter: déconnecté")

    async def send(self, reply: str, target: MessageTarget) -> None:
        if self._client is None:
            # Mode simulation : loguer
            logger.info(
                "WhatsAppAdapter [SIMULATION] → %s: %s",
                target.user_id, reply[:100],
            )
            return
        if target.platform != Platform.WHATSAPP:
            raise ValueError("Wrong platform for WhatsAppAdapter")
        await self._client.send_message(
            to=target.user_id,
            text=reply,
        )