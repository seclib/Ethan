"""EventSchemaRegistry — Gestion des schémas d'événements.

Assure la gouvernance des événements :
- Enregistrement des schémas JSON Schema
- Validation des événements au runtime
- Versioning sémantique
- Migration automatique entre versions
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from core.types.event import Event

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Migration
# ──────────────────────────────────────────────


class Migration:
    """Migration d'une version à une autre d'un schéma d'événement."""

    def __init__(
        self,
        from_version: str,
        to_version: str,
        migrate_fn: Callable[[dict[str, Any]], dict[str, Any]],
        description: str = "",
    ):
        self.from_version = from_version
        self.to_version = to_version
        self.migrate_fn = migrate_fn
        self.description = description

    def apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Applique la migration au payload.

        Args:
            payload: Payload de l'événement à migrer

        Returns:
            Payload migré
        """
        return self.migrate_fn(payload)

    def __repr__(self) -> str:
        return f"Migration({self.from_version} → {self.to_version}: {self.description})"


# ──────────────────────────────────────────────
# Schema Registry
# ──────────────────────────────────────────────


@dataclass
class EventSchema:
    """Schéma d'un type d'événement.

    Stocké en mémoire et persistant dans PostgreSQL.
    """
    event_type: str
    version: str
    schema: dict[str, Any]  # JSON Schema
    description: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)


class EventSchemaRegistry:
    """Registry des schémas d'événements.

    Capable de :
    - Enregistrer des schémas avec version
    - Valider des événements contre leur schéma
    - Migrer des événements entre versions
    """

    def __init__(self):
        self._schemas: dict[tuple[str, str], EventSchema] = {}
        self._migrations: dict[str, list[Migration]] = {}
        self._latest_versions: dict[str, str] = {}

    # ──────────────────────────────────────────────
    # Registration
    # ──────────────────────────────────────────────

    def register_schema(
        self,
        event_type: str,
        version: str,
        schema: dict[str, Any],
        description: str = "",
        examples: list[dict[str, Any]] | None = None,
    ) -> None:
        """Enregistre un schéma d'événement.

        Args:
            event_type: Type d'événement (e.g., \"interface.command\")
            version: Version semver (e.g., \"1.0.0\")
            schema: Schéma JSON Schema
            description: Description optionnelle
            examples: Exemples optionnels
        """
        key = (event_type, version)
        self._schemas[key] = EventSchema(
            event_type=event_type,
            version=version,
            schema=schema,
            description=description,
            examples=examples or [],
        )

        # Mettre à jour la dernière version
        current = self._latest_versions.get(event_type)
        if current is None or self._compare_versions(version, current) > 0:
            self._latest_versions[event_type] = version

        logger.debug(
            "Schema registered: %s v%s", event_type, version
        )

    def register_migration(
        self,
        event_type: str,
        from_version: str,
        to_version: str,
        migrate_fn: Callable[[dict[str, Any]], dict[str, Any]],
        description: str = "",
    ) -> None:
        """Enregistre une migration entre deux versions d'un schéma.

        Args:
            event_type: Type d'événement
            from_version: Version source
            to_version: Version cible
            migrate_fn: Fonction de migration
            description: Description optionnelle
        """
        if event_type not in self._migrations:
            self._migrations[event_type] = []

        migration = Migration(
            from_version=from_version,
            to_version=to_version,
            migrate_fn=migrate_fn,
            description=description,
        )

        # Insérer dans l'ordre des versions
        self._migrations[event_type].append(migration)

        logger.debug(
            "Migration registered: %s %s → %s",
            event_type, from_version, to_version,
        )

    # ──────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────

    def validate(self, event: Event) -> list[str]:
        """Valide un événement contre son schéma enregistré.

        Args:
            event: Événement à valider

        Returns:
            Liste des erreurs de validation (vide si l'événement est valide)
        """
        version = event.metadata.get("version", "1.0.0")
        schema = self._schemas.get((event.type.value, version))

        if schema is None:
            # Si le schéma exact n'existe pas, essayer la dernière version
            latest = self._latest_versions.get(event.type.value)
            if latest and latest != version:
                try:
                    migrated = self.migrate(event, latest)
                    schema = self._schemas.get((event.type.value, latest))
                    if schema is None:
                        return [f"No schema found for {event.type.value}"]
                except Exception as e:
                    return [f"Migration failed: {e}"]
            else:
                return [f"No schema found for {event.type.value} v{version}"]

        if schema is None:
            return [f"No schema found for {event.type.value}"]

        errors: list[str] = []
        payload = event.payload

        # Vérifier les champs requis
        required = schema.schema.get("required", [])
        for field_name in required:
            if field_name not in payload:
                errors.append(f"Missing required field: '{field_name}'")

        # Vérifier les types des propriétés
        properties = schema.schema.get("properties", {})
        # Mapping Python types -> JSON Schema types
        PYTHON_TO_JSON_TYPE = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "NoneType": "null",
        }

        for field_name, field_schema in properties.items():
            if field_name in payload:
                expected_type = field_schema.get("type")
                if expected_type:
                    actual_type = type(payload[field_name]).__name__
                    mapped_type = PYTHON_TO_JSON_TYPE.get(actual_type, actual_type)
                    if mapped_type != expected_type:
                        errors.append(
                            f"Field '{field_name}': expected {expected_type}, got {mapped_type}"
                        )

        return errors

    def is_valid(self, event: Event) -> bool:
        """Vérifie rapidement si un événement est valide.

        Args:
            event: Événement à valider

        Returns:
            True si l'événement est valide
        """
        errors = self.validate(event)
        if errors:
            for error in errors:
                logger.warning("Event validation error: %s", error)
            return False
        return True

    # ──────────────────────────────────────────────
    # Migration
    # ──────────────────────────────────────────────

    def migrate(self, event: Event, target_version: str) -> Event:
        """Migre un événement vers une version cible.

        Args:
            event: Événement à migrer
            target_version: Version cible

        Returns:
            Événement migré

        Raises:
            ValueError: Si la migration n'est pas possible
        """
        current_version = event.metadata.get("version", "1.0.0")

        if current_version == target_version:
            return event

        # Trouver le chemin de migration
        migrations = self._find_migration_path(
            event.type.value, current_version, target_version
        )

        if not migrations:
            raise ValueError(
                f"No migration path from {current_version} to {target_version} "
                f"for {event.type.value}"
            )

        # Appliquer les migrations
        payload = dict(event.payload)
        for migration in migrations:
            try:
                payload = migration.apply(payload)
                logger.debug(
                    "Applied migration: %s %s → %s",
                    event.type.value, migration.from_version, migration.to_version,
                )
            except Exception as e:
                raise ValueError(
                    f"Migration failed at {migration.from_version} → {migration.to_version}: {e}"
                ) from e

        # Créer l'événement migré
        return Event(
            id=event.id,
            type=event.type,
            source=event.source,
            timestamp=event.timestamp,
            payload=payload,
            metadata={**event.metadata, "version": target_version},
        )

    def _find_migration_path(
        self,
        event_type: str,
        from_version: str,
        to_version: str,
    ) -> list[Migration]:
        """Trouve le chemin de migration entre deux versions.

        Args:
            event_type: Type d'événement
            from_version: Version source
            to_version: Version cible

        Returns:
            Liste des migrations à appliquer dans l'ordre
        """
        migrations = self._migrations.get(event_type, [])

        # Filtrer les migrations pertinentes
        path: list[Migration] = []
        current = from_version

        while current != to_version:
            found = False
            for migration in migrations:
                if migration.from_version == current:
                    # Vérifier qu'on va dans la bonne direction
                    cmp = self._compare_versions(migration.to_version, to_version)
                    if cmp <= 0:
                        path.append(migration)
                        current = migration.to_version
                        found = True
                        break
            if not found:
                return []

        return path

    # ──────────────────────────────────────────────
    # Query
    # ──────────────────────────────────────────────

    def get_schema(
        self,
        event_type: str,
        version: str | None = None,
    ) -> EventSchema | None:
        """Récupère le schéma d'un événement.

        Args:
            event_type: Type d'événement
            version: Version (utilise la dernière si non spécifiée)

        Returns:
            Le schéma, ou None si non trouvé
        """
        if version is None:
            version = self._latest_versions.get(event_type, "1.0.0")

        return self._schemas.get((event_type, version))

    def list_event_types(self) -> list[str]:
        """Liste tous les types d'événements enregistrés.

        Returns:
            Liste des types d'événements
        """
        return list(self._latest_versions.keys())

    def list_versions(self, event_type: str) -> list[str]:
        """Liste toutes les versions d'un type d'événement.

        Args:
            event_type: Type d'événement

        Returns:
            Liste des versions, triées
        """
        versions = [
            version
            for (e_type, version) in self._schemas
            if e_type == event_type
        ]
        return sorted(versions, key=self._compare_versions_key, reverse=True)

    def count(self) -> int:
        """Nombre de schémas enregistrés.

        Returns:
            Nombre de schémas
        """
        return len(self._schemas)

    # ──────────────────────────────────────────────
    # Utils
    # ──────────────────────────────────────────────

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare deux versions semver.

        Args:
            v1: Première version
            v2: Deuxième version

        Returns:
            < 0 si v1 < v2, > 0 si v1 > v2, 0 si égal
        """
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        for i in range(3):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 != p2:
                return p1 - p2
        return 0

    @staticmethod
    def _compare_versions_key(version: str) -> tuple[int, ...]:
        """Convertit une version semver en clé de tri."""
        return tuple(int(x) for x in version.split("."))