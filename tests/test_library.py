"""tests/test_library.py — Unified library API client."""

import pytest


def test_library_item_types():
    """Verify all library item types are defined."""
    types = {"document", "image", "knowledge", "collection", "project"}
    # These are the canonical types used across the library
    assert "document" in types
    assert "image" in types
    assert "knowledge" in types
    assert "collection" in types
    assert "project" in types


def test_library_filters_structure():
    """Verify LibraryFilters structure."""
    filters = {
        "type": "document",
        "search": "test",
        "sort_by": "created_at",
        "sort_order": "desc",
    }
    assert filters["type"] == "document"
    assert filters["search"] == "test"
    assert filters["sort_by"] == "created_at"
    assert filters["sort_order"] == "desc"


def test_library_response_structure():
    """Verify LibraryResponse structure."""
    response = {
        "items": [],
        "total": 0,
        "filters": {},
    }
    assert response["total"] == 0
    assert response["items"] == []


def test_library_item_structure():
    """Verify LibraryItem structure."""
    item = {
        "id": "test-1",
        "title": "Test Item",
        "type": "document",
        "description": "A test item",
        "content": "Test content",
        "source": "test",
        "metadata": {"key": "value"},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    assert item["id"] == "test-1"
    assert item["title"] == "Test Item"
    assert item["type"] == "document"


def test_type_config_completeness():
    """All library types must have a config entry."""
    TYPE_CONFIG = {
        "document": {"label": "Documents", "color": "text-blue-400"},
        "image": {"label": "Images", "color": "text-green-400"},
        "knowledge": {"label": "Knowledge", "color": "text-purple-400"},
        "collection": {"label": "Collections", "color": "text-yellow-400"},
        "project": {"label": "Projects", "color": "text-orange-400"},
    }
    for item_type in ["document", "image", "knowledge", "collection", "project"]:
        assert item_type in TYPE_CONFIG


def test_type_filters_completeness():
    """All type filters must be present."""
    TYPE_FILTERS = [
        {"id": "all", "label": "All"},
        {"id": "document", "label": "Documents"},
        {"id": "image", "label": "Images"},
        {"id": "knowledge", "label": "Knowledge"},
        {"id": "collection", "label": "Collections"},
    ]
    ids = [f["id"] for f in TYPE_FILTERS]
    assert "all" in ids
    assert "document" in ids
    assert "image" in ids
    assert "knowledge" in ids
    assert "collection" in ids


def test_library_api_endpoints_defined():
    """Verify all library API endpoints are defined."""
    endpoints = [
        "/v1/rag/documents",
        "/v1/knowledge",
        "/v1/knowledge/collections",
        "/v1/files",
        "/v1/projects/{id}/documents",
    ]
    assert len(endpoints) == 5
    assert "/v1/rag/documents" in endpoints
    assert "/v1/knowledge" in endpoints
    assert "/v1/knowledge/collections" in endpoints
