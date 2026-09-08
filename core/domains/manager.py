from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_RECORDS = "domains"
_DOMAIN_MEMBERSHIPS = "domain-memberships"

# Registre des types de ressources classables (ouvert : voir add_provider).
DEFAULT_RESOURCE_TYPES = ("knowledge", "collection", "skill", "source")

# Sentinelle interne : distingue « champ non fourni » de « valeur None ».
_UNSET = object()


class DomainResourceProvider:
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


class DomainManager:
    """Domains fonctionnels et rattachement multi-ressources (Core-owned).

    Args:
        store: CoreRecordStore partagé (PG durable + Redis + fallback mémoire).
        event_bus: Bus d'événements optionnel (toutes les mutations sont
            publiées).
        knowledge/collections/skills: managers Core optionnels — chacun
            enregistre un provider de résolution pour son type de ressource.
        resource_types: registry de types additionnels (ouvert).
    """

    def __init__(
        self,
        store: CoreRecordStore | None = None,
        event_bus: EventBus | None = None,
        *,
        knowledge: Any | None = None,
        collections: Any | None = None,
        skills: Any | None = None,
        resource_types: tuple[str, ...] | None = None,
    ) -> None:
        self._store = store or CoreRecordStore()
        self._bus = event_bus
        self._providers: dict[str, DomainResourceProvider] = {}
        self._resource_types: set[str] = set(resource_types or DEFAULT_RESOURCE_TYPES)
        if knowledge is not None:
            self.add_provider(
                "knowledge", DomainResourceProvider(knowledge.get, knowledge.list)
            )
        if collections is not None:
            self.add_provider(
                "collection",
                DomainResourceProvider(
                    collections.get_collection, collections.list_collections
                ),
            )
        if skills is not None:
            self.add_provider(
                "skill", DomainResourceProvider(skills.get_skill, skills.list_skills)
            )
        self._resource_types |= set(self._providers)

    def add_provider(
        self, resource_type: str, provider: DomainResourceProvider
    ) -> None:
        """Enregistre un type de ressource classable (registre ouvert)."""
        self._providers[resource_type] = provider
        self._resource_types.add(resource_type)

    # ── CRUD domains ─────────────────────────────────────────────────────

    async def create_domain(
        self,
        name: str,
        *,
        description: str = "",
        user_id: str = "anonymous",
        icon: str | None = None,
        color: str | None = None,
        order: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Crée un domain de spécialité (nom unique, plat, librement choisi)."""
        normalized = (name or "").strip()
        if not normalized:
            raise ValueError("Domain name must not be empty")
        await self._ensure_unique_name(normalized)
        domain = {
            "id": str(uuid4()),
            "name": normalized,
            "description": description,
            "user_id": user_id,
            "icon": icon,
            "color": color,
            "order": order,
            "metadata": dict(metadata or {}),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        await self._store.save(_DOMAIN_RECORDS, domain["id"], domain)
        await self._publish(
            EventType.DOMAIN_CREATED, "domain.created", {"domain": domain}
        )
        return domain

    async def get_domain(self, domain_id: str) -> dict[str, Any] | None:
        return await self._store.get(_DOMAIN_RECORDS, domain_id)

    async def find_by_name(self, name: str) -> dict[str, Any] | None:
        """Retrouve un domain par son nom unique (utile aux agents)."""
        normalized = (name or "").strip().lower()
        for domain in await self._store.list(_DOMAIN_RECORDS):
            if domain.get("name", "").strip().lower() == normalized:
                return domain
        return None

    async def list_domains(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """Liste plate des domains (ordre : ``order`` puis ``name``)."""
        domains = await self._store.list(_DOMAIN_RECORDS)
        if user_id is not None:
            domains = [d for d in domains if d.get("user_id") == user_id]
        return sorted(
            domains, key=lambda d: (d.get("order", 0), d.get("name", ""))
        )

    async def update_domain(
        self,
        domain_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        icon: Any = _UNSET,
        color: Any = _UNSET,
        order: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Mise à jour partielle : seuls les champs fournis sont modifiés."""
        domain = await self.get_domain(domain_id)
        if domain is None:
            return None
        if name is not None:
            normalized = name.strip()
            if not normalized:
                raise ValueError("Domain name must not be empty")
            if normalized != domain["name"]:
                await self._ensure_unique_name(normalized)
            domain["name"] = normalized
        if description is not None:
            domain["description"] = str(description)
        if icon is not _UNSET:
            domain["icon"] = icon
        if color is not _UNSET:
            domain["color"] = color
        if order is not None:
            domain["order"] = int(order)
        if metadata is not None:
            domain["metadata"] = dict(metadata)
        domain["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_RECORDS, domain_id, domain)
        await self._publish(
            EventType.DOMAIN_UPDATED, "domain.updated", {"domain": domain}
        )
        return domain

    async def delete_domain(self, domain_id: str) -> dict[str, Any] | None:
        """Supprime un domain.

        Les ressources rattachées ne sont **pas** supprimées (relation, pas
        possession) — elles redeviennent simplement sans domain.  Les
        références ``domain_ids`` des agents ne sont pas réécrites : la
        sélection d'un agent est résolue à l'exécution et les ids inconnus
        sont ignorés (aucune ressource fantôme injectée).
        """
        domain = await self.get_domain(domain_id)
        if domain is None:
            return None
        for membership in await self._store.list(_DOMAIN_MEMBERSHIPS):
            if membership.get("domain_id") == domain_id:
                await self._store.delete(_DOMAIN_MEMBERSHIPS, membership["id"])
        await self._store.delete(_DOMAIN_RECORDS, domain_id)
        await self._publish(
            EventType.DOMAIN_DELETED,
            "domain.deleted",
            {"domain_id": domain_id},
        )
        return {"id": domain_id}

    # ── memberships (relation domain ↔ ressource, many-to-many) ─────────

    async def attach_resource(
        self, domain_id: str, resource_type: str, resource_id: str
    ) -> dict[str, Any]:
        """Rattache une ressource à un domain (idempotent).

        La ressource n'est ni copiée ni déplacée : le domain n'est qu'une
        référence vers le record possédé par son manager Core d'origine.
        """
        if await self.get_domain(domain_id) is None:
            raise ValueError(f"Domain {domain_id} not found")
        if resource_type not in self._resource_types:
            raise ValueError(
                f"Unknown resource type {resource_type!r} "
                f"(known: {sorted(self._resource_types)})"
            )
        if not str(resource_id).strip():
            raise ValueError("resource_id must not be empty")

        membership_id = _membership_id(domain_id, resource_type, resource_id)
        existing = await self._store.get(_DOMAIN_MEMBERSHIPS, membership_id)
        if existing is not None:
            return existing

        membership = {
            "id": membership_id,
            "domain_id": domain_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "created_at": _utc_now(),
        }
        await self._store.save(_DOMAIN_MEMBERSHIPS, membership_id, membership)
        await self._publish(
            EventType.DOMAIN_RESOURCE_ATTACHED,
            "domain.resource.attached",
            {
                "domain_id": domain_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        return membership

    async def detach_resource(
        self, domain_id: str, resource_type: str, resource_id: str
    ) -> bool:
        """Détache une ressource d'un domain (la ressource elle-même reste)."""
        membership_id = _membership_id(domain_id, resource_type, resource_id)
        existing = await self._store.get(_DOMAIN_MEMBERSHIPS, membership_id)
        if existing is None:
            return False
        await self._store.delete(_DOMAIN_MEMBERSHIPS, membership_id)
        await self._publish(
            EventType.DOMAIN_RESOURCE_DETACHED,
            "domain.resource.detached",
            {
                "domain_id": domain_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        return True

    async def list_resource_ids(
        self, domain_id: str, resource_type: str | None = None
    ) -> list[dict[str, str]]:
        """Ids bruts rattachés à un domain, filtrables par type."""
        result = []
        for membership in await self._store.list(_DOMAIN_MEMBERSHIPS):
            if membership.get("domain_id") != domain_id:
                continue
            if resource_type is not None and membership.get(
                "resource_type"
            ) != resource_type:
                continue
            result.append(
                {
                    "resource_type": membership["resource_type"],
                    "resource_id": membership["resource_id"],
                }
            )
        return result

    async def list_resources(
        self, domain_id: str, resource_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Ressources réelles résolues via les managers Core propriétaires.

        Un id devenu orphelin (ressource supprimée) purge son lien au vol
        (auto-pruning) : aucun record fantôme n'est jamais renvoyé.
        """
        resolved: list[dict[str, Any]] = []
        for ref in await self.list_resource_ids(domain_id, resource_type):
            rtype = ref["resource_type"]
            provider = self._providers.get(rtype)
            record = None
            if provider is not None:
                try:
                    record = _to_dict(await provider.get(ref["resource_id"]))
                except Exception:  # noqa: BLE001 — défensif : provider défaillant ne casse pas la lecture
                    record = None
            if record is None and provider is not None:
                # La ressource n'existe plus : on purge le lien orphelin.
                await self._store.delete(
                    _DOMAIN_MEMBERSHIPS,
                    _membership_id(domain_id, rtype, ref["resource_id"]),
                )
                continue
            resolved.append(
                {
                    "resource_type": rtype,
                    "resource_id": ref["resource_id"],
                    "record": record,
                }
            )
        return resolved

    async def count_resources(self, domain_id: str) -> int:
        """Nombre de ressources rattachées (pour l'affichage des listes)."""
        return len(await self.list_resource_ids(domain_id))

    async def list_domains_for_resource(
        self, resource_type: str, resource_id: str
    ) -> list[str]:
        """Ids des domains auxquels une ressource appartient (index inverse)."""
        return [
            m["domain_id"]
            for m in await self._store.list(_DOMAIN_MEMBERSHIPS)
            if m.get("resource_type") == resource_type
            and m.get("resource_id") == resource_id
        ]

    async def list_domains_with_counts(
        self, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Domains enrichis de ``resource_count`` (vue liste WebUI/API)."""
        domains = await self.list_domains(user_id)
        return [
            {**domain, "resource_count": await self.count_resources(domain["id"])}
            for domain in domains
        ]

    # ── internals ────────────────────────────────────────────────────────

    async def _ensure_unique_name(self, name: str) -> None:
        for domain in await self._store.list(_DOMAIN_RECORDS):
            if domain.get("name", "").strip().lower() == name.strip().lower():
                raise ValueError(f"Domain name already exists: {name}")

    async def _publish(
        self, event_type: EventType, subject: str, payload: dict[str, Any]
    ) -> None:
        if self._bus is None:
            return
        await self._bus.publish(
            subject,
            Event(type=event_type, source="domains", payload=payload),
        )


def _membership_id(domain_id: str, resource_type: str, resource_id: str) -> str:
    return f"{domain_id}:{resource_type}:{resource_id}"


def _to_dict(record: Any) -> dict[str, Any] | None:
    """Normalise un record Core (dict ou objet avec ``to_dict``)."""
    if record is None:
        return None
    if isinstance(record, dict):
        return record
    if hasattr(record, "to_dict"):
        return record.to_dict()
    return None


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "DEFAULT_RESOURCE_TYPES",
    "DomainManager",
    "DomainResourceProvider",
]


