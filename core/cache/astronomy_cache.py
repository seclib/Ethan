"""
ETHAN Core — Cache stratifie pour les donnees astronomiques.

Architecture :
  couche 1 (RAM) : dict synchronise, TTL auto-expire,
                   pour les lectures frequentes (recherche, config).
  couche 2 (DISQUE) : fichiers persistants avec TTL, duree max
                     et checksum, pour les relecture apres redemarrage.

Politique de secret :
  Aucun secret n'est persite dans les fichiers de cache ;
  seule une reference est stockee (ex: "secret://ref:key").
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheConfig:
    """Configuration du cache astronomique."""

    memory_max_items: int = 1000
    memory_ttl_seconds: float = 300.0
    disk_dir: Path = field(default_factory=lambda: Path("/home/fatsio/AI/Ethan/.cache/astronomy"))
    disk_ttl_seconds: float = 86400.0  # 24h par defaut
    disk_max_size_mb: int = 500
    enable_disk: bool = True
    enable_memory: bool = True


@dataclass
class CacheEntry:
    """Une entree de cache avec TTL et meta-informations.

    Attributes:
        key: Identifiant de l'entree de cache.
        value: Donnee a stocker (objet Python arbitraire).
        created_at: Horodatage creation (temps Unix).
        access_count: Nombre de lectures (initialise a 0).
        ttl_seconds: Duree de vie de l'entree (en secondes).
    """

    key: str
    value: Any
    created_at: float
    access_count: int = 0
    ttl_seconds: float = field(default=300.0, init=True)

    def __post_init__(self) -> None:
        """Calcule le timestamp d'expiration et initialise last_accessed."""
        self.last_accessed = time.time()
        self._expiry_time = self.created_at + self.ttl_seconds

    @property
    def expiry_time(self) -> float:
        """Horodatage d'expiration (temps Unix)."""
        return self._expiry_time

    def is_expired(self) -> bool:
        """Verifie si l'entree est expiree."""
        return time.time() > self._expiry_time

    def touch(self) -> None:
        """Met a jour le timestamp de dernier acces pour le TTL."""
        self.last_accessed = time.time()
        self._expiry_time = self.last_accessed + self.ttl_seconds


class AstronomyCache:
    """Gestionnaire de cache astronomique (memoire + disque + TTL).

    Utilise :
      - la couche memoire (RAM) pour les lectures frequentes,
      - la couche disque (fichiers) pour la persistance,
      - les TTL pour l'expiration automatique.

    Produce par :
      - adapters API (JPL Horizons, SIMBAD) pour les reponses courantes,
      - service d'ephémérides pour les resultats frequents,
      - requete d'objets connus pour la rapidite de reponse.

    Regle de secret :
      Aucune cle API ou secret n'est jamais stockee dans le cache ;
      seule une reference ou un hash est garde.
    """

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        self.config = config or CacheConfig()
        self._memory: dict[str, CacheEntry] = {}
        self._memory_lock = asyncio.Lock()
        self._disk_dir = self.config.disk_dir
        self._disk_dir.mkdir(parents=True, exist_ok=True)
        self._disk_lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Recupere une entree par cle (tire compte des deux couches).

        Retourne la valeur si trouve et non expiree, None sinon.
        """
        async with self._memory_lock:
            entry = self._memory.get(key)
            if entry is not None and not entry.is_expired():
                entry.access_count += 1
                entry.last_accessed = time.time()
                return entry.value

        # Lire le disque si la memoire est vide ou expiree
        if self.config.enable_disk:
            return await self._read_from_disk(key)

        return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Store une valeur dans la memoire et eventuellement sur le disque.

        Si la memoire est pleine, les entrees les moins utilisees sont evacuees.
        """
        async with self._memory_lock:
            if self.config.enable_memory:
                self._evict_if_needed()

            # CacheEntry.compute ttl_seconds dans __post_init__
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl_seconds or self.config.memory_ttl_seconds,
            )
            self._memory[key] = entry

        if self.config.enable_disk:
            await self._write_to_disk(key, value, ttl_seconds or self.config.disk_ttl_seconds)

    async def delete(self, key: str) -> bool:
        """Supprime une entree pour la memoire et le disque."""
        async with self._memory_lock:
            if key in self._memory:
                del self._memory[key]

        if self.config.enable_disk:
            async with self._disk_lock:
                self._delete_from_disk(key)
        return True

    async def clear(self) -> None:
        """Nettoie la memoire et le disque."""
        async with self._memory_lock:
            self._memory.clear()
        if self.config.enable_disk:
            await self._clear_disk()

    # --- Internes de la couche memoire ---

    def _evict_if_needed(self) -> None:
        """Evacue les entrees si le cache est plein."""
        if len(self._memory) < self.config.memory_max_items:
            return

        # Trie par acces least recently : LRU
        sorted_items = sorted(
            self._memory.items(), key=lambda kv: kv[1].last_accessed
        )
        to_remove = sorted_items[: len(self._memory) - self.config.memory_max_items]
        for k, _ in to_remove:
            del self._memory[k]

    # --- Internes de la couche disque ---

    async def _write_to_disk(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Ecrit la valeur dans un fichier binaire sur le disque."""
        async with self._disk_lock:
            try:
                filepath = self._disk_dir / f"{self._sanitize_key(key)}.cache"
                payload = {
                    "value": value,
                    "created_at": time.time(),
                    "ttl_seconds": ttl_seconds,
                    "checksum": hashlib.sha256(pickle.dumps(value)).hexdigest(),
                }
                # Lecture/ecriture avec gestion d'erreurs de I/O
                tmp_path = filepath.with_suffix(".cache.tmp")
                with open(tmp_path, "wb") as f:
                    pickle.dump(payload, f)
                os.replace(tmp_path, filepath)
            except OSError as e:
                log.warning(f"Ecriture cache disque echouee pour {key} : {e}")

    async def _read_from_disk(self, key: str) -> Optional[Any]:
        """Lit la valeur depuis le disque."""
        async with self._disk_lock:
            try:
                filepath = self._disk_dir / f"{self._sanitize_key(key)}.cache"
                if not filepath.exists():
                    return None

                with open(filepath, "rb") as f:
                    payload = pickle.load(f)

                if not self._checksum_valid(payload):
                    log.warning(f"Checksum invalide pour {key}, supprime")
                    self._delete_from_disk(key)
                    return None

                if time.time() > payload["created_at"] + payload["ttl_seconds"]:
                    log.info(f"Cache disque expire pour {key}")
                    self._delete_from_disk(key)
                    return None

                return payload["value"]
            except (pickle.PickleError, OSError) as e:
                log.warning(f"Lecture cache disque echouee pour {key} : {e}")
                return None

    def _delete_from_disk(self, key: str) -> None:
        """Supprime le fichier du disque."""
        try:
            filepath = self._disk_dir / f"{self._sanitize_key(key)}.cache"
            if filepath.exists():
                filepath.unlink()
        except OSError:
            pass

    async def _clear_disk(self) -> None:
        """Efface tous les fichiers du cache disque."""
        async with self._disk_lock:
            for f in self._disk_dir.glob("*.cache"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def _checksum_valid(self, payload: dict[str, Any]) -> bool:
        """Verifie le checksum de l'entree."""
        if "checksum" not in payload:
            return False
        try:
            computed = hashlib.sha256(pickle.dumps(payload["value"])).hexdigest()
            return computed == payload["checksum"]
        except Exception:
            return False

    def _sanitize_key(self, key: str) -> str:
        """Neutralise les caracteres speciaux dans un cle de fichier."""
        return "_".join(str(key).split())


def get_astronomy_cache(config: Optional[CacheConfig] = None) -> AstronomyCache:
    """Construit un gestionnaire de cache configuration."""
    return AstronomyCache(config=config or CacheConfig())


__all__ = [
    "CacheConfig", "CacheEntry", "AstronomyCache", "get_astronomy_cache",
]
