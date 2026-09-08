from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)

_DOMAIN_FOLDERS = "folders"
_DOMAIN_MEMBERSHIPS = "folder-memberships"

# Registre des types de ressources classables (ouvert : voir add_provider).
DEFAULT_RESOURCE_TYPES = ("knowledge", "collection", "skill")

# Sentinelle interne : distingue « champ non fourni » de « valeur None ».
_UNSET = object()


class FolderResourceProvider:
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


class FolderManager:
    """Dossiers utilisateur et classement multi-ressources (Core-owned).

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
        self._providers: dict[str, FolderResourceProvider] = {}
        self._resource_types: set[str] = set(resource_types or DEFAULT_RESOURCE_TYPES)
        if knowledge is not None:
            self.add_provider(
                "knowledge", FolderResourceProvider(knowledge.get, knowledge.list)
            )
        if collections is not None:
            self.add_provider(
                "collection",
                FolderResourceProvider(
                    collections.get_collection, collections.list_collections
                ),
            )
        if skills is not None:
            self.add_provider(
                "skill", FolderResourceProvider(skills.get_skill, skills.list_skills)
            )
        self._resource_types |= set(self._providers)

    def add_provider(
        self, resource_type: str, provider: FolderResourceProvider
    ) -> None:
        """Enregistre un type de ressource classable (registre ouvert)."""
        self._providers[resource_type] = provider
        self._resource_types.add(resource_type)

    # ── CRUD dossiers ────────────────────────────────────────────────────

    async def create_folder(
        self,
        name: str,
        *,
        description: str = "",
        user_id: str = "anonymous",
        parent_id: str | None = None,
        icon: str | None = None,
        order: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Crée un dossier nommé librement par l'utilisateur.

        ``parent_id`` permet d'imbriquer librement des sous-dossiers ; aucune
        hiérarchie n'est seedée ni imposée (avant la première création il
        n'existe aucun dossier).
        """
        normalized = (name or "").strip()
        if not normalized:
            raise ValueError("Folder name must not be empty")
        if parent_id is not None:
            await self._require_folder(parent_id)
        folder = {
            "id": str(uuid4()),
            "name": normalized,
            "description": description,
            "user_id": user_id,
            "parent_id": parent_id,
            "icon": icon,
            "order": order,
            "metadata": dict(metadata or {}),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        await self._store.save(_DOMAIN_FOLDERS, folder["id"], folder)
        await self._publish(
            EventType.FOLDER_CREATED, "folder.created", {"folder": folder}
        )
        return folder

    async def get_folder(self, folder_id: str) -> dict[str, Any] | None:
        return await self._store.get(_DOMAIN_FOLDERS, folder_id)

    async def list_folders(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """Liste plate des dossiers (ordre : ``order`` puis ``name``)."""
        folders = await self._store.list(_DOMAIN_FOLDERS)
        if user_id is not None:
            folders = [f for f in folders if f.get("user_id") == user_id]
        return sorted(
            folders, key=lambda f: (f.get("order", 0), f.get("name", ""))
        )

    async def rename_folder(self, folder_id: str, name: str) -> dict[str, Any] | None:
        """Renomme un dossier (le nom reste librement modifiable)."""
        return await self.update_folder(folder_id, name=name)

    async def update_folder(
        self,
        folder_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        icon: Any = _UNSET,
        order: int | None = None,
        parent_id: Any = _UNSET,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Mise à jour partielle : seuls les champs fournis sont modifiés.

        ``parent_id``/``icon`` utilisent la sentinelle ``_UNSET`` pour
        distinguer « non fourni » de « remettre à None » (racine/sans icône).
        """
        folder = await self.get_folder(folder_id)
        if folder is None:
            return None
        if name is not None:
            normalized = name.strip()
            if not normalized:
                raise ValueError("Folder name must not be empty")
            folder["name"] = normalized
        if description is not None:
            folder["description"] = str(description)
        if icon is not _UNSET:
            folder["icon"] = icon
        if order is not None:
            folder["order"] = int(order)
        if parent_id is not _UNSET:
            await self._validate_parent(folder_id, parent_id)
            folder["parent_id"] = parent_id
        if metadata is not None:
            folder["metadata"] = dict(metadata)
        folder["updated_at"] = _utc_now()
        await self._store.save(_DOMAIN_FOLDERS, folder_id, folder)
        await self._publish(
            EventType.FOLDER_UPDATED, "folder.updated", {"folder": folder}
        )
        return folder

    async def move_folder(
        self, folder_id: str, new_parent_id: str | None
    ) -> dict[str, Any] | None:
        """Déplace un dossier (re-parentage avec détection de cycles)."""
        return await self.update_folder(folder_id, parent_id=new_parent_id)

    async def delete_folder(self, folder_id: str) -> dict[str, Any] | None:
        """Supprime un dossier.

        Les sous-dossiers sont re-rattachés au grand-parent (aucun enfant
        orphelin) et les classements pointant vers ce dossier sont purgés.
        Les ressources classées ne sont **pas** supprimées (relation, pas
        possession) — elles redeviennent simplement sans dossier.
        """
        folder = await self.get_folder(folder_id)
        if folder is None:
            return None
        grandparent = folder.get("parent_id")
        reattached: list[str] = []
        for child in await self._store.list(_DOMAIN_FOLDERS):
            if child.get("parent_id") == folder_id:
                child["parent_id"] = grandparent
                child["updated_at"] = _utc_now()
                await self._store.save(_DOMAIN_FOLDERS, child["id"], child)
                reattached.append(child["id"])
        for membership in await self._store.list(_DOMAIN_MEMBERSHIPS):
            if membership.get("folder_id") == folder_id:
                await self._store.delete(_DOMAIN_MEMBERSHIPS, membership["id"])
        await self._store.delete(_DOMAIN_FOLDERS, folder_id)
        await self._publish(
            EventType.FOLDER_DELETED,
            "folder.deleted",
            {"folder_id": folder_id, "reattached_children": reattached},
        )
        return {"id": folder_id, "reattached_children": reattached}

    # ── Arborescence ─────────────────────────────────────────────────────

    async def list_tree(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """Arborescence ordonnée (``order`` puis ``name``).

        Les dossiers dont le parent a disparu (donnée corrompue) remontent à
        la racine : aucun record ne disparaît de la vue utilisateur.
        """
        folders = await self.list_folders(user_id)
        by_id = {f["id"] for f in folders}
        by_parent: dict[str | None, list[dict[str, Any]]] = {}
        for folder in folders:
            parent = folder.get("parent_id")
            if parent not in by_id:
                parent = None  # orphelin → racine
            by_parent.setdefault(parent, []).append(folder)

        counts = await self._resource_counts()

        def build(folder: dict[str, Any]) -> dict[str, Any]:
            node = dict(folder)
            node["resource_count"] = counts.get(folder["id"], 0)
            node["children"] = [
                build(child)
                for child in sorted(
                    by_parent.get(folder["id"], []),
                    key=lambda f: (f.get("order", 0), f.get("name", "")),
                )
            ]
            return node

        return [
            build(folder)
            for folder in sorted(
                by_parent.get(None, []),
                key=lambda f: (f.get("order", 0), f.get("name", "")),
            )
        ]

    async def _resource_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for membership in await self._store.list(_DOMAIN_MEMBERSHIPS):
            fid = membership.get("folder_id")
            counts[fid] = counts.get(fid, 0) + 1
        return counts

    # ── Classement des ressources (relations, jamais de duplication) ────

    async def attach_resource(
        self, folder_id: str, resource_type: str, resource_id: str
    ) -> dict[str, Any]:
        """Classe une ressource dans un dossier (idempotent).

        Une ressource peut appartenir à plusieurs dossiers ; la relation ne
        duplique aucune donnée — l'id suffit, la ressource reste possédée par
        son manager Core d'origine.  Une ressource inexistante est rejetée
        (fail-closed : jamais de relation fantôme).
        """
        await self._require_folder(folder_id)
        await self._require_resource(resource_type, resource_id)
        membership_id = _membership_id(folder_id, resource_type, resource_id)
        existing = await self._store.get(_DOMAIN_MEMBERSHIPS, membership_id)
        if existing is not None:
            return existing
        membership = {
            "id": membership_id,
            "folder_id": folder_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "created_at": _utc_now(),
        }
        await self._store.save(_DOMAIN_MEMBERSHIPS, membership_id, membership)
        await self._publish(
            EventType.FOLDER_RESOURCE_ATTACHED,
            "folder.resource.attached",
            {
                "folder_id": folder_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        return membership

    async def detach_resource(
        self, folder_id: str, resource_type: str, resource_id: str
    ) -> bool:
        """Retire une ressource d'un dossier (la ressource n'est pas supprimée)."""
        await self._require_folder(folder_id)
        deleted = await self._store.delete(
            _DOMAIN_MEMBERSHIPS, _membership_id(folder_id, resource_type, resource_id)
        )
        if deleted:
            await self._publish(
                EventType.FOLDER_RESOURCE_DETACHED,
                "folder.resource.detached",
                {
                    "folder_id": folder_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                },
            )
        return deleted

    async def move_resource(
        self, resource_type: str, resource_id: str, folder_ids: list[str]
    ) -> list[str]:
        """Définit l'ensemble des dossiers d'une ressource (remplacement).

        ``folder_ids`` vide remet la ressource **sans dossier** ; plusieurs
        dossiers sont permis (multi-membership).
        """
        if resource_type not in self._resource_types:
            raise ValueError(f"Unknown resource type: {resource_type!r}")
        await self._require_resource(resource_type, resource_id)
        target_ids: list[str] = []
        for folder_id in folder_ids:
            await self._require_folder(folder_id)
            if folder_id not in target_ids:
                target_ids.append(folder_id)
        current = {
            m["folder_id"]
            for m in await self._store.list(_DOMAIN_MEMBERSHIPS)
            if m.get("resource_type") == resource_type
            and m.get("resource_id") == resource_id
        }
        for folder_id in current - set(target_ids):
            await self.detach_resource(folder_id, resource_type, resource_id)
        for folder_id in target_ids:
            if folder_id not in current:
                await self.attach_resource(folder_id, resource_type, resource_id)
        return target_ids

    # ── Résolution (lecture déléguée aux managers Core propriétaires) ───

    async def list_resource_folders(
        self, resource_type: str, resource_id: str
    ) -> list[dict[str, Any]]:
        """Dossiers contenant une ressource donnée."""
        if resource_type not in self._resource_types:
            raise ValueError(f"Unknown resource type: {resource_type!r}")
        folders: list[dict[str, Any]] = []
        for membership in await self._store.list(_DOMAIN_MEMBERSHIPS):
            if (
                membership.get("resource_type") == resource_type
                and membership.get("resource_id") == resource_id
            ):
                folder = await self.get_folder(membership["folder_id"])
                if folder is not None:
                    folders.append(folder)
        return folders

    async def list_folder_resources(
        self, folder_id: str, resource_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Résout les ressources classées dans un dossier.

        Le contenu réel est délégué au manager Core propriétaire via le
        provider (aucune copie).  Les ressources disparues (stale) sont
        purgées du classement au passage.
        """
        await self._require_folder(folder_id)
        resolved: list[dict[str, Any]] = []
        for membership in await self._store.list(_DOMAIN_MEMBERSHIPS):
            if membership.get("folder_id") != folder_id:
                continue
            r_type = membership.get("resource_type")
            if resource_type is not None and r_type != resource_type:
                continue
            provider = self._providers.get(r_type)
            record: dict[str, Any] | None = None
            if provider is not None:
                record = _to_dict(await provider.get(membership["resource_id"]))
                if record is None:
                    # Ressource supprimée ailleurs : purge du classement stale.
                    await self._store.delete(_DOMAIN_MEMBERSHIPS, membership["id"])
                    continue
            resolved.append(
                {
                    "resource_type": r_type,
                    "resource_id": membership["resource_id"],
                    "record": record,
                }
            )
        return resolved

    async def list_untagged(self, resource_type: str) -> list[dict[str, Any]]:
        """Ressources d'un type classées dans **aucun** dossier (état par défaut)."""
        provider = self._providers.get(resource_type)
        if provider is None:
            raise ValueError(
                f"No provider registered for resource type: {resource_type!r}"
            )
        tagged = {
            m.get("resource_id")
            for m in await self._store.list(_DOMAIN_MEMBERSHIPS)
            if m.get("resource_type") == resource_type
        }
        untagged: list[dict[str, Any]] = []
        for record in await provider.list_all():
            data = _to_dict(record)
            if data and data.get("id") not in tagged:
                untagged.append(data)
        return untagged

    async def folder_index(
        self, resource_type: str | None = None
    ) -> dict[str, list[str]]:
        """Index batch ressource → dossiers (pour filtrer les listes de
        ressources par dossier côté interfaces).

        Retourne ``{resource_id: [folder_id, ...]}`` ; les ressources sans
        dossier n'y apparaissent pas.  Lecture pure : aucune duplication.
        """
        if resource_type is not None and resource_type not in self._resource_types:
            raise ValueError(f"Unknown resource type: {resource_type!r}")
        index: dict[str, list[str]] = {}
        for membership in await self._store.list(_DOMAIN_MEMBERSHIPS):
            if (
                resource_type is not None
                and membership.get("resource_type") != resource_type
            ):
                continue
            index.setdefault(membership["resource_id"], []).append(
                membership["folder_id"]
            )
        return index

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _require_folder(self, folder_id: str) -> dict[str, Any]:
        folder = await self.get_folder(folder_id)
        if folder is None:
            raise ValueError(f"Folder {folder_id} not found")
        return folder

    async def _require_resource(self, resource_type: str, resource_id: str) -> None:
        if resource_type not in self._resource_types:
            raise ValueError(f"Unknown resource type: {resource_type!r}")
        provider = self._providers.get(resource_type)
        if provider is None:
            # Pas de résolveur : l'existence reste de la responsabilité du
            # domaine propriétaire (registre ouvert sans provider obligatoire).
            return
        if _to_dict(await provider.get(resource_id)) is None:
            raise ValueError(f"{resource_type} {resource_id} not found")

    async def _validate_parent(self, folder_id: str, parent_id: str | None) -> None:
        if parent_id is None:
            return
        if parent_id == folder_id:
            raise ValueError("A folder cannot be its own parent")
        await self._require_folder(parent_id)
        descendants = await self._descendant_ids(folder_id)
        if parent_id in descendants:
            raise ValueError(
                f"Cannot move folder {folder_id} under its own descendant {parent_id}"
            )

    async def _descendant_ids(self, folder_id: str) -> set[str]:
        by_parent: dict[str | None, list[str]] = {}
        for folder in await self._store.list(_DOMAIN_FOLDERS):
            by_parent.setdefault(folder.get("parent_id"), []).append(folder["id"])
        descendants: set[str] = set()
        frontier = list(by_parent.get(folder_id, []))
        while frontier:
            current = frontier.pop()
            if current in descendants:
                continue  # défensif : un store corrompu ne doit pas boucler
            descendants.add(current)
            frontier.extend(by_parent.get(current, []))
        return descendants

    async def _publish(
        self, event_type: EventType, subject: str, payload: dict[str, Any]
    ) -> None:
        if self._bus is None:
            return
        await self._bus.publish(
            subject,
            Event(type=event_type, source="folders", payload=payload),
        )


def _membership_id(folder_id: str, resource_type: str, resource_id: str) -> str:
    return f"{folder_id}:{resource_type}:{resource_id}"


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


__all__ = ["FolderManager", "FolderResourceProvider", "DEFAULT_RESOURCE_TYPES"]
