"""Discord Adapter — Connecteur Discord pour MessagingGateway.

Utilise discord.py (nextcord ou py-cord compatibles).
"""

from __future__ import annotations

import logging
from typing import Any

from interfaces.channels.base import ChannelAdapter, IncomingMessage, MessageTarget, Platform

logger = logging.getLogger(__name__)


class DiscordAdapter(ChannelAdapter):
    """Adaptateur Discord."""

    def __init__(self, token: str, allowed_guilds: list[int] | None = None) -> None:
        self._token = token
        self._allowed_guilds = set(allowed_guilds or [])
        self._client: Any = None
        self._dispatch_cb: Any = None

    @property
    def platform(self) -> Platform:
        return Platform.DISCORD

    async def start(self) -> None:
        try:
            import discord
            from discord.ext import commands
        except ImportError as e:
            raise RuntimeError(
                "discord.py requis : pip install discord.py"
            ) from e

        intents = discord.Intents.default()
        intents.message_content = True

        bot = commands.Bot(command_prefix="!", intents=intents)

        @bot.event
        async def on_ready() -> None:
            logger.info("DiscordAdapter: connected as %s", bot.user)

        @bot.event
        async def on_message(message: discord.Message) -> None:
            if self._dispatch_cb is None:
                return
            if message.author == bot.user:
                return
            if self._allowed_guilds and message.guild.id not in self._allowed_guilds:
                return
            incoming = IncomingMessage(
                platform=Platform.DISCORD,
                user_id=str(message.author.id),
                text=message.content,
                channel_id=str(message.channel.id),
                raw=message,
            )
            await self._dispatch_cb(incoming)

        self._client = bot
        # Lancer le bot en arrière-plan (ne pas bloquer)
        import asyncio
        asyncio.create_task(bot.start(self._token))
        logger.info("DiscordAdapter: started")

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.close()
            logger.info("DiscordAdapter: stopped")

    async def send(self, reply: str, target: MessageTarget) -> None:
        if self._client is None:
            raise RuntimeError("DiscordAdapter not started")
        if target.platform != Platform.DISCORD:
            raise ValueError("Wrong platform for DiscordAdapter")
        channel = self._client.get_channel(int(target.channel_id))
        if channel is None:
            user = await self._client.fetch_user(int(target.user_id))
            if user is None:
                raise ValueError("Channel or user not found")
            await user.send(reply)
        else:
            await channel.send(reply)