"""Router-level tests for the Engineering Memory vault endpoints.

The vault routes are strictly read-only except for the managed write
endpoint, which must refuse the raw Archives. Uses a temporary vault root
and dependency overrides, exactly like the pre-existing router tests.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from interfaces.api.routers.engineering_memory import (
    memory_read_permission,
    memory_record_permission,
    router,
)


def _client(tmp_path: Path) -> tuple[TestClient, Path]:
    root = tmp_path / "Obsidian"
    root.mkdir(parents=True)
    os.environ["ETHAN_ENGINEERING_MEMORY_ROOT"] = str(root)
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[memory_read_permission] = lambda: True
    application.dependency_overrides[memory_record_permission] = lambda: True
    return TestClient(application), root


def test_vault_tree_lists_markdown(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("# Note\nSee [[other]].\n", encoding="utf-8")
    response = client.get("/v1/memory/vault/tree")
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "directory"
    assert "docs" in str(payload)


def test_vault_file_read_and_traversal_rejected(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    (root / "note.md").write_text("# Title\n", encoding="utf-8")
    ok = client.get("/v1/memory/vault/file", params={"path": "note.md"})
    assert ok.status_code == 200
    assert "# Title" in ok.json()["content"]

    rejected = client.get("/v1/memory/vault/file", params={"path": "../secret.md"})
    assert rejected.status_code == 404


def test_vault_search_and_backlinks(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    (root / "target.md").write_text("# Target\n", encoding="utf-8")
    (root / "source.md").write_text("Links to [[target]] here.\n", encoding="utf-8")
    hits = client.get("/v1/memory/vault/search", params={"q": "target"})
    assert hits.status_code == 200
    assert any("target.md" in hit["path"] for hit in hits.json()["hits"])

    backlinks = client.get("/v1/memory/vault/backlinks", params={"path": "target.md"})
    assert backlinks.status_code == 200
    assert any("source.md" in entry["path"] for entry in backlinks.json()["backlinks"])


def test_vault_write_blocks_archives(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    archives = root / "Archives"
    archives.mkdir()
    (archives / "original.md").write_text("archive", encoding="utf-8")

    response = client.post("/v1/memory/vault/file", json={"path": "Archives/original.md", "content": "tampered"})
    assert response.status_code == 403
    assert (archives / "original.md").read_text(encoding="utf-8") == "archive"


def test_vault_write_managed_document(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    response = client.post(
        "/v1/memory/vault/file",
        json={"path": "Knowledge/new-note.md", "content": "# New note\n"},
    )
    assert response.status_code == 200
    assert (root / "Knowledge" / "new-note.md").read_text(encoding="utf-8") == "# New note\n"


def test_vault_graph(tmp_path: Path) -> None:
    client, root = _client(tmp_path)
    (root / "a.md").write_text("Links [[b]].\n", encoding="utf-8")
    (root / "b.md").write_text("# B\n", encoding="utf-8")
    response = client.get("/v1/memory/vault/graph", params={"limit_nodes": 10})
    assert response.status_code == 200
    paths = {node["path"] for node in response.json()["nodes"]}
    assert "a.md" in paths
    assert "b.md" in paths


def test_memory_records_lists_without_v1_collision(tmp_path: Path) -> None:
    client, _root = _client(tmp_path)
    response = client.get("/v1/memory/records", params={"record_type": "component"})
    assert response.status_code == 200
    assert "results" in response.json()
