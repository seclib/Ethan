"""Socle partagé Folders/Domains — helpers de rattachement multi-ressources.

``FolderManager`` (core/folders) et ``DomainManager`` (core/domains)
appliquaient le même protocole par copier-coller.  Ce module mutualise
la partie **strictement identique** — zéro changement de comportement :

  - ``ResourceProvider`` : adapter getter/lister d'un manager Core ;
  - ``membership_key``   : clé idempotente d'une relation ;
  - ``normalize_record`` : dict ou objet ``to_dict`` → dict ;
  - ``utc_now``          : horodatage ISO-8601 (suffixe Z) ;
  - ``UNSET``            : sentinelle « champ non fourni ».

Les **politiques** restent chez chaque manager (écart assumé, Phase 4) :

  - ``FolderManager`` est **fail-closed** : il vérifie l'existence de la
    ressource (provider) avant de créer la relation — jamais de lien
    fantôme ;
  - ``DomainManager`` valide le domaine, le type de ressource et
    ``resource_id``, mais ne résout pas la ressource (lecture
    auto-prunée côté ``list_resources``).

Voir ``docs/hardening.md`` (Phase 4 — dette Folders/Domains).
"""

from __future__ import annotations

from typing import Any

# Sentinelle interne : distingue « champ non fourni » de « valeur None ».
UNSET = object()


class ResourceProvider:
    """Adapte un manager Core au protocole de résolution des ressources.

    ``getter``/``lister`` sont des callables asynchrones du manager
    propriétaire (ex. ``SkillStore.get_skill`` / ``SkillStore.list_skills``).
    Le provider ne duplique rien : il ne fait que lire à la demande.
    """

    def __init__(self, getter: Any, lister: Any) -> None:
        self._getter = getter
        self._lister = lister

    async def get(self, resource_id: str) -> Any:
        return await self._getter(resource_id)

    async def list_all(self) -> list[Any]:
        return list(await self._lister())


def membership_key(owner_id: str, resource_type: str, resource_id: str) -> str:
    """Clé idempotente d'une relation owner↔ressource."""
    return f"{owner_id}:{resource_type}:{resource_id}"


def normalize_record(record: Any) -> dict[str, Any] | None:
    """Normalise un record Core (dict ou objet avec ``to_dict``)."""
    if record is None:
        return None
    if isinstance(record, dict):
        return record
    if hasattr(record, "to_dict"):
        return record.to_dict()
    return None


def utc_now() -> str:
    """Horodatage ISO-8601 UTC (suffixe ``Z``)."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["UNSET", "ResourceProvider", "membership_key", "normalize_record", "utc_now"]
