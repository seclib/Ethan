"""Jarvis OS — Python SDK Client"""

import httpx
from typing import Any

from .models import ChatMessage, ChatResponse, AgentInfo, MemoryEntry


class JarvisClient:
    """Client SDK pour interagir avec Jarvis OS."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def chat(
        self,
        message: str,
        model: str | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        """Chat with Jarvis."""
        response = await self._client.post(
            "/api/chat",
            json={"message": message, "model": model, "stream": stream},
        )
        response.raise_for_status()
        data = response.json()
        return ChatResponse(**data)

    async def run_agent(
        self,
        agent_name: str,
        input_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an agent."""
        response = await self._client.post(
            f"/api/agents/{agent_name}/run",
            json={"input": input_data or {}},
        )
        response.raise_for_status()
        return response.json()

    async def list_agents(self) -> list[AgentInfo]:
        """List all available agents."""
        response = await self._client.get("/api/agents")
        response.raise_for_status()
        return [AgentInfo(**a) for a in response.json()]

    @property
    def memory(self) -> "MemoryAPI":
        return MemoryAPI(self._client)

    async def health(self) -> dict[str, Any]:
        """Check service health."""
        response = await self._client.get("/health")
        return response.json()

    async def close(self):
        await self._client.aclose()


class MemoryAPI:
    """Memory operations via SDK."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def store(self, key: str, value: str, namespace: str = "default") -> None:
        response = await self._client.post(
            "/api/memory/store",
            json={"key": key, "value": value, "namespace": namespace},
        )
        response.raise_for_status()

    async def retrieve(self, key: str, namespace: str = "default") -> MemoryEntry | None:
        response = await self._client.get(
            f"/api/memory/{namespace}/{key}",
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return MemoryEntry(**response.json())

    async def search(self, query: str, namespace: str = "default", limit: int = 10) -> list[MemoryEntry]:
        response = await self._client.post(
            "/api/memory/search",
            json={"query": query, "namespace": namespace, "limit": limit},
        )
        response.raise_for_status()
        return [MemoryEntry(**m) for m in response.json()]