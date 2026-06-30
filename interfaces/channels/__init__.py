"""ETHAN Channels — Multi-platform messaging adapters.

Abstraction pour connecter Ethan à diverses plateformes de messagerie
(Telegram, Discord, WhatsApp, Signal, Slack) via des adaptateurs normalisés.
"""

from .base import ChannelAdapter, IncomingMessage, MessageTarget, Platform
from .gateway import MessagingGateway

__version__ = "1.0.0"
__all__ = ["ChannelAdapter", "IncomingMessage", "MessageTarget", "Platform", "MessagingGateway"]