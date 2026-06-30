"""Telegram Adapter — Connecteur Telegram pour MessagingGateway.

Utilise python-telegram-bot v20+ (asyncio).
"""

from __future__ import annotations

import logging
from typing import Any

from interfaces.channels.base import ChannelAdapter, IncomingMessage, MessageTarget, Platform

logger = logging.getLogger(__name__)


class TelegramAdapter(ChannelAdapter):
    """Adaptateur Telegram."""

    def __init__(self, token: str, allowed_users: list[str] | None = None) -> None:
        self._token = token
        self._allowed_users = set(allowed_users or [])
        self._application: Any = None
        self._dispatch_cb: Any = None

    @property
    def platform(self) -> Platform:
        return Platform.TELEGRAM

    async def start(self) -> None:
        try:
            from telegram.ext import ApplicationBuilder, MessageHandler, filters
        except ImportError as e:
            raise RuntimeError(
                "python-telegram-bot requis : pip install python-telegram-bot"
            ) from e

        async def on_message(update: Any, context: Any) -> None:
            if self._dispatch_cb is None:
                return
            msg = update.message
            if msg is None:
                return
            user_id = str(msg.from_user.id)
            if self._allowed_users and user_id not in self._allowed_users:
                logger.info("Telegram: user %s not allowed", user_id)
                return
            incoming = IncomingMessage(
                platform=Platform.TELEGRAM,
                user_id=user_id,
                text=msg.text or "",
                channel_id=str(msg.chat_id),
                raw=update,
            )
            await self._dispatch_cb(incoming)

        self._application = (
            ApplicationBuilder().token(self._token).build()
        )
        self._application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, on_message)
        )
        await self._application.initialize()
        await self._application.start()
        logger.info("TelegramAdapter: started")

    async def stop(self) -> None:
        if self._application is not None:
            await self._application.stop()
            await self._application.shutdown()
            logger.info("TelegramAdapter: stopped")

    async def send(self, reply: str, target: MessageTarget) -> None:
        if self._application is None:
            raise RuntimeError("TelegramAdapter not started")
        if target.platform != Platform.TELEGRAM:
            raise ValueError("Wrong platform for TelegramAdapter")
        await self._application.bot.send_message(
            chat_id=int(target.user_id),
            text=reply,
        )