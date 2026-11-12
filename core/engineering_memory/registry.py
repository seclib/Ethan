"""Registry documentaire et type pour la mémoire technique ETHAN."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.engineering_memory.models import RecordType


@dataclass(frozen=True)
class RegistryDestination:
    """Destination et règles d'enregistrement pour un type de record."""

    record_type: RecordType
    relative_directory: str
    schema_name: str
    statuses: frozenset[str]
    naming: str
    required_fields: tuple[str, ...]


_REGISTRY: dict[RecordType, RegistryDestination] = {
    RecordType.COMPONENT: RegistryDestination(
        record_type=RecordType.COMPONENT,
        # P2.8.0 — correspondance réparée. Le corpus réel utilise le nom
        # français : `Knowledge/Composants/` (daena/INDEX.md, daena/AGENTS.md,
        # daena/README.md). `Knowledge/Components/` n'existe pas et n'a jamais
        # existé dans le corpus — le chemin configuré aurait créé un second
        # répertoire à l'écriture.
        relative_directory="Knowledge/Composants",
        schema_name="Component",
        statuses=frozenset({"PLANNED", "IMPLEMENTED", "VERIFIED", "DEPRECATED", "UNKNOWN"}),
        naming="CMP-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.DECISION: RegistryDestination(
        record_type=RecordType.DECISION,
        relative_directory="Knowledge/Decisions",
        schema_name="Decision",
        statuses=frozenset({"PROPOSED", "UNDER_REVIEW", "APPROVED", "REJECTED", "DEPRECATED", "SUPERSEDED"}),
        naming="DEC-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.ENGINEERING_EVENT: RegistryDestination(
        record_type=RecordType.ENGINEERING_EVENT,
        relative_directory="Archives/Events",
        schema_name="EngineeringEvent",
        statuses=frozenset({"PROPOSED", "UNDER_REVIEW", "IMPLEMENTED", "VERIFIED", "DECLINED", "FAILED", "REJECTED", "RECORDED", "OBSERVED"}),
        naming="EVT-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.INCIDENT: RegistryDestination(
        record_type=RecordType.INCIDENT,
        relative_directory="Knowledge/Incidents",
        schema_name="Incident",
        statuses=frozenset({"OPEN", "INVESTIGATING", "MITIGATED", "RESOLVED", "VERIFIED", "FALSE_POSITIVE"}),
        naming="INC-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at", "incident_type"),
    ),
    RecordType.REPAIR: RegistryDestination(
        record_type=RecordType.REPAIR,
        relative_directory="Archives/Events",
        schema_name="Repair",
        statuses=frozenset({"PROPOSED", "APPROVED", "IMPLEMENTED", "VERIFIED", "FAILED", "ABANDONED"}),
        naming="REP-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.VERIFICATION: RegistryDestination(
        record_type=RecordType.VERIFICATION,
        # P2.8.0 — correspondance réparée. Le corpus réel utilise
        # `Knowledge/Tests-et-Preuves/` (daena/INDEX.md : « Tests et preuves »).
        # `Knowledge/Tests/` n'existe pas dans le corpus.
        relative_directory="Knowledge/Tests-et-Preuves",
        schema_name="Verification",
        statuses=frozenset({"PENDING", "PASSED", "FAILED", "INCONCLUSIVE", "OBSOLETE"}),
        naming="VER-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.DEPENDENCY: RegistryDestination(
        record_type=RecordType.DEPENDENCY,
        # P2.8.0 — correspondance réparée. Le corpus ne comporte aucun
        # répertoire dédié aux dépendances (`Knowledge/Dependencies/` n'a jamais
        # existé). La table de routage du corpus (daena/AGENTS.md) place la
        # catégorie « dépendance » dans la couche `Knowledge/...` ; la
        # destination retenue est donc cette couche, qui existe.
        relative_directory="Knowledge",
        schema_name="Dependency",
        statuses=frozenset({"CLEAN", "VULNERABLE", "REMEDIATED", "ACCEPTED_RISK", "UNKNOWN"}),
        naming="DEP-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.TEST_RESULT: RegistryDestination(
        record_type=RecordType.TEST_RESULT,
        # P2.8.0 — correspondance réparée. Même destination que VERIFICATION :
        # `Knowledge/Tests-et-Preuves/` (daena/INDEX.md : « Tests et preuves »).
        relative_directory="Knowledge/Tests-et-Preuves",
        schema_name="TestResult",
        statuses=frozenset({"RECORDED", "VERIFIED", "STALE", "INVALIDATED"}),
        naming="TST-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.TECHNICAL_DEBT: RegistryDestination(
        record_type=RecordType.TECHNICAL_DEBT,
        relative_directory="Operational-Memory",
        schema_name="TechnicalDebt",
        statuses=frozenset({"IDENTIFIED", "ACCEPTED", "FIXED", "VERIFIED", "WAIVED"}),
        naming="DEBT-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.EVIDENCE: RegistryDestination(
        record_type=RecordType.EVIDENCE,
        relative_directory="_meta",
        schema_name="Evidence",
        statuses=frozenset({"COLLECTED", "TRUSTED", "DISPUTED", "RETRACTED"}),
        naming="EVD-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
    RecordType.AGENT_REPORT: RegistryDestination(
        record_type=RecordType.AGENT_REPORT,
        relative_directory="Archives/Rapports-Agents",
        schema_name="AgentReport",
        statuses=frozenset({"PROVISIONAL", "REVIEWED", "VALIDATED", "REJECTED", "ABANDONED"}),
        naming="RPT-YYYY-NNN-slug.md",
        required_fields=("title", "source_of_fact", "status", "updated_at"),
    ),
}


class EngineeringMemoryRegistry:
    """Résolution simple et sûre des destinations par type."""

    def destination_for(self, record_type: RecordType | str) -> RegistryDestination:
        if isinstance(record_type, str):
            record_type = RecordType(record_type)
        if record_type not in _REGISTRY:
            raise ValueError(f"unknown record type: {record_type}")
        return _REGISTRY[record_type]

    def is_status_allowed(self, record_type: RecordType | str, status: str) -> bool:
        if isinstance(record_type, str):
            record_type = RecordType(record_type)
        return status.upper() in self.destination_for(record_type).statuses

    def relative_path_for(self, record_type: RecordType | str, record_id: str, title: str) -> Path:
        if isinstance(record_type, str):
            record_type = RecordType(record_type)
        if not record_id.strip():
            raise ValueError("record_id must not be empty")
        if any(sep in record_id for sep in ("/", "\\")) or ".." in record_id:
            raise ValueError("record_id is not safe for a relative path")
        destination = self.destination_for(record_type)
        safe_title = title.lower().replace(" ", "-").replace("/", "-")[:48]
        filename = f"{record_id}-{safe_title}.md" if safe_title else f"{record_id}.md"
        return Path(destination.relative_directory, filename)

    def destination_exists(self, root: Path, record_type: RecordType | str) -> bool:
        """Indique si la destination d'un type existe dans le corpus.

        Méthode **strictement en lecture seule** : elle inspecte le système de
        fichiers sans rien créer, déplacer ni modifier. Elle permet à un agent
        ou à une interface de vérifier une destination *avant* toute écriture.

        Args:
            root: Racine du corpus documentaire.
            record_type: Type d'enregistrement dont on veut la destination.

        Returns:
            True si le répertoire de destination existe déjà sous ``root``.
        """
        destination = self.destination_for(record_type)
        return (Path(root) / destination.relative_directory).is_dir()

    def resolve_destination(
        self,
        root: Path,
        record_type: RecordType | str,
        record_id: str,
        title: str,
    ) -> tuple[Path, bool]:
        """Résout la destination d'un enregistrement sans rien écrire.

        Opération **strictement en lecture seule** : elle calcule le chemin
        relatif et signale si le répertoire de destination existe déjà dans le
        corpus. Aucun répertoire n'est créé, ce qui évite qu'une correction
        logique de destination se traduise par une création physique.

        Args:
            root: Racine du corpus documentaire.
            record_type: Type d'enregistrement.
            record_id: Identifiant de l'enregistrement.
            title: Titre de l'enregistrement (pour le nom de fichier).

        Returns:
            Tuple (chemin relatif, destination existante dans le corpus).
        """
        relative = self.relative_path_for(record_type, record_id, title)
        return relative, (Path(root) / relative.parent).is_dir()

    def corpus_mapping(self) -> dict[str, dict[str, str]]:
        """Retourne la correspondance canonique type → destination.

        Expose la table de routage effective pour les interfaces (WebUI, MCP)
        sans leur donner accès à l'écriture.

        Returns:
            Dictionnaire ``{type: {relative_directory, schema_name, naming}}``.
        """
        return {
            record_type.value: {
                "relative_directory": destination.relative_directory,
                "schema_name": destination.schema_name,
                "naming": destination.naming,
            }
            for record_type, destination in _REGISTRY.items()
        }
