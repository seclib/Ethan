"""Jarvis OS — Python SDK

SDK public pour interagir avec Jarvis OS depuis des applications Python.

Usage:
    from jarvis_sdk import JarvisClient

    client = JarvisClient(api_key="...", base_url="http://localhost:8000")

    # Chat avec l'IA
    response = await client.chat("Hello, Jarvis!")

    # Exécuter un agent
    result = await client.run_agent("planner", {"objective": "..."})

    # Stocker en mémoire
    await client.memory.store("key", "value", namespace="default")

    # Recherche vectorielle
    results = await client.memory.search("query", namespace="default")
"""

from .client import JarvisClient
from .models import ChatMessage, ChatResponse, AgentInfo, MemoryEntry

__all__ = [
    "JarvisClient",
    "ChatMessage",
    "ChatResponse",
    "AgentInfo",
    "MemoryEntry",
]