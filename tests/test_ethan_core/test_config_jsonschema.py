"""Tests for the JSON Schema generator (core/config/jsonschema.py)."""

import pytest

from core.config.jsonschema import config_to_json_schema, get_domains


def test_get_domains_contains_expected():
    domains = get_domains()
    assert "rag" in domains
    assert "providers" in domains
    assert "models" in domains
    assert "runtime" in domains


def test_full_schema_is_object():
    schema = config_to_json_schema()
    assert schema["type"] == "object"
    assert "properties" in schema
    props = schema["properties"]
    assert "rag" in props
    assert "providers" in props
    assert "models" in props


def test_rag_domain_schema_types():
    schema = config_to_json_schema("rag")
    props = schema["properties"]
    assert props["enabled"]["type"] == "boolean"
    assert props["chunk_size"]["type"] == "integer"
    assert props["chunk_overlap"]["type"] == "integer"
    assert props["top_k"]["type"] == "integer"
    assert props["embedding_model"]["type"] == "string"
    assert props["similarity_threshold"]["type"] == "number"


def test_rag_domain_defaults():
    schema = config_to_json_schema("rag")
    props = schema["properties"]
    assert props["enabled"]["default"] is True
    assert props["chunk_size"]["default"] == 1000
    assert props["top_k"]["default"] == 5


def test_unknown_domain_raises():
    with pytest.raises(KeyError):
        config_to_json_schema("does_not_exist")


def test_runtime_enum_schema():
    schema = config_to_json_schema("runtime")
    props = schema["properties"]
    assert props["mode"]["type"] == "string"
    assert "enum" in props["mode"]
    assert "auto" in props["mode"]["enum"]
    assert "standalone" in props["mode"]["enum"]
    assert "distributed" in props["mode"]["enum"]


def test_nested_dataclass_schema():
    schema = config_to_json_schema("providers")
    props = schema["properties"]
    assert props["providers"]["type"] == "object"
    assert props["active"]["type"] == "string"


def test_config_router_schema_routes():
    """Les routes /config/schema existent dans le router FastAPI."""
    fastapi = pytest.importorskip("fastapi")
    from interfaces.api.routers.config import router

    paths = {route.path for route in router.routes}
    assert "/config/schema" in paths
    assert "/config/schema/{domain}" in paths

    # Les routes /schema doivent être déclarées avant /{domain}
    # pour ne pas être capturées par le routeur générique.
    route_order = [
        route.path
        for route in router.routes
        if getattr(route, "path", "").startswith("/config")
    ]
    assert route_order.index("/config/schema") < route_order.index("/config/{domain}")
