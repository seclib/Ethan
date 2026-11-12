"""JSON Schema generator for ETHAN configuration.

Generates JSON Schema (Draft 2020-12) from the typed dataclasses in
``core/config/schema.py``.  The WebUI (and any other interface) can consume
these schemas to auto-generate settings forms, while ETHAN Core remains the
single source of truth for the configuration structure.

The generated schema contains only types, descriptions and default values —
**never** secret values (API keys, tokens, passwords).
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Any, get_args, get_origin


def config_to_json_schema(domain: str | None = None) -> dict[str, Any]:
    """Generate a JSON Schema for one or all configuration domains.

    Args:
        domain: Optional domain name (e.g. ``"rag"``, ``"providers"``).
                If ``None``, returns the full ``ConfigSchema`` object schema.

    Returns:
        JSON Schema Draft 2020-12 dict describing the configuration.
    """
    from core.config.schema import ConfigSchema

    if domain is not None:
        valid_domains = {f.name for f in dataclasses.fields(ConfigSchema)}
        if domain not in valid_domains:
            raise KeyError(f"Unknown configuration domain '{domain}'")
        type_hints = _resolve_type_hints(ConfigSchema)
        if domain not in type_hints:
            raise KeyError(f"Unknown configuration domain '{domain}'")
        return _dataclass_to_schema(type_hints[domain], title=domain)

    return _dataclass_to_schema(ConfigSchema, title="ConfigSchema")


def get_domains() -> list[str]:
    """Return the list of configurable domain names."""
    from core.config.schema import ConfigSchema

    return [f.name for f in dataclasses.fields(ConfigSchema)]


def _resolve_type_hints(dataclass_type: type) -> dict[str, Any]:
    """Resolve real type annotations for a dataclass (handles forward refs)."""
    from typing import get_type_hints

    try:
        return get_type_hints(dataclass_type)
    except Exception:
        return {}


def _dataclass_to_schema(
    dataclass_type: type,
    title: str | None = None,
) -> dict[str, Any]:
    """Convert a dataclass type into a JSON Schema object."""
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    if title:
        schema["title"] = title

    type_hints = dataclasses.MISSING
    try:
        from typing import get_type_hints

        type_hints = get_type_hints(dataclass_type)
    except Exception:
        type_hints = dataclasses.MISSING

    for field in dataclasses.fields(dataclass_type):
        annotation: Any = field.type
        if type_hints is not dataclasses.MISSING and field.name in type_hints:
            annotation = type_hints[field.name]
        field_schema = _type_to_schema(annotation)
        if field.metadata.get("description"):
            field_schema["description"] = field.metadata["description"]

        default = _field_default(field)
        if default is not dataclasses.MISSING:
            field_schema["default"] = default

        schema["properties"][field.name] = field_schema

    required = [
        f.name
        for f in dataclasses.fields(dataclass_type)
        if _field_default(f) is dataclasses.MISSING
    ]
    if required:
        schema["required"] = required

    return schema


def _field_default(field: dataclasses.Field) -> Any:
    """Return the field default or ``dataclasses.MISSING``."""
    if field.default is not dataclasses.MISSING:
        return field.default
    if field.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
        try:
            return field.default_factory()  # type: ignore[misc]
        except Exception:
            return dataclasses.MISSING
    return dataclasses.MISSING


def _type_to_schema(annotation: Any) -> dict[str, Any]:
    """Convert a Python type annotation into a JSON Schema fragment."""
    origin = get_origin(annotation)

    if origin is None and annotation is type(None):
        return {"type": "null"}

    if origin is not None:
        args = list(get_args(annotation))
        if type(None) in args:
            non_none = [a for a in args if a is not type(None)]
            inner_schema = _type_to_schema(non_none[0]) if non_none else {"type": "null"}
            return {"anyOf": [inner_schema, {"type": "null"}]}

        if origin is list:
            items = get_args(annotation)
            return {
                "type": "array",
                "items": _type_to_schema(items[0]) if items else {"type": "object"},
                "uniqueItems": origin is set,
            }
        if origin is dict:
            return {"type": "object", "additionalProperties": True}

    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return {
            "type": "string",
            "enum": [member.value for member in annotation],  # type: ignore[union-attr]
        }

    if dataclasses.is_dataclass(annotation):
        from typing import cast

        dc_type = cast(type, annotation)
        return _dataclass_to_schema(dc_type, title=dc_type.__name__)

    if annotation is str:
        return {"type": "string"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}

    return {"type": "object", "additionalProperties": True}
