"""Service central de l'Engineering Memory d'ETHAN."""

from __future__ import annotations

import json
from pathlib import Path

from core.engineering_memory.models import (
    ConfidenceLevel,
    MemoryRecord,
    RecordType,
    RecordOrigin,
    SourceOfFactLevel,
)
from core.engineering_memory.persistence import (
    DuplicateRecordError,
    ObsidianPersistence,
)
from core.engineering_memory.registry import EngineeringMemoryRegistry, RegistryDestination
from core.engineering_memory.security import SecurityPolicy
from core.engineering_memory.validators import MemoryRecordValidator, ValidationError

class EngineeringMemoryService:
    """Service sans base secondaire : Obsidian reste le lieu d'écriture principal."""

    def __init__(
        self,
        root: Path,
        registry: EngineeringMemoryRegistry | None = None,
        *,
        require_existing_destination: bool = False,
    ):
        self.root = root.expanduser()
        self.registry = registry or EngineeringMemoryRegistry()
        self.persistence = ObsidianPersistence(
            self.root,
            self.registry,
            require_existing_destination=require_existing_destination,
        )
        self._audit_log_path = self.root / "_meta" / "MEMORY_EVENT_LOG.ndjson"

    def destination_status(self, record_type: RecordType | str) -> dict[str, Any]:
        """Décrit la destination d'un type d'enregistrement — lecture seule.

        Permet à un agent ou à une interface de vérifier une destination
        avant toute écriture, sans rien créer ni modifier dans le corpus.

        Args:
            record_type: Type d'enregistrement à décrire.

        Returns:
            Dictionnaire décrivant la destination et son existence.
        """
        destination = self.registry.destination_for(record_type)
        return {
            "record_type": str(record_type),
            "relative_directory": destination.relative_directory,
            "schema_name": destination.schema_name,
            "naming": destination.naming,
            "exists": self.registry.destination_exists(self.root, record_type),
        }

    def corpus_mapping(self) -> dict[str, dict[str, str]]:
        """Retourne la correspondance canonique type → destination (lecture seule)."""
        return self.registry.corpus_mapping()

    def validate(self, record: MemoryRecord) -> MemoryRecord:
        if not self.registry.is_status_allowed(record.record_type, record.status):
            raise ValidationError(f"status {record.status} is not allowed")
        return MemoryRecordValidator.validate(record)

    def record(self, record: MemoryRecord) -> MemoryRecord:
        validated = self.validate(record)
        SecurityPolicy.validate_record(validated)
        try:
            path = self.persistence.write(validated)
            SecurityPolicy.ensure_path_in_root(self.root, path)
        except DuplicateRecordError:
            raise
        validated.repository_path = path
        self._append_audit(validated, path)
        return validated

    def collect_event(self, record: MemoryRecord) -> MemoryRecord:
        return self.record(record)

    def get(self, record_id: str) -> MemoryRecord | None:
        return self.persistence.read(record_id)

    def search(
        self,
        *,
        component: str | None = None,
        record_type: str | None = None,
        status: str | None = None,
    ) -> list[MemoryRecord]:
        records = self.persistence.list_records(record_type=record_type)
        results: list[MemoryRecord] = []
        for record in records:
            if component is not None and component not in record.components:
                continue
            if status is not None and record.status != status:
                continue
            results.append(record)
        return results

    def search_records(self, **filters: str | None) -> list[MemoryRecord]:
        # Small compatibility helper to avoid duplicating search semantics.
        return self.search(
            component=filters.get("component"),
            record_type=filters.get("record_type"),
            status=filters.get("status"),
        )

    def component_history(self, component: str) -> list[MemoryRecord]:
        return self.search(component=component)

    def verify_integrity(self) -> dict[str, int | list[str]]:
        report = self.persistence.integrity_report()
        report["registry_destination"] = "loaded"
        return report

    def repository_path(self, record_id: str, record_type: RecordType | str | None = None) -> Path:
        # This helper is intentionally deterministic for callers that do not
        # need the validation state.
        _ = record_type
        existing = self.persistence.read(record_id)
        if existing is not None:
            if existing.repository_path is not None:
                return existing.repository_path
        if not isinstance(record_type, RecordType):
            raise ValidationError("record_type is required to resolve an unknown path")
        destination = self.registry.relative_path_for(record_type, record_id, record_id)
        return self.root / destination

    def _append_audit(self, record: MemoryRecord, path: Path) -> None:
        try:
            self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            line = f"{record.created_at}\t{record.id}\t{record.status}\t{path}\n"
            with self._audit_log_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError:
            raise ValidationError("could not write the memory audit log")
