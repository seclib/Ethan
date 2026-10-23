"""Redis Store — Working Memory (Redis).

Stockage rapide pour :
- Sessions actives (avec TTL)
- Cache de modules
- Locks et sémaphores
- État live du système
"""

from __future__ import annotations

import json
import logging
from typing import Any

from core.memory.interface import MemoryStore, SearchResult

logger = logging.getLogger(__name__)


class RedisStore(MemoryStore):
    """Implémentation Redis du MemoryStore.

    Utilise Redis comme working memory :
    - Clés avec TTL pour les sessions
    - Namespaces via préfixe
    - Pas de recherche sémantique (utiliser VectorStore pour ça)
    """

    def __init__(self, url: str = "redis://localhost:6379", prefix: str = "ethan:"):
        self._url = url
        self._prefix = prefix
        self._client: Any = None  # redis.Redis

    async def connect(self) -> None:
        """Connexion à Redis."""
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self._url,
                decode_responses=True,
                protocol=2,
            )
            await self._client.ping()
            logger.info(f"RedisStore connected to {self._url}")
        except ImportError:
            raise RuntimeError(
                "redis not installed. Install with: pip install redis"
            )
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Redis at {self._url}: {e}")

    async def close(self) -> None:
        """Ferme la connexion."""
        if self._client:
            await self._client.close()

    def _key(self, namespace: str, key: str) -> str:
        """Construit la clé Redis complète."""
        return f"{self._prefix}{namespace}:{key}"

    async def store(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Stocke une valeur."""
        if not self._client:
            await self.connect()

        full_key = self._key(namespace, key)
        data = json.dumps(value) if not isinstance(value, str) else value

        if ttl:
            await self._client.setex(full_key, ttl, data)
        else:
            await self._client.set(full_key, data)

    async def get(self, namespace: str, key: str) -> Any | None:
        """Récupère une valeur."""
        if not self._client:
            await self.connect()

        full_key = self._key(namespace, key)
        data = await self._client.get(full_key)
        if data is None:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    async def delete(self, namespace: str, key: str) -> None:
        """Supprime une valeur."""
        if not self._client:
            await self.connect()

        full_key = self._key(namespace, key)
        await self._client.delete(full_key)

    async def list_namespace(self, namespace: str) -> list[str]:
        """Liste toutes les clés dans un namespace."""
        if not self._client:
            await self.connect()

        pattern = f"{self._prefix}{namespace}:*"
        keys = await self._client.keys(pattern)
        # Extraire juste la clé (sans préfixe)
        prefix_len = len(self._prefix) + len(namespace) + 1
        return [k[prefix_len:] for k in keys]

    async def search(
        self,
        namespace: str,
        query: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Recherche simple (pas de recherche sémantique dans Redis).

        Redis ne fait pas de recherche sémantique.
        Utiliser VectorStore pour ça.
        """
        logger.warning("RedisStore.search() is not semantic. Use VectorStore instead.")
        keys = await self.list_namespace(namespace)
        results = []
        for key in keys[:limit]:
            value = await self.get(namespace, key)
            results.append(SearchResult(key=key, value=value))
        return results

    async def exists(self, namespace: str, key: str) -> bool:
        """Vérifie si une clé existe."""
        if not self._client:
            await self.connect()

        full_key = self._key(namespace, key)
        return await self._client.exists(full_key) > 0

    async def ttl(self, namespace: str, key: str) -> int | None:
        """Retourne le TTL restant."""
        if not self._client:
            await self.connect()

        full_key = self._key(namespace, key)
        ttl = await self._client.ttl(full_key)
        if ttl < 0:
            return None
        return ttl

    # ─── Méthodes utilitaires ────────────────────────────────────────

    async def set_lock(self, lock_name: str, ttl: int = 10) -> bool:
        """Tente d'acquérir un lock (distribué).

        Returns:
            True si lock acquis, False sinon
        """
        if not self._client:
            await self.connect()

        lock_key = f"{self._prefix}lock:{lock_name}"
        # SETNX + EXPIRE atomique
        acquired = await self._client.set(lock_key, "1", ex=ttl, nx=True)
        return acquired is True

    async def release_lock(self, lock_name: str) -> None:
        """Libère un lock."""
        if not self._client:
            await self.connect()

        lock_key = f"{self._prefix}lock:{lock_name}"
        await self._client.delete(lock_key)

    async def increment(self, namespace: str, key: str, amount: int = 1) -> int:
        """Incrémente un compteur."""
        if not self._client:
            await self.connect()

        full_key = self._key(namespace, key)
        return await self._client.incrby(full_key, amount)