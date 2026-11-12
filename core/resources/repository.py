"""Repository de persistance des ressources ETHAN — Source de vérité PostgreSQL.

P2.8.1 — Unification de la persistance.

`ResourceRegistry` disposait d'un stockage **fichier** (`registry-meta.json`)
distinct du `CoreRecordStore` utilisé par tous les autres services Core. Cette
divergence produisait deux défauts concrets :

1. les enregistrements de ressources n'étaient pas visibles des autres
   services Core (API, CLI, agents) ;
2. les `KnowledgeNode` créés par le registre partaient dans un
   `CoreRecordStore` **sans backend**, donc en mémoire seulement : ils
   disparaissaient au redémarrage alors que les métadonnées affirmaient
   `knowledge_state: indexed`.

`ResourceRepository` fait de `CoreRecordStore` le chemin d'écriture et de
lecture unique des `ResourceRecord`, sur le modèle des autres services Core
(`skills`, `knowledge`, `rag-documents`, `projects`, …).

Le fichier `registry-meta.json` reste supporté comme **amorçage** (bootstrap)
et comme **export portable**, mais il n'est plus une autorité concurrente :
lorsqu'un repository est disponible, c'est lui qui fait foi.

Aucun nouveau stockage n'est introduit : c'est la table existante
`core_domain_records`, domaine `resources`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

from core.resources.types import ResourceStatus, ResourceType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

# Domaine de persistance des ressources dans `core_domain_records`.
# Suit la convention des autres services Core (un domaine par type de donnee).
RESOURCE_DOMAIN = "resources"


class ResourceRepository:
    """Persistance des `ResourceRecord` via le `CoreRecordStore` partage.

    Le repository ne fait que de la sérialisation : il ne connaît ni la
    découverte, ni le cycle de vie, ni les relations. Ces responsabilités
    restent dans `ResourceRegistry`.

    Args:
        store: Store Core partagé (PostgreSQL + cache Redis en production).
            Sans store, le repository fonctionne en mémoire seule — utile
            pour les tests isolés, mais la persistance n'est alors pas
            garantie.
    """

    def __init__(self, store: CoreRecordStore | None = None) -> None:
        self._store = store or CoreRecordStore()
        self._domain = RESOURCE_DOMAIN

    @property
    def domain(self) -> str:
        """Domaine de persistance utilisé."""
        return self._domain

    @property
    def store(self) -> CoreRecordStore:
        """Store Core sous-jacent."""
        return self._store

    async def save(self, record: Any) -> None:
        """Enregistre (upsert) une ressource.

        Args:
            record: `ResourceRecord` à persister.
        """
        await self._store.save(self._domain, record.stable_id, record.to_dict())

    async def save_all(self, records: Iterable[Any]) -> int:
        """Enregistre un lot de ressources.

        L'écriture est idempotente : le `stable_id` est la cle, donc une
        re-execution ecrase la meme cle au lieu de dupliquer.

        Args:
            records: Ressources a persister.

        Returns:
            Nombre de ressources ecrites.
        """
        count = 0
        for record in records:
            await self.save(record)
            count += 1
        return count

    async def get(self, stable_id: str) -> Optional[Dict[str, Any]]:
        """Retourne l'enregistrement brut d'une ressource, ou None.

        Args:
            stable_id: Identifiant stable de la ressource.

        Returns:
            Dictionnaire serialise, ou None si absent.
        """
        return await self._store.get(self._domain, stable_id)

    async def load_all(self) -> List[Dict[str, Any]]:
        """Retourne tous les enregistrements de ressources.

        Returns:
            Liste de dictionnaires serialises.
        """
        return await self._store.list(self._domain)

    async def delete(self, stable_id: str) -> bool:
        """Supprime une ressource.

        Args:
            stable_id: Identifiant stable de la ressource.

        Returns:
            True si la ressource existait et a ete supprimee.
        """
        return await self._store.delete(self._domain, stable_id)

    async def count(self) -> int:
        """Retourne le nombre de ressources persistees.

        Returns:
            Nombre d'enregistrements dans le domaine.
        """
        return len(await self.load_all())

    async def sync_from_records(self, records: Iterable[Any]) -> Dict[str, int]:
        """Synchronise un ensemble de ressources dans le store.

        Cette operation **ecrase** la vue materialisee du domaine avec
        l'ensemble fourni : elle garantit qu'aucune ressource disparue ne
        reste dans la base. Elle ne supprime aucune donnee hors de ce
        domaine.

        Args:
            records: Ensemble complet de ressources a persister.

        Returns:
            Statistiques ``{"written": N, "removed": M}``.
        """
        written = 0
        seen: set[str] = set()
        for record in records:
            seen.add(record.stable_id)
            await self.save(record)
            written += 1

        removed = 0
        for existing in await self.load_all():
            record_id = existing.get("stable_id") or existing.get("id")
            if not record_id or record_id in seen:
                continue
            if await self.delete(record_id):
                removed += 1

        if removed:
            logger.info(
                "ResourceRepository : %d ressources retirees du domaine %s",
                removed,
                self._domain,
            )
        return {"written": written, "removed": removed}


def resource_metadata_summary(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait les metadonnees de classement d'une ressource.

    Utile pour les interfaces qui doivent afficher la classification sans
    connaitre le modele complet.

    Args:
        metadata: Metadonnees d'une ressource.

    Returns:
        Dictionnaire des champs de classement presents.
    """
    keys = (
        "domain",
        "level",
        "resource_type",
        "knowledge_state",
        "classification_reason",
        "categories",
        "description",
        "version",
        "author",
    )
    return {key: metadata[key] for key in keys if key in metadata}


__all__ = [
    "RESOURCE_DOMAIN",
    "ResourceRepository",
    "resource_metadata_summary",
    "ResourceStatus",
    "ResourceType",
]
