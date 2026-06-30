"""MessagingGateway — Point d'entrée central pour les canaux de messagerie.

Gère le cycle de vie de tous les adaptateurs et dispatche les messages
entrants vers le handler central d'Ethan.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from interfaces.channels.base import ChannelAdapter, IncomingMessage

logger = logging.getLogger(__name__)


class MessagingGateway:
    """Point d'entrée central pour les canaux de messagerie.

    - Enregistre et démarre les adaptateurs
    - Dispatche les messages entrants vers le handler central
    - Arrête proprement tous les canaux
    """

    def __init__(
        self,
        message_handler: Any = None,
    ) -> None:
        self._adapters: dict[str, ChannelAdapter] = {}
        self._message_handler = message_handler
        self._running = False

    def register(self, adapter: ChannelAdapter) -> None:
        """Enregistre un adaptateur de canal."""
        name = adapter.platform.value
        if name in self._adapters:
            logger.warning("MessagingGateway: adapter %s already registered, replacing", name)
        adapter.set_dispatch(self._on_message)
        self._adapters[name] = adapter
        logger.info("MessagingGateway: registered adapter %s", name)

    async def start_all(self) -> None:
        """Démarre tous les adaptateurs enregistrés."""
        self._running = True
        for name, adapter in self._adapters.items():
            try:
                await adapter.start()
                logger.info("MessagingGateway: started %s", name)
            except Exception as e:
                logger.error("MessagingGateway: failed to start %s: %s", name, e)

    async def stop_all(self) -> None:
        """Arrête tous les adaptateurs."""
        self._running = False
        for name, adapter in self._adapters.items():
            try:
                await adapter.stop()
                logger.info("MessagingGateway: stopped %s", name)
            except Exception as e:
                logger.error("MessagingGateway: failed to stop %s: %s", name, e)

    async def _on_message(self, message: IncomingMessage) -> None:
        """Dispatche un message entrant vers le handler central."""
        logger.debug(
            "MessagingGateway: message from %s/%s: %s",
            message.platform.value, message.user_id,
            message.text[:100],
        )
        if self._message_handler is not None:
            try:
                await self._message_handler(message)
            except Exception as e:
                logger.error(
                    "MessagingGateway: handler error for %s: %s",
                    message.session_key, e,
                )
        else:
            logger.warning("MessagingGateway: no message handler registered")

    async def broadcast(self, text: str, platform: str | None = None) -> int:
        """Envoie un message à tous les canaux (ou un canal spécifique)."""
        count = 0
        for name, adapter in self._adapters.items():
            if platform is not None and name != platform:
                continue
            try:
                from interfaces.channels.base import MessageTarget, Platform
                target = MessageTarget(
                    platform=Platform(name),
                    user_id="__broadcast__",
                )
                await adapter.send(text, target)
                count += 1
            except Exception as e:
                logger.warning("MessagingGateway: broadcast to %s failed: %s", name, e)
        return count

    @property
    def active_adapters(self) -> list[str]:
        """Liste des adaptateurs actifs."""
        return list(self._adapters.keys())

    def get_adapter(self, platform: str) -> ChannelAdapter | None:
        """Récupère un adaptateur par sa plateforme."""
        return self._adapters.get(platform)