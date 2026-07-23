"""Tests pour EventSchemaRegistry."""

from __future__ import annotations

from core.registry.events import EventSchemaRegistry
from core.ethan_types.event import Event, EventType


class TestEventSchemaRegistry:
    """Tests du EventSchemaRegistry."""

    def test_register_schema(self, schema_registry: EventSchemaRegistry):
        """Enregistrement d'un schéma."""
        schema_registry.register_schema(
            event_type="test.event",
            version="1.0.0",
            schema={
                "type": "object",
                "properties": {
                    "cmd": {"type": "string"},
                    "args": {"type": "array"},
                },
                "required": ["cmd"],
            },
            description="Test event schema",
        )

        assert schema_registry.count() == 1
        assert "test.event" in schema_registry.list_event_types()

    def test_validate_valid_event(self, schema_registry: EventSchemaRegistry):
        """Validation d'un événement valide."""
        event_type = EventType.INTERFACE_COMMAND.value  # "ethan.interface.command"
        schema_registry.register_schema(
            event_type=event_type,
            version="1.0.0",
            schema={
                "type": "object",
                "properties": {
                    "cmd": {"type": "string"},
                },
                "required": ["cmd"],
            },
        )

        event = Event(
            type=EventType.INTERFACE_COMMAND,
            source="cli",
            payload={"cmd": "chat"},
            metadata={"version": "1.0.0"},
        )

        errors = schema_registry.validate(event)
        assert len(errors) == 0
        assert schema_registry.is_valid(event)

    def test_validate_invalid_event(self, schema_registry: EventSchemaRegistry):
        """Validation d'un événement invalide."""
        schema_registry.register_schema(
            event_type="interface.command",
            version="1.0.0",
            schema={
                "type": "object",
                "properties": {
                    "cmd": {"type": "string"},
                },
                "required": ["cmd"],
            },
        )

        event = Event(
            type=EventType.INTERFACE_COMMAND,
            source="cli",
            payload={"args": []},  # cmd manquant
            metadata={"version": "1.0.0"},
        )

        errors = schema_registry.validate(event)
        assert len(errors) > 0
        assert not schema_registry.is_valid(event)

    def test_validate_no_schema(self, schema_registry: EventSchemaRegistry):
        """Validation d'un événement sans schéma enregistré."""
        event = Event(
            type=EventType.SYSTEM_BOOT,
            source="system",
            payload={},
        )

        errors = schema_registry.validate(event)
        assert len(errors) > 0
        assert "No schema found" in errors[0]

    def test_schema_versioning(self, schema_registry: EventSchemaRegistry):
        """Gestion des versions d'un même type d'événement."""
        # V1
        schema_registry.register_schema(
            event_type="test.event",
            version="1.0.0",
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )

        # V2
        schema_registry.register_schema(
            event_type="test.event",
            version="2.0.0",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
                "required": ["name", "email"],
            },
        )

        versions = schema_registry.list_versions("test.event")
        assert len(versions) == 2
        assert "2.0.0" in versions
        assert "1.0.0" in versions

    def test_get_schema(self, schema_registry: EventSchemaRegistry):
        """Récupération d'un schéma."""
        schema_registry.register_schema(
            event_type="test.event",
            version="1.0.0",
            schema={"type": "object", "properties": {}},
        )

        schema = schema_registry.get_schema("test.event")
        assert schema is not None
        assert schema.version == "1.0.0"

        schema = schema_registry.get_schema("test.event", "1.0.0")
        assert schema is not None

        schema = schema_registry.get_schema("test.event", "2.0.0")
        assert schema is None

    def test_get_schema_not_found(self, schema_registry: EventSchemaRegistry):
        """Récupération d'un schéma inexistant."""
        schema = schema_registry.get_schema("nonexistent")
        assert schema is None

    def test_register_migration(self, schema_registry: EventSchemaRegistry):
        """Enregistrement d'une migration."""
        schema_registry.register_migration(
            event_type="test.event",
            from_version="1.0.0",
            to_version="2.0.0",
            migrate_fn=lambda payload: {**payload, "email": "unknown@example.com"},
            description="Add email field with default",
        )

        # Vérifier que la migration est accessible via le registry
        assert schema_registry._migrations.get("test.event") is not None
        assert len(schema_registry._migrations["test.event"]) == 1

    def test_migration_apply(self, schema_registry: EventSchemaRegistry):
        """Application d'une migration avec le bon EventType."""
        event_type_str = EventType.INTERFACE_COMMAND.value  # "ethan.interface.command"
        schema_registry.register_migration(
            event_type=event_type_str,
            from_version="1.0.0",
            to_version="2.0.0",
            migrate_fn=lambda payload: {**payload, "email": "unknown@example.com"},
        )
        schema_registry.register_schema(
            event_type=event_type_str,
            version="1.0.0",
            schema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        )
        schema_registry.register_schema(
            event_type=event_type_str,
            version="2.0.0",
            schema={"type": "object", "properties": {"name": {"type": "string"}, "email": {"type": "string"}}, "required": ["name", "email"]},
        )

        event = Event(
            type=EventType.INTERFACE_COMMAND,
            source="test",
            payload={"name": "test"},
            metadata={"version": "1.0.0"},
        )

        migrated = schema_registry.migrate(event, "2.0.0")
        assert migrated.payload["name"] == "test"
        assert migrated.payload["email"] == "unknown@example.com"
        assert migrated.metadata["version"] == "2.0.0"

    def test_migration_same_version(self, schema_registry: EventSchemaRegistry):
        """Migration vers la même version."""
        event = Event(
            type=EventType.INTERFACE_COMMAND,
            source="test",
            payload={"name": "test"},
            metadata={"version": "1.0.0"},
        )

        migrated = schema_registry.migrate(event, "1.0.0")
        assert migrated == event

    def test_migration_no_path(self, schema_registry: EventSchemaRegistry):
        """Migration sans chemin possible."""
        event = Event(
            type=EventType.INTERFACE_COMMAND,
            source="test",
            payload={"name": "test"},
            metadata={"version": "1.0.0"},
        )

        import pytest
        with pytest.raises(ValueError, match="No migration path"):
            schema_registry.migrate(event, "99.0.0")

    def test_compare_versions(self, schema_registry: EventSchemaRegistry):
        """Comparaison de versions semver."""
        assert EventSchemaRegistry._compare_versions("1.0.0", "1.0.0") == 0
        assert EventSchemaRegistry._compare_versions("2.0.0", "1.0.0") > 0
        assert EventSchemaRegistry._compare_versions("1.0.0", "2.0.0") < 0
        assert EventSchemaRegistry._compare_versions("1.1.0", "1.0.0") > 0
        assert EventSchemaRegistry._compare_versions("1.0.1", "1.0.0") > 0