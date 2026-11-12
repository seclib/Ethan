"""Project Anchors — rattachement des connaissances et données ETHAN à un projet.

P2.8.2 — Introduction des ancrages projet.

Un *Project Anchor* identifie explicitement le projet auquel appartient une
information, **sans dupliquer son contenu** et sans modifier l'identité de
l'information elle-même.

Choix d'architecture
--------------------
Le rattachement passe par une **relation dédiée** (`core_domain_records[project-anchors]`)
et non par un champ identique ajouté à chaque modèle. Rasons :

* une connaissance, une ressource ou un événement d'ingénierie peut
  appartenir **legitimement à plusieurs projets** (un composant de code sert
  plusieurs chantiers) ;
* la relation porte sa propre provenance (qui a rattaché, quand, pourquoi) ;
* le modèle de données des cinq types concernés reste **inchangé** : aucune
  migration de schéma, aucune donnée historique réécrite, les données
  existantes restant exploitables ;
* une seule chemin de requête pour le filtrage projet et l'isolation.

Portée
------
La portée est **dérivée** des ancres, jamais stockée : un champ de portée
redondant finirait par contredire les ancres.

* ``GLOBAL``       : aucune ancre — l'information est indépendante d'un projet.
* ``PROJECT``      : exactement une ancre.
* ``MULTI_PROJECT``: plusieurs ancres.

Les données historiques, non rattachées, restent ``GLOBAL`` : aucun projet
n'est inventé, aucun rattachement n'est déduit. Un rattachement ultérieur
reste possible explicitement.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
)

from core.state.record_store import CoreRecordStore, RecordStoreUnavailable

logger = logging.getLogger(__name__)

# Domaine de persistance des ancres dans `core_domain_records`.
ANCHOR_DOMAIN = "project-anchors"

# Domaine de persistance des projets (même convention que core/projects).
PROJECT_DOMAIN = "projects"

# Namespace UUID v5 réservé aux ancres de projet.
_ANCHOR_NAMESPACE = uuid.UUID("6f5b6c8e-4a1d-5c2b-9f3e-0d7a1b2c3d4e")


class AnchorTargetType(str, Enum):
    """Types de données qui peuvent être ancrés à un projet."""

    KNOWLEDGE_NODE = "knowledge_node"
    RESOURCE = "resource"
    MEMORY_RECORD = "memory_record"
    MISSION = "mission"
    SESSION = "session"


class AnchorScope(str, Enum):
    """Portée d'une information par rapport aux projets."""

    GLOBAL = "global"
    PROJECT = "project"
    MULTI_PROJECT = "multi_project"


class TargetExistence(str, Enum):
    """Résultat de la résolution de l'existence d'une cible.

    La distinction est nécessaire : une source *non alimentée* ne prouve pas
    qu'une donnée est absente. Confondre les deux reviendrait à refuser des
    rattachements légitimes, ou — pire — à valider l'existence d'une cible
    jamais consultée.
    """

    #: La source a été consultée et la cible existe.
    VERIFIED = "verified"
    #: La source a été consultée et la cible n'existe pas.
    NOT_FOUND = "not_found"
    #: La source n'est pas accessible dans cette phase : l'existence n'a pas
    #: été établie et n'est pas prétendument établie.
    UNRESOLVABLE = "unresolvable"


@dataclass(frozen=True)
class TargetResolution:
    """Résolution de l'existence d'une cible ancrable.

    Attributes:
        existence: Verdict de la résolution.
        reason: Motif lisible (source non alimentée, domaine absent, ...).
        source: Source interrogée, pour le diagnostic.
    """

    existence: TargetExistence
    reason: str = ""
    source: str = ""

    @property
    def verified(self) -> bool:
        """Indique si l'existence de la cible a été établie."""
        return self.existence is TargetExistence.VERIFIED

    @classmethod
    def found(cls, source: str = "") -> "TargetResolution":
        """La cible existe."""
        return cls(TargetExistence.VERIFIED, "target found in its source", source)

    @classmethod
    def missing(cls, source: str = "") -> "TargetResolution":
        """La source a été consultée : la cible n'existe pas."""
        return cls(TargetExistence.NOT_FOUND, "target not found in its source", source)

    @classmethod
    def unresolvable(cls, reason: str, source: str = "") -> "TargetResolution":
        """La source n'est pas accessible : l'existence reste inconnue."""
        return cls(TargetExistence.UNRESOLVABLE, reason, source)


@dataclass(frozen=True)
class TargetInventory:
    """Inventaire des cibles existantes d'un type de données.

    Attributes:
        target_type: Type de données inventorié.
        existence: État de l'inventaire (`VERIFIED` si la source a été
            consultée, `UNRESOLVABLE` si elle n'est pas accessible).
        ids: Identifiants trouvés (vide si l'inventaire est indisponible).
        reason: Motif de l'indisponibilité, le cas échéant.
        source: Source interrogée.
    """

    target_type: AnchorTargetType
    existence: TargetExistence
    ids: Sequence[str] = ()
    reason: str = ""
    source: str = ""

    @property
    def available(self) -> bool:
        """Indique si l'inventaire a réellement pu être établi."""
        return self.existence is not TargetExistence.UNRESOLVABLE

    @property
    def is_empty(self) -> bool:
        """Indique que la source est accessible et ne contient aucune cible."""
        return self.available and not list(self.ids)


# Catégories de données dont l'appartenance à un projet est **exclusive** :
# une session d'agent ou un chantier appartient à un seul projet. Les autres
# catégories (connaissances, ressources, événements d'ingénierie) sont
# partageables par nature.
EXCLUSIVE_TARGET_TYPES: frozenset[AnchorTargetType] = frozenset(
    {AnchorTargetType.MISSION, AnchorTargetType.SESSION}
)

# Domaine du store partagé qui porte la **véritable source** de chaque type
# de données. Un type absent de cette table n'a pas de source exploitable
# dans le store : son inventaire et l'existence de ses cibles ne peuvent
# être établis que par un résolveur injecté.
#
# - `knowledge` : `KnowledgeManager._DOMAIN`
# - `resources` : `core/resources/repository.py` (`RESOURCE_DOMAIN`)
# - `missions`  : `core/missions/manager.py` (`MissionManager._DOMAIN`)
# - documents d'ingénierie : corpus documentaire (Engineering Memory) —
#   hors store, résolveur injectable
# - sessions archivées : non persistées dans cette phase (P2.8.7)
_STORE_DOMAIN_BY_TYPE: Dict[AnchorTargetType, str] = {
    AnchorTargetType.KNOWLEDGE_NODE: "knowledge",
    AnchorTargetType.RESOURCE: "resources",
    AnchorTargetType.MISSION: "missions",
}


def _utc_now() -> str:
    """Horodatage ISO-8601 UTC, format commun aux services Core."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _anchor_id(target_type: AnchorTargetType | str, target_id: str, project_id: str) -> str:
    """Calcule l'identifiant déterministe d'une ancre.

    L'identifiant ne dépend que du triplet (type, cible, projet) : un rattachement
    répété produit la même ancre, ce qui rend l'opération idempotente.

    Args:
        target_type: Type de la donnée ancrée.
        target_id: Identifiant de la donnée ancrée.
        project_id: Identifiant du projet.

    Returns:
        Identifiant stable au format UUIDv5.
    """
    kind = target_type.value if isinstance(target_type, AnchorTargetType) else str(target_type)
    key = f"{kind}:{target_id}:{project_id}"
    return str(uuid.uuid5(_ANCHOR_NAMESPACE, key))


@dataclass(frozen=True)
class ProjectAnchor:
    """Ancre de rattachement entre une donnée ETHAN et un projet.

    L'ancre est une **relation** : elle ne contient jamais le contenu de la
    donnée ancrée, seulement son adresse et sa provenance de rattachement.

    Historique
    ----------
    Les cycles de rattachement sont conservés dans ``history`` : chaque
    cycle porte sa date de rattachement, son auteur, ses métadonnées, sa
    date de détachement et le verdict de résolution de l'existence de la
    cible. Un état courant seul ne permettrait pas de reconstituer une
    succession rattachement → détachement → rattachement, et la
    réactivation écraserait silencieusement les métadonnées d'origine.
    """

    anchor_id: str
    target_type: AnchorTargetType
    target_id: str
    project_id: str
    created_at: str = ""
    actor: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    detached_at: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Indique si le rattachement est actif."""
        return self.detached_at is None

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'ancre pour la persistance."""
        return {
            "anchor_id": self.anchor_id,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "actor": self.actor,
            "metadata": dict(self.metadata),
            "detached_at": self.detached_at,
            "history": [dict(cycle) for cycle in self.history],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectAnchor":
        """Reconstitue une ancre depuis sa forme persistée.

        Rétrocompatible : une ancre antérieure à l'historique des cycles
        (sans champ ``history``) est reconstituée avec un cycle implicite
        dérivé de son état courant, afin que l'historique ne perde pas
        l'information déjà portée par ``created_at`` / ``actor`` /
        ``metadata`` / ``detached_at``.

        Args:
            data: Dictionnaire persisté.

        Returns:
            Ancre reconstituée.
        """
        history = [dict(cycle) for cycle in (data.get("history") or [])]
        if not history:
            history = [
                {
                    "attached_at": str(data.get("created_at", "")),
                    "actor": str(data.get("actor", "")),
                    "metadata": dict(data.get("metadata") or {}),
                    "detached_at": data.get("detached_at"),
                    "target_existence": str(
                        (data.get("metadata") or {}).get("target_existence", "")
                    ),
                }
            ]
        return cls(
            anchor_id=str(data.get("anchor_id", "")),
            target_type=AnchorTargetType(data.get("target_type", "knowledge_node")),
            target_id=str(data.get("target_id", "")),
            project_id=str(data.get("project_id", "")),
            created_at=str(data.get("created_at", "")),
            actor=str(data.get("actor", "")),
            metadata=dict(data.get("metadata") or {}),
            detached_at=data.get("detached_at"),
            history=history,
        )


class ProjectAnchorError(ValueError):
    """Règle métier d'ancrage violée."""


class ProjectAnchorStoreUnavailable(RuntimeError):
    """Le store de persistance est indisponible.

    Distinct de `ProjectAnchorError` : une panne technique ne doit **jamais**
    être transformée en « projet introuvable ». L'appelant doit pouvoir
    distinguer une règle métier violée d'une infrastructure défaillante —
    la première est une erreur du client (422), la seconde une erreur
    serveur (503).
    """


class ProjectAnchorService:
    """Gestion des ancrages projet — Core-owned.

    Toute la logique métier d'ancrage vit ici. Les interfaces (API, CLI,
    WebUI) délèguent sans jamais réécrire les règles.

    Args:
        store: Store Core partagé (PostgreSQL + cache Redis en production).
        project_resolver: Résolveur optionnel d'existence de projet. Par
            défaut, la lecture se fait dans le domaine `projects` du store
            partagé — le même que celui utilisé par `ProjectManager`.
        target_resolvers: Résolveurs d'existence de cible, par type. Un
            type absent de cette table n'a pas de source exploitable dans
            cette phase : l'existence de la cible ne sera **pas** validée,
            et l'ancre consigne explicitement ce verdict.
    """

    def __init__(
        self,
        store: CoreRecordStore | None = None,
        *,
        project_resolver: Callable[[str], Awaitable[Optional[Dict[str, Any]]]] | None = None,
        target_resolvers: Optional[
            Dict[AnchorTargetType, Callable[[str], Awaitable[TargetResolution]]]
        ] = None,
    ) -> None:
        self._store = store or CoreRecordStore()
        self._project_resolver = project_resolver
        self._target_resolvers = dict(target_resolvers or {})

    # -- Validation des identifiants ------------------------------------

    @staticmethod
    def _normalize_target_type(target_type: AnchorTargetType | str) -> AnchorTargetType:
        """Valide et normalise un type de cible.

        Args:
            target_type: Type fourni.

        Returns:
            Type normalisé.

        Raises:
            ProjectAnchorError: Si le type est inconnu.
        """
        try:
            return AnchorTargetType(target_type)
        except ValueError as exc:
            raise ProjectAnchorError(f"unknown target_type: {target_type}") from exc

    @staticmethod
    def _normalize_identifier(value: str, field: str) -> str:
        """Valide et normalise un identifiant canonique.

        La normalisation se limite au **bord** (espaces et tabulations) : un
        identifiant valide n'est jamais réécrit dans son fond. La cohérence
        entre `attach()` et `detach()` est essentielle : sans elle, la même
        donnéeAnchorée sous deux graphies produirait deux ancres distinctes.

        Args:
            value: Identifiant fourni.
            field: Nom du champ (pour le message d'erreur).

        Returns:
            Identifiant normalisé.

        Raises:
            ProjectAnchorError: Si l'identifiant est vide.
        """
        if value is None:
            raise ProjectAnchorError(f"{field} must not be empty")
        normalized = str(value).strip()
        if not normalized:
            raise ProjectAnchorError(f"{field} must not be empty")
        return normalized

    def _validate_identifiers(
        self,
        target_type: AnchorTargetType | str,
        target_id: str,
        project_id: str,
    ) -> tuple[AnchorTargetType, str, str]:
        """Valide les trois identifiants d'un rattachement.

        Args:
            target_type: Type de la donnée.
            target_id: Identifiant de la donnée.
            project_id: Identifiant du projet.

        Returns:
            Le triplet normalisé.

        Raises:
            ProjectAnchorError: Si l'un des identifiants est invalide.
        """
        kind = self._normalize_target_type(target_type)
        return (
            kind,
            self._normalize_identifier(target_id, "target_id"),
            self._normalize_identifier(project_id, "project_id"),
        )

    # -- Existence et validité du projet ------------------------------

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retourne le projet bracketing, ou None.

        Une panne du store est signalée comme telle : elle ne doit pas se
        déguiser en « projet absent ».

        Args:
            project_id: Identifiant du projet.

        Returns:
            Le projet, ou None s'il n'existe pas.

        Raises:
            ProjectAnchorStoreUnavailable: Si le store est inaccessible.
        """
        if not project_id or not project_id.strip():
            return None
        if self._project_resolver is not None:
            try:
                return await self._project_resolver(project_id)
            except ProjectAnchorStoreUnavailable:
                raise
            except Exception as exc:
                raise ProjectAnchorStoreUnavailable(
                    f"project resolution failed for {project_id}: {exc}"
                ) from exc
        try:
            return await self._store.get_strict(PROJECT_DOMAIN, project_id)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc

    async def validate_project(self, project_id: str) -> Dict[str, Any]:
        """Valide qu'un projet existe et peut recevoir un ancrage.

        Un projet inactif est refusé pour un **nouveau** rattachement ; les
        ancres déjà posées vers ce projet restent valides et résolubles.

        Args:
            project_id: Identifiant du projet.

        Returns:
            Le projet validé.

        Raises:
            ProjectAnchorError: Si le projet n'existe pas ou est inactif.
            ProjectAnchorStoreUnavailable: Si le store est inaccessible.
        """
        if not project_id or not project_id.strip():
            raise ProjectAnchorError("project_id must not be empty")
        project = await self.get_project(project_id)
        if project is None:
            raise ProjectAnchorError(f"Project not found: {project_id}")
        if project.get("is_active") is False:
            raise ProjectAnchorError(f"Project is inactive: {project_id}")
        return project

    # -- Existence des cibles -------------------------------------------

    async def resolve_target(
        self, target_type: AnchorTargetType | str, target_id: str
    ) -> TargetResolution:
        """Détermine si une cible existe réellement.

        La résolution s'appuie sur la **véritable source** de chaque type de
        données. Aucun identifiant n'est inventé, et une cible n'est jamais
        considérée comme existante au seul motif qu'une chaîne non vide a
        été fournie.

        Deux stratégies cohabitent :

        * les types dont la source est le store partagé (connaissances,
          ressources, missions) sont vérifiés dans leur domaine ; un domaine
          **alimenté** qui ne contient pas la cible signifie « cible
          inexistante » ; un domaine **vide** signifie « source non
          alimentée », donc existence non vérifiable ;
        * les types dont la source n'est pas dans le store (documents
          d'ingénierie, sessions archivées) ne sont validés que si un
          résolveur a été injecté ; sinon l'existence reste **non établie**
          et l'ancre le consigne.

        Args:
            target_type: Type de la donnée.
            target_id: Identifiant de la donnée.

        Returns:
            Verdict de résolution.
        """
        kind = self._normalize_target_type(target_type)
        resolver = self._target_resolvers.get(kind)
        if resolver is not None:
            try:
                resolution = await resolver(target_id)
            except ProjectAnchorStoreUnavailable:
                raise
            except Exception as exc:
                raise ProjectAnchorStoreUnavailable(
                    f"target resolution failed for {kind.value}/{target_id}: {exc}"
                ) from exc
            if not isinstance(resolution, TargetResolution):
                return TargetResolution.unresolvable(
                    "resolver returned an unexpected result", kind.value
                )
            return resolution

        domain = _STORE_DOMAIN_BY_TYPE.get(kind)
        if domain is None:
            return TargetResolution.unresolvable(
                f"no source of truth available for {kind.value} in this phase", kind.value
            )
        try:
            rows = await self._store.list_strict(domain)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc
        if not rows:
            # Domaine non alimenté : l'absence de la cible ne prouve rien.
            return TargetResolution.unresolvable(
                f"source domain '{domain}' is not populated", domain
            )
        identifiers = {str(row.get("id") or row.get("stable_id") or "") for row in rows}
        identifiers.discard("")
        if target_id in identifiers:
            return TargetResolution.found(domain)
        return TargetResolution.missing(domain)

    async def inventory(self, target_type: AnchorTargetType | str) -> TargetInventory:
        """Inventorie les cibles existantes d'un type de données.

        L'inventaire distingue explicitement une liste **réellement vide**
        d'une source **inaccessible** : renvoyer une liste vide dans les
        deux cas ferait croire à tort qu'aucune donnée n'existe.

        Args:
            target_type: Type de données.

        Returns:
            Inventaire avec son état de disponibilité.
        """
        kind = self._normalize_target_type(target_type)
        domain = _STORE_DOMAIN_BY_TYPE.get(kind)
        if domain is None:
            return TargetInventory(
                target_type=kind,
                existence=TargetExistence.UNRESOLVABLE,
                reason=f"no source of truth available for {kind.value} in this phase",
                source=kind.value,
            )
        try:
            rows = await self._store.list_strict(domain)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc
        if not rows:
            return TargetInventory(
                target_type=kind,
                existence=TargetExistence.UNRESOLVABLE,
                reason=f"source domain '{domain}' is not populated",
                source=domain,
            )
        identifiers: Set[str] = set()
        for row in rows:
            identifier = str(row.get("id") or row.get("stable_id") or "")
            if identifier:
                identifiers.add(identifier)
        return TargetInventory(
            target_type=kind,
            existence=TargetExistence.VERIFIED,
            ids=sorted(identifiers),
            source=domain,
        )


    # -- Écriture ------------------------------------------------------

    async def attach(
        self,
        target_type: AnchorTargetType | str,
        target_id: str,
        project_id: str,
        *,
        actor: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProjectAnchor:
        """Rattache une donnée à un projet.

        L'opération est **idempotente** : rattacher deux fois la même donnée au
        même projet ne crée pas de seconde ancre.

        L'exclusivité est garantie **dans tous les chemins** — création,
        réactivation d'une ancre détachée, rattachement répété — et la
        vérification comme l'écriture se font dans une **section critique**
        : un simple contrôle suivi d'un `save()` laisserait deux
        rattachements concurrents d'une cible exclusive passer tous deux.

        L'existence de la cible est résolue auprès de sa vraie source. Si
        cette source n'est pas accessible dans cette phase, l'ancre consigne
        explicitement que l'existence **n'a pas été établie** — elle ne
        prétend pas l'avoir vérifiée.

        Args:
            target_type: Type de la donnée à ancrer.
            target_id: Identifiant de la donnée à ancrer.
            project_id: Identifiant du projet cible.
            actor: Auteur ou composant producteur du rattachement.
            metadata: Métadonnées libres du rattachement (origine, motif).

        Returns:
            L'ancre créée ou retrouvée.

        Raises:
            ProjectAnchorError: Si un identifiant est invalide, si le projet
                est inconnu ou inactif, si la cible n'existe pas, ou si la
                cible appartient à une catégorie exclusive déjà rattachée
                ailleurs.
            ProjectAnchorStoreUnavailable: Si le store est inaccessible.
        """
        kind, canonical_target_id, canonical_project_id = self._validate_identifiers(
            target_type, target_id, project_id
        )

        await self.validate_project(canonical_project_id)
        resolution = await self.resolve_target(kind, canonical_target_id)
        if resolution.existence is TargetExistence.NOT_FOUND:
            # La source a été consultée : la cible n'existe pas. Rattacher
            # une cible inexistante créerait une relation vers rien.
            raise ProjectAnchorError(f"Target not found: {canonical_target_id}")

        anchor_id = _anchor_id(kind, canonical_target_id, canonical_project_id)
        guard = f"project-anchor:{kind.value}:{canonical_target_id}"

        async with self._atomic(guard):
            existing = await self._store.get_strict(ANCHOR_DOMAIN, anchor_id)
            if existing is not None:
                anchor = ProjectAnchor.from_dict(existing)
                if anchor.is_active:
                    return anchor
                # Ancre détachée : elle est réactivée, mais **après** avoir
                # vérifié l'exclusivité — une ancre détachée ne doit jamais
                # revenir active si une autre ancre exclusive l'a déjà
                # prise pour un autre projet.
                await self._assert_exclusive_available(
                    kind, canonical_target_id, canonical_project_id
                )
                anchor = self._reactivated(anchor, kind, actor, metadata, resolution)
                await self._save(anchor)
                logger.info(
                    "Ancrage réactivé : %s %s -> projet %s (%s)",
                    kind.value,
                    canonical_target_id,
                    canonical_project_id,
                    anchor.anchor_id,
                )
                return anchor

            if kind in EXCLUSIVE_TARGET_TYPES:
                await self._assert_exclusive_available(
                    kind, canonical_target_id, canonical_project_id
                )

            anchor = ProjectAnchor(
                anchor_id=anchor_id,
                target_type=kind,
                target_id=canonical_target_id,
                project_id=canonical_project_id,
                created_at=_utc_now(),
                actor=actor,
                metadata=dict(metadata or {}),
                history=[
                    {
                        "attached_at": _utc_now(),
                        "actor": actor,
                        "metadata": dict(metadata or {}),
                        "detached_at": None,
                        "target_existence": resolution.existence.value,
                        "target_existence_reason": resolution.reason,
                    }
                ],
            )
            await self._save(anchor)
            logger.info(
                "Ancrage créé : %s %s -> projet %s (%s)",
                kind.value,
                canonical_target_id,
                canonical_project_id,
                anchor_id,
            )
            return anchor

    async def detach(
        self,
        target_type: AnchorTargetType | str,
        target_id: str,
        project_id: str,
        *,
        actor: str = "",
    ) -> bool:
        """Détache une donnée d'un projet sans supprimer la donnée elle-même.

        L'ancre est marquée détachée : l'historique du rattachement est
        conservé, cycle après cycle.

        Args:
            target_type: Type de la donnée.
            target_id: Identifiant de la donnée.
            project_id: Identifiant du projet.
            actor: Auteur du détachement (conservé dans l'historique).

        Returns:
            True si une ancre active a été détachée.

        Raises:
            ProjectAnchorError: Si un identifiant est invalide.
            ProjectAnchorStoreUnavailable: Si le store est inaccessible.
        """
        kind, canonical_target_id, canonical_project_id = self._validate_identifiers(
            target_type, target_id, project_id
        )
        anchor_id = _anchor_id(kind, canonical_target_id, canonical_project_id)
        guard = f"project-anchor:{kind.value}:{canonical_target_id}"

        async with self._atomic(guard):
            existing = await self._store.get_strict(ANCHOR_DOMAIN, anchor_id)
            if existing is None:
                return False
            anchor = ProjectAnchor.from_dict(existing)
            if not anchor.is_active:
                return False
            detached_at = _utc_now()
            history = [dict(cycle) for cycle in anchor.history]
            if history:
                history[-1] = {**history[-1], "detached_at": detached_at, "detached_by": actor}
            else:  # pragma: no cover - ancre sans cycle (donnée ancienne)
                history = [
                    {
                        "attached_at": anchor.created_at,
                        "actor": anchor.actor,
                        "metadata": dict(anchor.metadata),
                        "detached_at": detached_at,
                        "detached_by": actor,
                    }
                ]
            anchor = ProjectAnchor(
                anchor_id=anchor.anchor_id,
                target_type=anchor.target_type,
                target_id=anchor.target_id,
                project_id=anchor.project_id,
                created_at=anchor.created_at,
                actor=anchor.actor,
                metadata=anchor.metadata,
                detached_at=detached_at,
                history=history,
            )
            await self._save(anchor)
            logger.info(
                "Ancrage détaché : %s %s <- projet %s", kind.value, canonical_target_id, canonical_project_id
            )
            return True

    # -- Lecture -------------------------------------------------------

    async def anchors_for(
        self,
        target_type: AnchorTargetType | str,
        target_id: str,
        *,
        include_detached: bool = False,
    ) -> List[ProjectAnchor]:
        """Retourne les ancres d'une donnée.

        Args:
            target_type: Type de la donnée.
            target_id: Identifiant de la donnée.
            include_detached: Inclut les ancres détachées (historique).

        Returns:
            Liste des ancres.

        Raises:
            ProjectAnchorError: Si le type est inconnu.
            ProjectAnchorStoreUnavailable: Si le store est inaccessible.
        """
        kind = self._normalize_target_type(target_type)
        found: List[ProjectAnchor] = []
        try:
            rows = await self._store.list_strict(ANCHOR_DOMAIN)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc
        for raw in rows:
            anchor = ProjectAnchor.from_dict(raw)
            if anchor.target_type != kind or anchor.target_id != target_id:
                continue
            if not anchor.is_active and not include_detached:
                continue
            found.append(anchor)
        return sorted(found, key=lambda a: (a.project_id, a.anchor_id))

    async def scope_for(
        self, target_type: AnchorTargetType | str, target_id: str
    ) -> AnchorScope:
        """Détermine la portée d'une donnée par rapport aux projets.

        La portée est **dérivée** des ancres actives : elle ne peut pas
        contredire les relations.

        Args:
            target_type: Type de la donnée.
            target_id: Identifiant de la donnée.

        Returns:
            Portée calculée.
        """
        anchors = await self.anchors_for(target_type, target_id)
        if not anchors:
            return AnchorScope.GLOBAL
        if len(anchors) == 1:
            return AnchorScope.PROJECT
        return AnchorScope.MULTI_PROJECT

    async def projects_for(
        self, target_type: AnchorTargetType | str, target_id: str
    ) -> List[str]:
        """Retourne les projets auxquels une donnée est rattachée.

        Args:
            target_type: Type de la donnée.
            target_id: Identifiant de la donnée.

        Returns:
            Liste des identifiants de projet.
        """
        return [a.project_id for a in await self.anchors_for(target_type, target_id)]

    async def targets_for_project(
        self,
        project_id: str,
        target_type: AnchorTargetType | str | None = None,
    ) -> List[str]:
        """Retourne les identifiants de données ancrées à un projet.

        Args:
            project_id: Identifiant du projet.
            target_type: Restriction facultative à un type de données.

        Returns:
            Liste des identifiants de données.
        """
        wanted = self._normalize_target_type(target_type) if target_type is not None else None
        found: List[str] = []
        try:
            rows = await self._store.list_strict(ANCHOR_DOMAIN)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc
        for raw in rows:
            anchor = ProjectAnchor.from_dict(raw)
            if not anchor.is_active or anchor.project_id != project_id:
                continue
            if wanted is not None and anchor.target_type != wanted:
                continue
            found.append(anchor.target_id)
        return sorted(set(found))

    async def global_targets(self, target_type: AnchorTargetType | str) -> List[str]:
        """Retourne les données d'un type qui ne sont rattachées à aucun projet.

        Ces données sont de portée ``GLOBAL`` : elles ne dépendent d'aucun
        projet et restent accessibles partout.

        Args:
            target_type: Type de données.

        Returns:
            Liste des identifiants globaux.

        Raises:
            ProjectAnchorError: Si l'inventaire de la source est indisponible.
                Une liste vide ne doit pas signifier « aucune donnée » quand
                la source n'a pas pu être consultée.
        """
        inventory = await self.inventory(target_type)
        if not inventory.available:
            raise ProjectAnchorError(
                f"inventory for {inventory.target_type.value} is unavailable: "
                f"{inventory.reason}"
            )
        anchored: Set[str] = set()
        try:
            rows = await self._store.list_strict(ANCHOR_DOMAIN)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc
        for raw in rows:
            anchor = ProjectAnchor.from_dict(raw)
            if anchor.target_type == inventory.target_type and anchor.is_active:
                anchored.add(anchor.target_id)
        return sorted(cid for cid in inventory.ids if cid not in anchored)

    async def global_inventory(self, target_type: AnchorTargetType | str) -> Dict[str, Any]:
        """Décrit l'inventaire global d'un type, avec son état de disponibilité.

        unlike `global_targets`, cette méthode **ne lève pas** : elle
        expose la distinction entre une liste réellement vide et un
        inventaire indisponible, afin que l'interface puisse la restituer
        telle quelle au client.

        Args:
            target_type: Type de données.

        Returns:
            Description de l'inventaire.
        """
        inventory = await self.inventory(target_type)
        if not inventory.available:
            return {
                "target_type": inventory.target_type.value,
                "status": "unavailable",
                "source": inventory.source,
                "reason": inventory.reason,
                "targets": [],
            }
        anchored: Set[str] = set()
        try:
            rows = await self._store.list_strict(ANCHOR_DOMAIN)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc
        for raw in rows:
            anchor = ProjectAnchor.from_dict(raw)
            if anchor.target_type == inventory.target_type and anchor.is_active:
                anchored.add(anchor.target_id)
        targets = sorted(cid for cid in inventory.ids if cid not in anchored)
        return {
            "target_type": inventory.target_type.value,
            "status": "ok",
            "source": inventory.source,
            "reason": "",
            "targets": targets,
        }

    # -- Isolation ------------------------------------------------------

    async def filter_by_project(
        self,
        candidate_ids: Iterable[str],
        project_id: str,
        target_type: AnchorTargetType | str,
        *,
        include_global: bool = True,
    ) -> List[str]:
        """Filtre des identifiants selon la portée projet.

        Règle d'isolation : un candidat **exclusif** d'un autre projet n'est
        jamais retourné. Les candidats globaux le sont si `include_global`
        est vrai. Une cible dont toutes les ancres sont détachées redevient
        globale.

        Le projet est validé avant tout filtrage : filtrer pour un projet
        inexistant ou inactif n'est pas un cas d'usage légitime, et
        l'accepter reviendrait à laisser un appelant croire à une isolation
        alors que rien n'a été vérifié.

        Args:
            candidate_ids: Identifiants candidats.
            project_id: Projet courant.
            target_type: Type des données candidates.
            include_global: Inclut les données de portée globale.

        Returns:
            Liste des identifiants accessibles dans le projet.

        Raises:
            ProjectAnchorError: Si le projet est inconnu ou inactif.
            ProjectAnchorStoreUnavailable: Si le store est inaccessible.
        """
        kind = self._normalize_target_type(target_type)
        canonical_project_id = self._normalize_identifier(project_id, "project_id")
        await self.validate_project(canonical_project_id)

        wanted = {str(candidate) for candidate in candidate_ids}
        index = await self._active_anchor_index()
        allowed: List[str] = []
        for candidate in sorted(wanted):
            anchors = index.get((kind, candidate), [])
            if not anchors:
                if include_global:
                    allowed.append(candidate)
                continue
            if any(anchor.project_id == canonical_project_id for anchor in anchors):
                allowed.append(candidate)
        return allowed

    # -- Internes ------------------------------------------------------

    @asynccontextmanager
    async def _atomic(self, guard: str) -> AsyncIterator[None]:
        """Ouvre une section critique sérialisée par clé de garde.

        Args:
            guard: Clé de garde.

        Yields:
            None, à l'intérieur de la section critique.

        Raises:
            ProjectAnchorStoreUnavailable: Si la section est indisponible.
        """
        try:
            async with self._store.atomic(guard):
                yield
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc

    async def _save(self, anchor: ProjectAnchor) -> None:
        """Persiste une ancre, sans masquer un échec d'écriture.

        Args:
            anchor: Ancre à écrire.

        Raises:
            ProjectAnchorStoreUnavailable: Si l'écriture a échoué.
        """
        try:
            await self._store.save_strict(ANCHOR_DOMAIN, anchor.anchor_id, anchor.to_dict())
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc

    async def _assert_exclusive_available(
        self,
        kind: AnchorTargetType,
        target_id: str,
        project_id: str,
    ) -> None:
        """Vérifie qu'une cible exclusive est libre pour un projet.

        La vérification est faite **dans la section critique** appelante :
        elle est donc atomique avec l'écriture qui suit.

        Args:
            kind: Type de la donnée.
            target_id: Identifiant de la donnée.
            project_id: Projet visé.

        Raises:
            ProjectAnchorError: Si un autre projet possède déjà la cible.
        """
        if kind not in EXCLUSIVE_TARGET_TYPES:
            return
        others = await self._other_active_projects(kind, target_id, project_id)
        if others:
            raise ProjectAnchorError(
                f"{kind.value} is exclusive and already anchored to project(s): "
                f"{', '.join(sorted(others))}"
            )

    def _reactivated(
        self,
        anchor: ProjectAnchor,
        kind: AnchorTargetType,
        actor: str,
        metadata: Optional[Dict[str, Any]],
        resolution: TargetResolution,
    ) -> ProjectAnchor:
        """Construit l'ancre réactivée, sans perdre l'historique.

        Le cycle détaché est conservé tel quel ; un nouveau cycle est ajouté.
        Les métadonnées d'origine restent accessibles dans l'historique, même
        si le cycle courant en porte d'autres.

        Args:
            anchor: Ancre détachée d'origine.
            kind: Type de la donnée.
            actor: Auteur de la réactivation.
            metadata: Métadonnées du nouveau cycle.
            resolution: Verdict de résolution de l'existence de la cible.

        Returns:
            Ancre réactivée.
        """
        history = [dict(cycle) for cycle in anchor.history]
        history.append(
            {
                "attached_at": _utc_now(),
                "actor": actor or anchor.actor,
                "metadata": dict(metadata or {}),
                "detached_at": None,
                "target_existence": resolution.existence.value,
                "target_existence_reason": resolution.reason,
            }
        )
        return ProjectAnchor(
            anchor_id=anchor.anchor_id,
            target_type=kind,
            target_id=anchor.target_id,
            project_id=anchor.project_id,
            created_at=anchor.created_at or _utc_now(),
            actor=actor or anchor.actor,
            metadata=dict(anchor.metadata),
            detached_at=None,
            history=history,
        )

    async def _active_anchor_index(self) -> Dict[tuple[AnchorTargetType, str], List[ProjectAnchor]]:
        """Indexe les ancres actives par (type, cible) en une seule lecture.

        Sans cet index, un filtrage de N candidats déclenchait N lectures
        complètes du domaine : le coût était quadratique.

        Returns:
            Index des ancres actives.

        Raises:
            ProjectAnchorStoreUnavailable: Si le store est inaccessible.
        """
        index: Dict[tuple[AnchorTargetType, str], List[ProjectAnchor]] = {}
        try:
            rows = await self._store.list_strict(ANCHOR_DOMAIN)
        except RecordStoreUnavailable as exc:
            raise ProjectAnchorStoreUnavailable(str(exc)) from exc
        for raw in rows:
            anchor = ProjectAnchor.from_dict(raw)
            if not anchor.is_active:
                continue
            index.setdefault((anchor.target_type, anchor.target_id), []).append(anchor)
        return index

    async def _other_active_projects(
        self,
        kind: AnchorTargetType,
        target_id: str,
        exclude_project_id: str,
    ) -> Set[str]:
        """Retourne les projets actifs d'une donnée exclusive, hors projet donné."""
        others: Set[str] = set()
        for anchor in await self.anchors_for(kind, target_id):
            if anchor.project_id != exclude_project_id:
                others.add(anchor.project_id)
        return others


def build_memory_record_resolver(
    engineering_memory: Any,
) -> Callable[[str], Awaitable[TargetResolution]]:
    """Construit un résolveur d'existence pour les documents d'ingénierie.

    La source de vérité des `MemoryRecord` est le **corpus documentaire**
    (vault de l'Engineering Memory), pas le store de records : le résolveur
    interroge cette source réelle au lieu de supposer l'existence d'une
    cible.

    La lecture du vault est un parcours de fichiers : elle est exécutée dans
    un thread pour ne pas bloquer la boucle événementielle de l'API.

    Args:
        engineering_memory: Service Engineering Memory (duck-typed : seule la
            méthode `get(record_id)` est utilisée).

    Returns:
        Résolveur asynchrone utilisable par `ProjectAnchorService`.
    """

    async def _resolve(target_id: str) -> TargetResolution:
        import asyncio

        try:
            record = await asyncio.to_thread(engineering_memory.get, target_id)
        except Exception as exc:  # pragma: no cover - garde-fou
            return TargetResolution.unresolvable(
                f"engineering memory read failed: {exc}", "engineering-memory"
            )
        if record is None:
            return TargetResolution.missing("engineering-memory")
        return TargetResolution.found("engineering-memory")

    return _resolve


__all__ = [
    "ANCHOR_DOMAIN",
    "AnchorScope",
    "AnchorTargetType",
    "EXCLUSIVE_TARGET_TYPES",
    "ProjectAnchor",
    "ProjectAnchorError",
    "ProjectAnchorService",
    "ProjectAnchorStoreUnavailable",
    "TargetExistence",
    "TargetInventory",
    "TargetResolution",
    "build_memory_record_resolver",
]
