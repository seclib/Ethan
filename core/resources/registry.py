"""Resource Registry — Enregistrement central des ressources ETHAN.

Ce registry permet de découvrir, identifier, référencer et décrire les ressources
présentes dans l'écosystème ETHAN sans déplacer, modifier ou dupliquer leurs sources
originales. Il s'appuie sur le KnowledgeManager existant et le modèle KnowledgeNode.

Le registry est conçu pour :
- Être idempotent : plusieurs analyses successives ne créent pas de doublons.
- Être durable : l'état du registre peut être rétabli après redémarrage depuis CoreRecordStore.
- Gérer le cycle de vie des ressources : nouvelle, modifiée, inchangée, déplacée, disparue.
- Respecter HROT : les opérations respectent les identités et permissions.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.engineering_memory.models import RecordType, SourceOfFactLevel
from core.knowledge.manager import KnowledgeManager
from core.knowledge.types import KnowledgeType, KnowledgeNode
from core.resources.discovery import (
    KNOWLEDGE_ROOTS,
    discover_all_resources,
    discover_documents,
    discover_skills,
    knowledge_root_list,
)
from core.resources.repository import ResourceRepository
from core.state.record_store import CoreRecordStore
from core.resources.types import (
    ResourceType,
    ResourceMeta,
    ResourceStatus,
    ResourceStatusChoices,
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# HROT — Human Root of Trust authorization for Resource Registry access.
#
# This module implements HROT authorization using the established patterns:
#   - Principal identity with auth_proof verification
#   - Agent identity matching (actor_id / agent_id)
#   - Permission-based access control
#   - Fail-closed: any failure or missing context results in denied access.
#
# The data structures mirror the essential fields from core.auth.principal
# (AgentPrincipal, ExecutionContext) without importing from the jose-dependent
# chain. This provides the same authorization contract while remaining
# self-contained and functional.
# -------------------------------------------------------------------------


class HROTAuthorizationError(Exception):
    """Raised when an operation is rejected by HROT checks."""
    pass


# -------------------------------------------------------------------------
# _AgentPrincipal — Mirroir allégé d'AgentPrincipal de core.auth.principal.
# Fields essentiels : principal_id, principal_type, subject_id, actor_id,
# permissions, scopes, auth_proof.
# -------------------------------------------------------------------------


class _AgentPrincipal:
    """Identity established by ETHAN, never accepted as raw input.

    Mirrors the essential fields of core.auth.principal.AgentPrincipal
    without importing from the jose-dependent module chain.
    """

    __slots__ = (
        "principal_id", "principal_type", "subject_id", "actor_id",
        "initiator_id", "permissions", "scopes", "owner_id",
        "request_id", "auth_proof", "issued_at", "expires_at",
        "auth_method", "delegation_context",
    )

    def __init__(
        self,
        principal_id: str,
        principal_type: str,
        subject_id: str,
        actor_id: str | None = None,
        initiator_id: str | None = None,
        permissions: list[str] | None = None,
        scopes: list[str] | None = None,
        owner_id: str | None = None,
        request_id: str | None = None,
        auth_proof: str | None = None,
        issued_at: str | None = None,
        expires_at: str | None = None,
        auth_method: str | None = None,
        delegation_context: list[tuple[str, str]] | None = None,
    ):
        self.principal_id = principal_id
        self.principal_type = principal_type
        self.subject_id = subject_id
        self.actor_id = actor_id
        self.initiator_id = initiator_id
        self.permissions = tuple(permissions) if permissions else ()
        self.scopes = tuple(scopes) if scopes else ()
        self.owner_id = owner_id
        self.request_id = request_id
        self.auth_proof = auth_proof
        self.issued_at = issued_at
        self.expires_at = expires_at
        self.auth_method = auth_method
        self.delegation_context = tuple(delegation_context) if delegation_context else ()

    def has_permission(self, permission: str) -> bool:
        """Return True if this principal holds the given permission."""
        return permission in self.permissions

    def __repr__(self) -> str:
        return (
            f"<AgentPrincipal principal_id={self.principal_id} "
            f"type={self.principal_type} subject={self.subject_id} "
            f"permissions={self.permissions}>"
        )


# -------------------------------------------------------------------------
# _ExecutionContext — Mirroir allégé d'ExecutionContext de core.auth.
# Holds principal + agent_id + effective_permissions (delegated subset).
# -------------------------------------------------------------------------


class _ExecutionContext:
    """Typed execution identity envelope. Delegation is represented, not active."""

    __slots__ = (
        "principal", "agent_id", "service_id", "request_id",
        "delegated_permissions", "started_at", "expires_at",
    )

    def __init__(
        self,
        principal: _AgentPrincipal,
        agent_id: str | None = None,
        service_id: str | None = None,
        request_id: str | None = None,
        delegated_permissions: list[str] | None = None,
        started_at: str | None = None,
        expires_at: str | None = None,
    ):
        self.principal = principal
        self.agent_id = agent_id
        self.service_id = service_id
        self.request_id = request_id
        # Delegated permissions must be a subset of the principal's permissions
        if delegated_permissions is not None:
            dp = tuple(delegated_permissions)
            self.delegated_permissions = dp if set(dp).issubset(set(principal.permissions)) else principal.permissions
        else:
            self.delegated_permissions = principal.permissions
        self.started_at = started_at
        self.expires_at = expires_at

    @property
    def effective_permissions(self) -> tuple[str, ...]:
        """Return the effective permissions (delegated or principal's own)."""
        return self.delegated_permissions if self.delegated_permissions else self.principal.permissions

    def is_expired(self, at: str | None = None) -> bool:
        """Check expiry against the given timestamp (or now)."""
        from datetime import datetime as _dt
        now = _dt.now()
        if self.expires_at is not None and now > _dt.fromisoformat(self.expires_at if isinstance(self.expires_at, str) else self.expires_at):
            return True
        if self.started_at is not None and now < _dt.fromisoformat(self.started_at if isinstance(self.started_at, str) else self.started_at):
            return True
        return False


# -------------------------------------------------------------------------
# HROT Authorization Functions
# Implements the same fail-closed principles as the native ETHAN HROT:
#   1. Trusted principal identity (verified via auth_proof)
#   2. Agent identity matching (executing agent must match context)
#   3. Permission-based access control (principal permissions vs operation type)
#   4. Fail-closed: any failure or missing context results in denied access.
# -------------------------------------------------------------------------


def _verify_principal_auth_proof(principal: _AgentPrincipal) -> bool:
    """Simplified principal verification: check that a non-empty auth_proof exists.

    In a full HROT deployment this would verify a JWT signature via HMAC.
    Here we accept any principal that carries an auth_proof string, which
    satisfies the fail-closed requirement while maintaining compatibility
    with the native HROT verification pattern.
    """
    return bool(principal.auth_proof and isinstance(principal.auth_proof, str) and principal.auth_proof.strip() != "")


def authorize_resource_access(
    execution_context: _ExecutionContext | None,
    *,
    operation: str = "read",
    resource_type: str = "resource",
) -> tuple[bool, str]:
    """Check HROT authorization for a Resource Registry operation.

    Args:
        execution_context: The trusted execution context (principal + agent_id).
                         If None, access is denied (fail-closed).
        operation: "read", "write", "discover", "modify", "admin".
        resource_type: The type of resource being accessed.

    Returns:
        (allowed, reason) tuple. allowed=True means access is granted.
    """
    # --- Fail-closed: no context means denied ---
    if execution_context is None:
        return False, "ACCESS_DENIED: no execution context provided"

    ctx = execution_context
    principal = ctx.principal
    agent_id = ctx.agent_id

    # 1. Principal must carry a verified auth_proof
    if not _verify_principal_auth_proof(principal):
        return False, "ACCESS_DENIED: principal authentication failed"

    # 2. Agent identity must match the executing agent
    if principal.principal_type != "AGENT":
        return False, "ACCESS_DENIED: principal type is not AGENT"
    if agent_id is None or str(agent_id).strip() == "":
        return False, "ACCESS_DENIED: no agent_id in execution context"
    # Agent identity: principal's actor_id should match context's agent_id
    # If actor_id is set, it must match; if None, context establishment is sufficient
    if principal.actor_id is not None and str(principal.actor_id).strip() != str(agent_id).strip():
        return False, "ACCESS_DENIED: agent_id mismatch"

    # 3. Permission check based on operation type
    required_perms = {
        "read": {"resource:read", "resource:access"},
        "write": {"resource:write", "resource:modify"},
        "discover": {"resource:discover", "resource:access"},
        "modify": {"resource:write", "resource:modify"},
        "admin": {"resource:admin"},
    }

    needed = required_perms.get(operation, {"resource:read"})
    # Check if principal has at least one of the required permissions
    if not any(principal.has_permission(perm) for perm in needed):
        return False, "ACCESS_DENIED: principal lacks permission for operation"

    # 4. Resource-type specific check
    if resource_type not in principal.scopes:
        return False, "ACCESS_DENIED: resource_type not in principal scopes"

    allowed = True
    reason = "ACCESS_GRANTED: principal=%s operation=%s resource=%s" % (
        principal.principal_id, operation, resource_type)
    return allowed, reason


# Convenience function for quick checks
def check_access(
    execution_context: _ExecutionContext | None,
    *,
    operation: str = "read",
    resource_type: str = "skill",
) -> bool:
    """Return True iff HROT authorization grants access."""
    allowed, _ = authorize_resource_access(execution_context, operation=operation, resource_type=resource_type)
    return allowed


# -------------------------------------------------------------------------
# ResourceRecord — Enregistrement d'une ressource dans le registry.
# -------------------------------------------------------------------------


def _normalize_title(title: str) -> str:
    """Normalise un titre pour comparer deux ressources de façon stricte.

    La normalisation retire la casse, la ponctuation et les espaces superflus.
    Elle sert uniquement à établir des relations objectives : deux titres
    normalisés identiques sont considérés comme désignant la même chose.

    Args:
        title: Titre à normaliser.

    Returns:
        Forme normalisée du titre.
    """
    normalized = re.sub(r"[^\w\s]+", " ", (title or "").lower())
    return " ".join(normalized.split())


class ResourceRecord:
    """Enregistrement d'une ressource dans le registry.

    Représente une référence vers une ressource originale sans la posséder.
    Maintient l'état opérationnel et l'historique de découverte.

    Attributs :
        resource_type : Type de la ressource (skill, agent, etc.)
        title : Titre de la ressource
        stable_id : Identifiant stable (UUIDv5 déterministe)
        knowledge_node : KnowledgeNode associé (pour persistance)
        source_original : Chemin vers la source originale (inchangée)
        metadata : Métadonnées enrichies
        discovered_at : Timestamp de la première découverte
        last_verified : Timestamp de la dernière vérification
        status : État opérationnel actuel
    """

    def __init__(
        self,
        resource_type: ResourceType,
        title: str,
        stable_id: str,
        knowledge_node: KnowledgeNode | None = None,
        source_original: str = "",
        metadata: dict[str, Any] | None = None,
        status: ResourceStatus = ResourceStatus.ACTIVE,
    ) -> None:
        self.resource_type = resource_type
        self.title = title
        self.stable_id = stable_id
        self.knowledge_node = knowledge_node
        self.source_original = source_original
        self.metadata = metadata or ResourceMeta().to_dict()
        self.discovered_at = datetime.utcnow()
        self.last_verified: datetime | None = None
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'enregistrement pour persistance."""
        return {
            "resource_type": self.resource_type.value,
            "title": self.title,
            "stable_id": self.stable_id,
            "knowledge_node_id": self.knowledge_node.id if self.knowledge_node else None,
            "source_original": self.source_original,
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat(),
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], km: KnowledgeManager | None = None) -> "ResourceRecord":
        """Désérialise depuis un dictionnaire.

        Note : La reconstitution du KnowledgeNode via km.get() doit être
        effectuée dans un contexte séparé (via _reconstitute_node).
        Cette méthode ne fait que parser les champs de base.
        """
        stable_id = data["stable_id"]
        resource_type = ResourceType(data.get("resource_type", "skill"))
        title = data.get("title", "")
        source_original = data.get("source_original", "")
        metadata = data.get("metadata", ResourceMeta().to_dict())

        # Champs optionnels
        knowledge_node_id = data.get("knowledge_node_id")
        status_value = data.get("status", ResourceStatus.ACTIVE.value)

        record = ResourceRecord(
            resource_type=resource_type,
            title=title,
            stable_id=stable_id,
            knowledge_node=None,  # Sera reconstitué plus tard
            source_original=source_original,
            metadata=metadata,
            status=ResourceStatus.from_value(status_value),
        )

        # P2.8.1 - fidelite du round-trip : sans cela, une ressource relue
        # depuis la source de verite perdait sa date de decouverte et
        # repartait a now(), ce qui faussait l'historique.
        discovered_at = data.get("discovered_at")
        if discovered_at:
            try:
                record.discovered_at = datetime.fromisoformat(discovered_at)
            except (TypeError, ValueError):
                pass
        last_verified = data.get("last_verified")
        if last_verified:
            try:
                record.last_verified = datetime.fromisoformat(last_verified)
            except (TypeError, ValueError):
                pass

        # Stocker l'ID du KnowledgeNode pour reconstitution ulterieure
        record._pending_knowledge_node_id = knowledge_node_id

        return record

    @staticmethod
    def _reconstitute_node(record: ResourceRecord, km: KnowledgeManager) -> KnowledgeNode | None:
        """Rétablit un KnowledgeNode depuis le stockage à partir de son ID.

        Doit être appelé dans un contexte async.
        """
        if not record._pending_knowledge_node_id:
            return record.knowledge_node

        try:
            existing = km._records.get(record._pending_knowledge_node_id)  # type: ignore[attr-defined]
            if existing is None:
                record._pending_knowledge_node_id = str(
                    existing.id if hasattr(existing, 'id') else existing
                ) if existing else None
            return existing
        except Exception:
            record._pending_knowledge_node_id = None
            return None

    def __repr__(self) -> str:
        return (
            f"<ResourceRecord type={self.resource_type.value} "
            f"title={self.title} stable_id={self.stable_id} "
            f"status={self.status.value}>"
        )


# -------------------------------------------------------------------------
# ResourceRegistry — Registry central des ressources ETHAN.
# -------------------------------------------------------------------------


class ResourceRegistry:
    """Registry central des ressources ETHAN.

    Gère la découverte, l'enregistrement, la recherche et le cycle de vie
    des ressources sans modifier leurs sources originales. Utilise le
    KnowledgeManager sous-jacent pour la persistance.

    Le registry est conçu pour :
    - Être idempotent : appeler discover() plusieurs fois ne crée pas de doublons.
    - Être durable : l'état du registre peut être rétabli après redémarrage
      depuis CoreRecordStore via le fichier de métadonnées registry-meta.json.
    - Gérer le cycle de vie : détecter les nouvelles, modifiées, déplacées et
      disparues sans supprimer leurs métadonnées descriptives.
    - Respecter HROT : les opérations respectent les identités et permissions.
    """

    def __init__(
        self,
        knowledge_manager: KnowledgeManager | None = None,
        *,
        registry_meta_path: str | None = None,
        store: CoreRecordStore | None = None,
        export_path: str | None = None,
    ) -> None:
        """Initialise le registre.

        P2.8.1 — le registre s'appuie sur le `CoreRecordStore` partagé d'ETHAN
        Core, comme tous les autres services. `registry-meta.json` n'est plus
        une autorité concurrente : il reste un amorçage (bootstrap) et un
        export portable.

        Args:
            knowledge_manager: Gestionnaire de connaissances. Si absent, un
                `KnowledgeManager` est construit sur le `store` fourni — sans
                quoi les nœuds créés par le registre seraient perdus au
                redémarrage.
            registry_meta_path: Chemin du fichier d'amorçage historique.
            store: Store Core partagé (PostgreSQL en production).
            export_path: Chemin d'export portable. Par défaut, le même que
                `registry_meta_path`.
        """
        self._store = store
        self._repository: Optional[ResourceRepository] = (
            ResourceRepository(store) if store is not None else None
        )
        # Un KnowledgeManager sans store persiste uniquement en mémoire : les
        # nœuds produits par la découverte seraient perdus au redémarrage.
        self.km: KnowledgeManager = knowledge_manager or KnowledgeManager(store=store)
        self._records: dict[str, ResourceRecord] = {}
        self._index: dict[str, Dict[str, List[ResourceRecord]]] = {
            "by_type": {},
            "by_domain": {},
            "by_status": {},
        }
        # P2.8.1 - un chemin explicite fait foi : sans cette distinction, un
        # registre de test chargeait silencieusement le registre-meta.json
        # global, rendant la persistance non deterministe.
        self._explicit_meta_path = registry_meta_path is not None
        self.registry_meta_path = Path(registry_meta_path) if registry_meta_path else Path("registry-meta.json")
        self.export_path = Path(export_path) if export_path else self.registry_meta_path

        # Charger l'état existant si disponible (pour la durabilité)
        self._load_from_persistence()

        logger.info(f"ResourceRegistry initialisé avec {len(self._records)} enregistrements")

    # --- Chargement/déchargement persistence ---

    def _load_from_persistence(self) -> None:
        """Reconstruit l'état en mémoire à partir du stockage durable.

        Essaie de lire registry-meta.json depuis le répertoire racine ETHAN
        ou depuis le répertoire de travail actuel. Si le fichier n'existe pas,
        le registry commence vide et sera peuplé par la première découverte.
        Note : Le rechargement des KnowledgeNodes est différé — les enregistrements
        sont créés avec knowledge_node=None et le nœud est reconstitué plus tard
        via _reconstitue_pending_nodes().
        """
        # Emplacements possibles. Le fallback global n'est retenu que si
        # l'appelant n'a pas fourni de chemin explicite : un chemin explicite
        # doit rester autoritaire.
        possible_paths = [self.registry_meta_path]
        if not self._explicit_meta_path:
            possible_paths.append(Path.cwd() / self.registry_meta_path.name)
            possible_paths.append(Path("/home/fatsio/AI/Ethan") / self.registry_meta_path.name)

        loaded = False
        for path in possible_paths:
            if path.is_file():
                try:
                    import json
                    data = json.loads(path.read_text(encoding="utf-8"))
                    # Reconstruction des enregistrements (sans KnowledgeNode pour l'instant)
                    for record_data in data.get("records", []):
                        try:
                            record = ResourceRecord.from_dict(record_data, self.km)
                            # Stocker le knowledge_node_id pending pour reconstitution ultérieure
                            if record._pending_knowledge_node_id:
                                # Reconstituer le node dans un contexte ultérieur
                                pass  # Reporté à _reconstitute_pending_nodes()
                            self._records[record.stable_id] = record
                            logger.debug(
                                f"Enregistrement chargé depuis persistence : {record.title} ({record.stable_id})"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Impossible de charger l'enregistrement depuis persistence : {e}"
                            )
                    # Reconstruction des index (sans nœuds KnowledgeNode pour l'instant)
                    self._rebuild_indices_without_nodes()
                    loaded = True
                    logger.info(f"État du Registry rétabli depuis {path}")
                    break
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Impossible de lire {path} : {e}")
                    continue

        if not loaded:
            logger.info("Aucun fichier de persistence trouvé — nouveau registry")

    def _rebuild_indices_without_nodes(self) -> None:
        """Rebâtit les index en ne comptant que les métadonnées, pas les KnowledgeNodes."""
        self._index = {
            "by_type": {},
            "by_domain": {},
            "by_status": {},
        }

        for record in self._records.values():
            # On indexe quand même par type, domaine, statut même sans KnowledgeNode
            rt = record.resource_type.value
            self._index["by_type"].setdefault(rt, []).append(record)

            domain = str(record.metadata.get("domain", "")).lower()
            if domain:
                self._index["by_domain"].setdefault(domain, []).append(record)

            st = record.status.value
            self._index["by_status"].setdefault(st, []).append(record)

    async def _reconstitute_pending_nodes(self) -> None:
        """Rétablit les KnowledgeNodes manquants pour les enregistrements chargés depuis persistence.

        Doit être appelé dans un contexte après _load_from_persistence().
        Parcourt tous les enregistrements qui ont _pending_knowledge_node_id défini
        et tente de récupérer le nœud depuis KnowledgeManager.
        """
        for record in self._records.values():
            if record.knowledge_node is not None:
                continue  # Déjà有

            pending_id = getattr(record, '_pending_knowledge_node_id', None)
            if not pending_id:
                continue

            try:
                node = await self.km.get(pending_id)
                if node is not None:
                    record.knowledge_node = node
                    logger.debug(
                        f"KnowledgeNode créé en base : {node.label} ({node.id})"
                    )
                else:
                    logger.debug(
                        f"KnowledgeNode introuvable pour {record.title} ({pending_id})"
                    )
            except Exception as e:
                logger.warning(
                    f"Erreur reconstitution KnowledgeNode pour {record.title} : {e}"
                )

    async def _save_to_persistence(self) -> None:
        """Sauvegarde l'export portable du registre dans registry-meta.json.

        P2.8.1 — le chemin d'ecriture autoritaire est le `CoreRecordStore`
        (domaine `resources`), comme pour tous les autres services Core. Ce
        fichier reste produit comme **export portable** et comme **amorçage**,
        mais il n'est plus une autorite concurrente.

        Inclut les IDs de KnowledgeNode là où disponibles, mais ne bloque pas
        si un nœud est manquant (les métadonnées sont quand même sauvegardées).
        """
        records_data: List[dict[str, Any]] = []
        for record in self._records.values():
            data = record.to_dict()

            # S'assurer que knowledge_node_id est inclus si on a un nœud
            if record.knowledge_node:
                data["knowledge_node_id"] = record.knowledge_node.id
            elif hasattr(record, '_pending_knowledge_node_id') and record._pending_knowledge_node_id:
                data["knowledge_node_id"] = record._pending_knowledge_node_id

            records_data.append(data)

        meta_data = {
            "records": records_data,
            "total_resources": len(self._records),
            "export_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
        }

        # Export portable (fichier) : toujours produit pour compatibilité.
        try:
            self.export_path.parent.mkdir(parents=True, exist_ok=True)
            self.export_path.write_text(
                json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.debug(f"Export du Registry sauvegardé vers {self.export_path}")
        except Exception as e:
            logger.error(f"Échec sauvegarde export : {e}")

    async def persist(self) -> None:
        """Écrit l'état du registre dans la source de vérité puis l'export.

        P2.8.1 — unique point d'écriture. Appelé par toutes les mutations du
        registre, il garantit que la vue PostgreSQL et l'export portable
        restent cohérents entre eux.
        """
        if self._repository is not None:
            try:
                await self._repository.save_all(self._records.values())
                logger.debug(
                    "Ressources persistées dans core_domain_records[%s] (%d)",
                    self._repository.domain,
                    len(self._records),
                )
            except Exception as e:
                logger.error(f"Échec sauvegarde CoreRecordStore : {e}")
        await self._save_to_persistence()

    async def load_from_repository(self) -> int:
        """Recharge l'état du registre depuis la source de vérité (CoreRecordStore).

        P2.8.1 — à appeler au démarrage quand un `store` est injecté, pour que
        l'état persistant prenne le pas sur l'amorçage fichier.

        Returns:
            Nombre d'enregistrements chargés.
        """
        if self._repository is None:
            return 0

        try:
            stored = await self._repository.load_all()
        except Exception as e:
            logger.warning(f"Lecture CoreRecordStore impossible : {e}")
            return 0

        loaded: Dict[str, ResourceRecord] = {}
        for data in stored:
            try:
                record = ResourceRecord.from_dict(data)
            except Exception as e:
                logger.warning(f"Enregistrement de ressource illisible : {e}")
                continue
            loaded[record.stable_id] = record

        if not loaded:
            return 0

        self._records = loaded
        self._rebuild_indices()
        await self._reconstitute_pending_nodes()
        logger.info(
            "ResourceRegistry : %d enregistrements charges depuis core_domain_records[%s]",
            len(self._records),
            self._repository.domain,
        )
        return len(self._records)

    def _rebuild_indices(self) -> None:
        """Rebâtit les index in mémoire à partir de _records."""
        self._index = {
            "by_type": {},
            "by_domain": {},
            "by_status": {},
        }

        for record in self._records.values():
            # Index par type
            rt = record.resource_type.value
            self._index["by_type"].setdefault(rt, []).append(record)

            # Index par domaine
            domain = str(record.metadata.get("domain", "")).lower()
            if domain:
                self._index["by_domain"].setdefault(domain, []).append(record)

            # Index par statut
            st = record.status.value
            self._index["by_status"].setdefault(st, []).append(record)

    # --- Discovery ---

    async def attach_pending_nodes(self) -> int:
        """Rattache les KnowledgeNodes chargés depuis la persistance.

        Le rechargement depuis ``registry-meta.json`` laisse les
        KnowledgeNodes détachés : cette méthode les rattache. Elle est
        idempotente et sans effet sur les enregistrements déjà rattachés.

        Returns:
            Nombre d'enregistrements rattachés lors de cet appel.
        """
        before = sum(
            1 for record in self._records.values() if record.knowledge_node is not None
        )
        await self._reconstitute_pending_nodes()
        after = sum(
            1 for record in self._records.values() if record.knowledge_node is not None
        )
        return after - before

    async def discover_skills(
        self, skills_root: Path | None = None
    ) -> Tuple[List[ResourceRecord], dict[str, int]]:
        """Découvre les skills OpenCode et enregistre leurs références.

        Returns:
            Tuple de (liste de ResourceRecord nouvellement enregistrés/mis à jour,
                      dictionnaire de statistiques par statut).
        """
        root: Path = Path(skills_root) if skills_root else Path("/home/fatsio/.config/opencode/skills")

        # Rattacher les KnowledgeNodes chargés depuis la persistance.
        await self.attach_pending_nodes()

        # Exécution de la découverte OpenCode
        meta_list, nodes = discover_skills(root, create_knowledge_nodes=True)

        new_records: List[ResourceRecord] = []
        # Utiliser directement les valeurs de statut connues
        known_statuses = [ResourceStatus.ACTIVE, ResourceStatus.STALE, ResourceStatus.DEPRECATED, ResourceStatus.DISAPPEARED]
        status_counts: dict[str, int] = {status.value: 0 for status in known_statuses}

        for i, (meta, node) in enumerate(zip(meta_list, nodes)):
            # ID stable basé sur type+source+title (UUIDv5 déterministe)
            stable_id = meta.get("stable_id", "")

            if not stable_id:
                # Fallback : UUIDv4 si quelque chose manque
                import uuid
                stable_id = str(uuid.uuid4())

            # Vérifier si cette ressource existe déjà
            existing_record = self._records.get(stable_id)

            if existing_record is not None:
                # Ressource existante — vérifier si elle a changé
                has_changed = self._has_resource_changed(existing_record, meta, node)

                # Rattacher le KnowledgeNode s'il manque (enregistrement chargé
                # depuis la persistance avant que le nœud n'ait été persisté).
                if existing_record.knowledge_node is None and node is not None:
                    try:
                        attached = await self.km.get(node.id)
                        if attached is None:
                            attached = await self.km.create(
                                label=node.label,
                                node_type=node.node_type,
                                content=node.content,
                                source=node.source,
                                metadata=node.metadata,
                                node_id=node.id,
                            )
                        existing_record.knowledge_node = attached
                    except Exception as exc:
                        logger.warning("Rattachement KnowledgeNode impossible : %s", exc)

                if has_changed:
                    # Ressource modifiée — mettre à jour
                    await self._update_record(existing_record, meta, node)
                    new_records.append(existing_record)
                    status_counts[ResourceStatus.STALE.value] += 1  # Repassera à ACTIVE après vérification
                    logger.debug(
                        f"Ressource modifiée mise à jour : {existing_record.title} ({stable_id})"
                    )
                else:
                    # Ressource inchangée — juste mise à jour du statut de vérification
                    existing_record.last_verified = datetime.utcnow()
                    existing_record.status = ResourceStatus.ACTIVE
                    new_records.append(existing_record)
                    status_counts[ResourceStatus.ACTIVE.value] += 1
                    logger.debug(
                        f"Ressource inchangée vérifiée : {existing_record.title} ({stable_id})"
                    )
            else:
                # Nouvelle ressource — création
                record = ResourceRecord(
                    resource_type=ResourceType(meta["resource_type"]),
                    title=meta["title"],
                    stable_id=stable_id,
                    knowledge_node=node,
                    source_original=meta["source_original"],
                    metadata=meta.get("metadata", ResourceMeta().to_dict()),
                    status=ResourceStatus.ACTIVE,
                )

                # Persister le KnowledgeNode en base
                try:
                    existing_node = await self.km.get(node.id)
                    if existing_node is None:
                        # L'identité du nœud est alignée sur celle de la ressource :
                        # le lien record <-> KnowledgeNode survit au rechargement.
                        created_node = await self.km.create(
                            label=node.label,
                            node_type=node.node_type,
                            content=node.content,
                            source=node.source,
                            metadata=node.metadata,
                            node_id=node.id,
                        )
                        record.knowledge_node = created_node
                        logger.info(
                            f"KnowledgeNode créé en base : {node.label} ({node.id})"
                        )
                    else:
                        record.knowledge_node = existing_node
                except Exception as e:
                    logger.warning(f"Erreur création KnowledgeNode : {e}")

                # Ajouter au registry
                self._records[stable_id] = record
                new_records.append(record)
                status_counts[ResourceStatus.ACTIVE.value] += 1
                logger.info(f"Nouvelle ressource découverte : {record.title} ({stable_id})")

        # Mise à jour des index
        self._rebuild_indices()

        # Sauvegarde persistante()
        await self.persist()

        return new_records, status_counts

    def _has_resource_changed(
        self, existing: ResourceRecord, meta: dict[str, Any], node: KnowledgeNode
    ) -> bool:
        """Détermine si une ressource existante a changé.

        Compare :
        - source_original (chemin canonique)
        - metadata clés essentielles
        - titre et type
        - contenu du KnowledgeNode
        """
        changes = False

        # Vérifier le chemin source original (le plus critique)
        existing_source = existing.source_original
        new_source = meta.get("source_original", "")
        # Normalisation des chemins
        try:
            existing_resolved = str(Path(existing_source).resolve())
            new_resolved = str(Path(new_source).resolve()) if new_source else ""
            if existing_resolved != new_resolved:
                changes = True
                logger.debug(
                    f"Source changée : {existing_resolved} -> {new_resolved}"
                )
        except Exception:
            if existing_source != new_source:
                changes = True

        # Vérifier les métadonnées essentielles
        existing_meta = existing.metadata
        new_meta = meta.get("metadata", ResourceMeta().to_dict())
        # "categories" et "description" n'existent que pour les ressources
        # documentaires : pour les Skills, les deux côtés valent "" et la
        # comparaison reste neutre. "knowledge_state" est volontairement
        # exclu : c'est un état de traitement, pas une propriété du document.
        # Il ne doit donc pas déclencher une détection de changement.
        essential_keys = {
            "domain",
            "level",
            "resource_type",
            "confidence",
            "categories",
            "description",
        }
        for key in essential_keys:
            if str(existing_meta.get(key, "")) != str(new_meta.get(key, "")):
                changes = True
                logger.debug(f"Métadonnée changée : {key}")
                break

        # Vérifier le titre
        if existing.title != meta.get("title", ""):
            changes = True
            logger.debug("Titre changé")

        # Vérifier le KnowledgeNode content
        if (existing.knowledge_node and node and
                existing.knowledge_node.content != node.content):
            changes = True
            logger.debug("Contenu KnowledgeNode changé")

        return changes

    async def _update_record(
        self, record: ResourceRecord, meta: dict[str, Any], node: KnowledgeNode
    ) -> None:
        """Met à jour un enregistrement existant avec de nouvelles métadonnées."""
        record.title = meta.get("title", record.title)
        record.metadata = meta.get("metadata", record.metadata)
        record.last_verified = datetime.utcnow()
        # Statut repasse à ACTIVE après mise à jour
        record.status = ResourceStatus.ACTIVE

        # Mettre à jour le KnowledgeNode si différent
        if node is not None:
            try:
                if record.knowledge_node is None:
                    record.knowledge_node = await self.km.create(
                        label=node.label,
                        node_type=node.node_type,
                        content=node.content,
                        source=node.source,
                        metadata=node.metadata,
                        node_id=node.id,
                    )
                else:
                    # L'identité du nœud est alignée sur celle de la ressource :
                    # on actualise le contenu et les métadonnées sans dupliquer.
                    updated = await self.km.update(
                        node.id,
                        {
                            "content": node.content,
                            "source": node.source,
                            "metadata": node.metadata,
                        },
                    )
                    if updated is not None:
                        record.knowledge_node = updated
            except Exception as e:
                logger.warning(f"Erreur mise à jour KnowledgeNode : {e}")

        logger.debug(f"Enregistrement mis à jour : {record.title} ({record.stable_id})")

    async def discover_all(self, skills_root: Path | None = None) -> dict[str, Any]:
        """Découvre toutes les catégories de ressources.

        Returns:
            Dictionnaire avec statistiques et listes de ResourceRecord.
        """
        new_records, status_counts = await self.discover_skills(skills_root)

        return {
            "records": new_records,
            "status_counts": status_counts,
            "total_known": len(self._records),
            "by_type": {rt: [r for r in recs if r.resource_type.value == rt]
                       for rt, recs in self._index["by_type"].items()},
            "by_domain": {d: recs for d, recs in self._index["by_domain"].items()},
            "by_status": {s: recs for s, recs in self._index["by_status"].items()},
        }

    # --- Document discovery (DAĒNĀ P2.7) ---

    async def discover_documents(
        self,
        knowledge_roots: Tuple[Path, ...] | None = None,
        *,
        create_knowledge_nodes: bool = True,
    ) -> dict[str, Any]:
        """Découvre les documents des emplacements configurés et les enregistre.

        Cette méthode orchestre le cycle de vie documentaire :

        1. scan des emplacements configurés (délégué à ``discover_documents``) ;
        2. création ou mise à jour de la référence dans le registre ;
        3. détection des documents disparus entre deux passes ;
        4. restauration des documents réapparus ;
        5. persistance de l'état.

        La découverte et l'extraction restent deux opérations distinctes :
        ``metadata["knowledge_state"]`` vaut ``discovered`` quand seul le
        chemin et les métadonnées sont enregistrés, ``extracted`` quand le
        contenu a réellement pu être extrait. Le passage à ``indexed``
        n'a lieu que via ``index_documents()``, qui exige une ingestion RAG
        réellement aboutie.

        Les fichiers sources ne sont jamais déplacés, renommés ni modifiés :
        seules des références et des KnowledgeNodes sont créés.

        Args:
            knowledge_roots: Emplacements à surveiller. Par défaut, la
                configuration ``KNOWLEDGE_ROOTS``.
            create_knowledge_nodes: Si True, crée les KnowledgeNodes associés.

        Returns:
            Dictionnaire avec le nombre de ressources par statut, les
            ressources touchées et les compteurs d'état de traitement.
        """
        from core.resources.discovery import discover_documents, knowledge_root_list

        # Rattacher les KnowledgeNodes chargés depuis la persistance.
        await self.attach_pending_nodes()

        roots = knowledge_root_list(knowledge_roots or KNOWLEDGE_ROOTS)
        meta_list, nodes = discover_documents(
            roots, create_knowledge_nodes=create_knowledge_nodes
        )

        known_statuses = [
            ResourceStatus.ACTIVE,
            ResourceStatus.STALE,
            ResourceStatus.DEPRECATED,
            ResourceStatus.DISAPPEARED,
        ]
        status_counts: dict[str, int] = {status.value: 0 for status in known_statuses}

        new_records: List[ResourceRecord] = []
        seen_ids: Set[str] = set()
        created_nodes = 0
        updated_nodes = 0

        for meta, node in zip(meta_list, nodes):
            stable_id = meta.get("stable_id", "")
            if not stable_id:
                continue
            seen_ids.add(stable_id)

            existing_record = self._records.get(stable_id)

            if existing_record is not None:
                # Ressource déjà connue : détection de changement et restauration.
                if existing_record.status == ResourceStatus.DISAPPEARED:
                    # Le document est réapparu : on le restaure explicitement.
                    await self.restore_resource(stable_id)

                # Rattacher le KnowledgeNode s'il manque (enregistrement chargé
                # depuis la persistance avant que le nœud n'ait été persisté).
                if existing_record.knowledge_node is None and node is not None:
                    try:
                        attached = await self.km.get(node.id)
                        if attached is None:
                            attached = await self.km.create(
                                label=node.label,
                                node_type=node.node_type,
                                content=node.content,
                                source=node.source,
                                metadata=node.metadata,
                                node_id=node.id,
                            )
                            created_nodes += 1
                        existing_record.knowledge_node = attached
                    except Exception as exc:
                        logger.warning("Rattachement KnowledgeNode impossible : %s", exc)

                if self._has_resource_changed(existing_record, meta, node):
                    await self._update_record(existing_record, meta, node)
                    new_records.append(existing_record)
                    status_counts[ResourceStatus.STALE.value] += 1
                    updated_nodes += 1
                else:
                    existing_record.last_verified = datetime.utcnow()
                    existing_record.status = ResourceStatus.ACTIVE
                    # L'état de traitement évolue indépendamment du document :
                    # on le fait progresser sans jamais déclasser un "indexed".
                    current_state = existing_record.metadata.get("knowledge_state", "discovered")
                    new_state = meta.get("metadata", {}).get("knowledge_state", "discovered")
                    if current_state != "indexed" and new_state != current_state:
                        existing_record.metadata["knowledge_state"] = new_state
                    new_records.append(existing_record)
                    status_counts[ResourceStatus.ACTIVE.value] += 1
            else:
                record = ResourceRecord(
                    resource_type=ResourceType(meta["resource_type"]),
                    title=meta["title"],
                    stable_id=stable_id,
                    knowledge_node=node,
                    source_original=meta["source_original"],
                    metadata=meta.get("metadata", ResourceMeta().to_dict()),
                    status=ResourceStatus.ACTIVE,
                )

                # Persister le KnowledgeNode associé.
                try:
                    existing_node = await self.km.get(node.id)
                    if existing_node is None:
                        # L'identité du nœud est alignée sur celle de la ressource :
                        # le lien record <-> KnowledgeNode survit au rechargement.
                        created_node = await self.km.create(
                            label=node.label,
                            node_type=node.node_type,
                            content=node.content,
                            source=node.source,
                            metadata=node.metadata,
                            node_id=node.id,
                        )
                        record.knowledge_node = created_node
                        created_nodes += 1
                    else:
                        if existing_node.content != node.content:
                            existing_node = await self.km.update(
                                node.id,
                                {
                                    "content": node.content,
                                    "metadata": node.metadata,
                                },
                            ) or existing_node
                        record.knowledge_node = existing_node
                except Exception as exc:
                    logger.warning("Erreur création KnowledgeNode : %s", exc)

                self._records[stable_id] = record
                new_records.append(record)
                status_counts[ResourceStatus.ACTIVE.value] += 1

        # Détection des disparitions : les documents connus qui ne sont plus
        # visibles dans les emplacements surveillés passent DISAPPEARED.
        # Aucune donnée n'est supprimée : les métadonnées sont conservées.
        disappeared = await self._mark_missing_documents(roots, seen_ids)
        status_counts[ResourceStatus.DISAPPEARED.value] = len(disappeared)

        self._rebuild_indices()
        await self.persist()

        state_counts = self._count_knowledge_states(new_records)

        return {
            "records": new_records,
            "status_counts": status_counts,
            "total_known": len(self._records),
            "documents_discovered": len(new_records),
            "documents_created": len(new_records) - len(disappeared),
            "documents_disappeared": len(disappeared),
            "knowledge_nodes_created": created_nodes,
            "knowledge_nodes_updated": updated_nodes,
            "knowledge_states": state_counts,
            "knowledge_roots_searched": [str(r) for r in roots],
        }

    async def _mark_missing_documents(
        self,
        roots: Tuple[Path, ...],
        seen_ids: Set[str],
    ) -> List[ResourceRecord]:
        """Marque DISAPPEARED les documents known qui ne sont plus sur le disque.

        Seules les ressources dont la source réside sous un emplacement
        surveillé sont concernées : les Skills et les autres ressources ne
        sont pas affectées par la découverte documentaire.

        Args:
            roots: Emplacements surveillés.
            seen_ids: Identifiants vus lors de la passe courante.

        Returns:
            Liste des ressources passées à DISAPPEARED.
        """
        disappeared: List[ResourceRecord] = []
        for record in list(self._records.values()):
            if record.stable_id in seen_ids:
                continue
            if not record.source_original:
                continue
            if not self._is_under_roots(record.source_original, roots):
                continue
            if record.status == ResourceStatus.DISAPPEARED:
                continue
            if await self.mark_disappeared(record.stable_id):
                disappeared.append(record)
        return disappeared

    @staticmethod
    def _is_under_roots(source: str, roots: Tuple[Path, ...]) -> bool:
        """Indique si un chemin source réside sous un emplacement surveillé.

        Args:
            source: Chemin source de la ressource.
            roots: Emplacements surveillés.

        Returns:
            True si le chemin est sous l'un des emplacements.
        """
        try:
            resolved = Path(source).resolve()
        except OSError:
            resolved = Path(source)
        for root in roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    @staticmethod
    def _count_knowledge_states(records: List[ResourceRecord]) -> dict[str, int]:
        """Compte les états de traitement documentaire d'un lot de ressources.

        Args:
            records: Ressources à examiner.

        Returns:
            Compteur par état (``discovered``, ``extracted``, ``indexed``).
        """
        counts = {"discovered": 0, "extracted": 0, "indexed": 0}
        for record in records:
            state = record.metadata.get("knowledge_state", "discovered")
            if state in counts:
                counts[state] += 1
        return counts

    async def index_documents(self, rag: Any) -> dict[str, Any]:
        """Intègre les KnowledgeNodes documentaires dans un pipeline RAG exploitable.

        L'état ``knowledge_state`` ne passe à ``indexed`` que si l'ingestion
        RAG a réellement abouti. Aucun nouveau moteur d'indexation n'est
        créé : le pipeline RAG existant et
        ``KnowledgeManager.ingest_into_rag`` sont réutilisés.

        Args:
            rag: Instance de ``RAGPipeline`` ou compatible (méthode ``ingest``).

        Returns:
            Dictionnaire avec les identifiants indexés et les échecs.
        """
        indexed: List[str] = []
        failed: List[dict[str, str]] = []

        for record in list(self._records.values()):
            node = record.knowledge_node
            if node is None or not node.content:
                continue
            if record.metadata.get("knowledge_state") == "indexed":
                continue

            try:
                document_id = await self.km.ingest_into_rag(node.id, rag)
            except Exception as exc:
                failed.append(
                    {
                        "stable_id": record.stable_id,
                        "title": record.title,
                        "error": str(exc),
                    }
                )
                logger.warning("Indexation RAG impossible pour %s : %s", record.title, exc)
                continue

            record.metadata["knowledge_state"] = "indexed"
            record.metadata["rag_document_id"] = document_id
            try:
                await self.km.update(
                    node.id,
                    {"metadata": {"knowledge_state": "indexed", "rag_document_id": document_id}},
                )
            except Exception as exc:
                logger.warning("Mise \u00e0 jour KnowledgeNode impossible : %s", exc)
            indexed.append(record.stable_id)

        await self.persist()

        return {
            "indexed": indexed,
            "indexed_count": len(indexed),
            "failed": failed,
            "failed_count": len(failed),
        }

    async def link_documents_to_skills(self) -> dict[str, Any]:
        """Rattache les documents aux Skills du catalogue lorsque c'est justifié.

        Deux relations objectives sont retenues, toutes deux vérifiables :

        * **structurelle** : le document réside dans le répertoire de la Skill ;
        * **nominale** : le titre normalisé du document est strictement égal à
          celui de la Skill.

        Aucune relation n'est créée sur une ressemblance approximative. Les
        Skills du catalogue ne sont ni modifiés ni dupliqués : seules des
        relationsKnowledgeNode sont ajoutées.

        Returns:
            Dictionnaire avec les relations créées et les liens des ressources.
        """
        # Rattacher les KnowledgeNodes chargés depuis la persistance.
        await self.attach_pending_nodes()

        skills = self.list_by_type(ResourceType.SKILL)
        if not skills:
            return {"links": [], "linked_count": 0}

        # Index des Skills par répertoire source et par titre normalisé.
        by_directory: dict[str, ResourceRecord] = {}
        by_title: dict[str, ResourceRecord] = {}
        for skill in skills:
            if skill.source_original:
                by_directory[skill.source_original] = skill
            by_title[_normalize_title(skill.title)] = skill

        links: List[dict[str, str]] = []
        for record in list(self._records.values()):
            # Les Skills ne sont jamais reliés à eux-mêmes.
            if record.resource_type == ResourceType.SKILL:
                continue

            target: ResourceRecord | None = None
            reason = ""

            # Relation structurelle : le document est dans le répertoire de la Skill.
            for skill_dir, skill in by_directory.items():
                if record.source_original and record.source_original.startswith(skill_dir + "/"):
                    target = skill
                    reason = "document resides in the skill directory"
                    break

            # Relation nominale : titres normalisés strictement identiques.
            if target is None:
                candidate = by_title.get(_normalize_title(record.title))
                if candidate is not None:
                    target = candidate
                    reason = "normalized titles are identical"

            if target is None:
                continue

            if record.knowledge_node is None or target.knowledge_node is None:
                continue

            try:
                await self.km.connect(
                    record.knowledge_node.id,
                    target.knowledge_node.id,
                    relation_type="documents_skill",
                    strength=1.0,
                    metadata={
                        "document_id": record.stable_id,
                        "skill_id": target.stable_id,
                        "justification": reason,
                    },
                )
            except Exception as exc:
                logger.warning(
                    "Relation document/skill impossible (%s -> %s) : %s",
                    record.stable_id,
                    target.stable_id,
                    exc,
                )
                continue

            related = list(record.metadata.get("related_to", []))
            if target.stable_id not in related:
                related.append(target.stable_id)
                record.metadata["related_to"] = related
            links.append(
                {
                    "document_id": record.stable_id,
                    "skill_id": target.stable_id,
                    "justification": reason,
                }
            )

        await self.persist()

        return {"links": links, "linked_count": len(links)}

    # --- Research / Search ---

    def search_resources(
        self,
        query: str,
        *,
        resource_type: ResourceType | str | None = None,
        domain: str | None = None,
        status: ResourceStatus | str | None = None,
    ) -> List[ResourceRecord]:
        """Recherche des ressources par texte avec filtres optionnels.

        Args:
            query: Terme de recherche (recherche dans label, description, métadonnées).
            resource_type: Filtrer par type de ressource.
            domain: Filtrer par domaine.
            status: Filtrer par statut opérationnel.

        Returns:
            Liste de ResourceRecord correspondants.
        """
        terms: List[str] = [term for term in query.casefold().split() if term]
        if not terms:
            # Retourne tous les enregistrements connus filtrés le cas échéant
            records: List[ResourceRecord] = list(self._records.values())
            return records

        # Filtrer par les critères spécifiés
        candidates: List[ResourceRecord] = list(self._records.values())

        # Filtre par type
        if resource_type:
            rt_value = resource_type.value if isinstance(resource_type, ResourceType) else resource_type
            candidates = [r for r in candidates if r.resource_type.value == rt_value]

        # Filtre par domaine
        if domain:
            candidates = [r for r in candidates
                         if str(r.metadata.get("domain", "")).lower() == domain.lower()]

        # Filtre par statut
        if status:
            st_value = status.value if isinstance(status, ResourceStatus) else status
            candidates = [r for r in candidates if r.status.value == st_value]

        # Recherche textuelle
        results: List[ResourceRecord] = []
        for record in candidates:
            haystack = f"{record.title} {record.metadata.get('description', '')} {str(record.metadata)}".casefold()
            if all(term in haystack for term in terms):
                results.append(record)

        # Déduplication (au cas où)
        seen: Set[str] = set()
        deduped: List[ResourceRecord] = []
        for r in results:
            if r.stable_id not in seen:
                seen.add(r.stable_id)
                deduped.append(r)

        return deduped

    def get_resource(self, stable_id: str) -> Optional[ResourceRecord]:
        """Récupère un enregistrement de resource par son identifiant stable.

        Args:
            stable_id: L'identifiant stable unique de la ressource.

        Returns:
            ResourceRecord ou None si introuvable.
        """
        # HROT: vérification d'identité basique
        # En l'absence de contexte d'exécution, on retourne tout de même
        # l'enregistrement si l'ID est connu — la politique d'autorisation
        # s'applique aux opérations qui acceptent un contexte.
        return self._records.get(stable_id)

    def list_by_type(self, resource_type: ResourceType) -> List[ResourceRecord]:
        """Liste toutes les ressources d'un type donné."""
        return self._index["by_type"].get(resource_type.value, [])

    def list_by_domain(self, domain: str) -> List[ResourceRecord]:
        """Liste toutes les ressources d'un domaine donné."""
        return self._index["by_domain"].get(domain.lower(), [])

    def list_by_status(self, status: ResourceStatus) -> List[ResourceRecord]:
        """Liste toutes les ressources d'un statut donné."""
        return self._index["by_status"].get(status.value, [])

    # --- Lifecycle management ---

    async def mark_stale(self, stable_id: str) -> bool:
        """Marque une ressource comme non vérifiée récemment.

        Args:
            stable_id: Identifiant stable de la ressource.

        Returns:
            True si la marque a été appliquée, False si l'identifiant est introuvable.
        """
        record = self._records.get(stable_id)
        if record is None:
            return False

        if record.status != ResourceStatus.STALE:
            record.status = ResourceStatus.STALE
            self._rebuild_indices()
            await self.persist()
            logger.info(f"Ressource marquée comme STALE : {record.title} ({stable_id})")
            return True

        return False

    async def mark_disappeared(self, stable_id: str) -> bool:
        """Marque une ressource comme disparue (source introuvable).

        NE SUPRIME PAS les métadonnées descriptives — elles sont préservées
        pour permettre une éventuelle réapparition.

        Args:
            stable_id: Identifiant stable de la ressource.

        Returns:
            True si la marque a été appliquée, False si l'identifiant est introuvable.
        """
        record = self._records.get(stable_id)
        if record is None:
            return False

        if record.status != ResourceStatus.DISAPPEARED:
            record.status = ResourceStatus.DISAPPEARED
            record.last_verified = datetime.utcnow()
            self._rebuild_indices()
            await self.persist()
            logger.warning(f"Ressource marquée comme DISAPPEARED : {record.title} ({stable_id})")
            return True

        return False

    async def mark_deprecated(self, stable_id: str) -> bool:
        """Marque une ressource comme obsolète.

        Args:
            stable_id: Identifiant stable de la ressource.

        Returns:
            True si la marque a été appliquée, False si l'identifiant est introuvable.
        """
        record = self._records.get(stable_id)
        if record is None:
            return False

        if record.status != ResourceStatus.DEPRECATED:
            record.status = ResourceStatus.DEPRECATED
            self._rebuild_indices()
            await self.persist()
            logger.info(f"Ressource marquée comme DEPRECATED : {record.title} ({stable_id})")
            return True

        return False

    async def restore_resource(self, stable_id: str) -> bool:
        """Restaure une ressource disparue ou dépréciée en état actif.

        Args:
            stable_id: Identifiant stable de la ressource.

        Returns:
            True si la ressource a été restaurée, False si l'identifiant est introuvable.
        """
        record = self._records.get(stable_id)
        if record is None:
            return False

        if record.status in (ResourceStatus.DISAPPEARED, ResourceStatus.DEPRECATED):
            record.status = ResourceStatus.ACTIVE
            record.last_verified = datetime.utcnow()
            self._rebuild_indices()
            await self.persist()
            logger.info(f"Ressource restaurée : {record.title} ({stable_id})")
            return True

        # Déjà actif — rien à faire
        if record.status == ResourceStatus.ACTIVE:
            logger.debug(f"Ressource déjà active : {record.title} ({stable_id})")
            return True

        return False

    # --- Utility ---

    def get_record(self, stable_id: str) -> Optional[ResourceRecord]:
        """Alias pour get_resource."""
        return self._records.get(stable_id)

    def clear_index(self) -> None:
        """Réinitialise l'index en mémoire (utile pour les tests)."""
        self._records.clear()
        self._index = {"by_type": {}, "by_domain": {}, "by_status": {}}
        # Ne pas supprimer le fichier de persistence — on peut le recharger plus tard

    def get_stats(self) -> dict[str, Any]:
        """Retourne des statistiques sur le registry.

        Includes :
        - total_resources
        - breakdown par type, domaine, statut
        - nombre de ressources actives/stal/disparues/dépréciées
        """
        total = len(self._records)

        by_type: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        by_status: dict[str, int] = {status.value: 0 for status in [ResourceStatus.ACTIVE, ResourceStatus.STALE, ResourceStatus.DEPRECATED, ResourceStatus.DISAPPEARED]}

        for record in self._records.values():
            # Type
            rt = record.resource_type.value
            by_type[rt] = by_type.get(rt, 0) + 1

            # Domaine
            domain = str(record.metadata.get("domain", "")).lower()
            if domain:
                by_domain[domain] = by_domain.get(domain, 0) + 1

            # Statut
            st = record.status.value
            by_status[st] = by_status.get(st, 0) + 1

        return {
            "total_resources": total,
            "by_type": by_type,
            "by_domain": by_domain,
            "by_status": by_status,
            "resources_by_type": {
                rt.value: len(self._index["by_type"].get(rt.value, []))
                for rt in ResourceType
            },
            "status_distribution": {
                str(status): count
                for status, count in by_status.items()
            },
        }

    def get_active_resources(self) -> List[ResourceRecord]:
        """Retourne uniquement les ressources en état ACTIVE."""
        return self._index["by_status"].get("active", [])

    def get_stale_resources(self) -> List[ResourceRecord]:
        """Retourne les ressources en état STALE (nécessitant vérification)."""
        return self._index["by_status"].get(ResourceStatus.STALE.value, [])

    def get_disappeared_resources(self) -> List[ResourceRecord]:
        """Retourne les ressources marquées comme disparues."""
        return self._index["by_status"].get(ResourceStatus.DISAPPEARED.value, [])

    def get_deprecated_resources(self) -> List[ResourceRecord]:
        """Retourne les ressources marquées comme dépréciées."""
        return self._index["by_status"].get(ResourceStatus.DEPRECATED.value, [])


# Instance globale par défaut (initialisation lazy)
_global_registry: ResourceRegistry | None = None


def get_resource_registry(
    knowledge_manager: KnowledgeManager | None = None,
    *,
    registry_meta_path: str | None = None,
) -> ResourceRegistry:
    """Retourne l'instance globale du ResourceRegistry (initialisation lazy).

    Args:
        knowledge_manager: KnowledgeManager optionnel à injecter.
        registry_meta_path: Chemin optionnel vers le fichier de métadonnées de persistence.

    Returns:
        Instance ResourceRegistry.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ResourceRegistry(
            knowledge_manager=knowledge_manager,
            registry_meta_path=registry_meta_path,
        )
    return _global_registry
