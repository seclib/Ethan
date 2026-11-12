"""Tests for the read-only Engineering Memory vault service.

The vault never writes, moves or deletes anything — these tests create a
temporary root fixture and verify browsing, search, backlinks and the
path-traversal guard. Nothing outside the fixture tree is touched.
"""

from __future__ import annotations

import pytest

from core.engineering_memory.vault import VaultError, VaultService


@pytest.fixture()
def vault_root(tmp_path):
    root = tmp_path / "vault"
    (root / "docs" / "nested").mkdir(parents=True)
    (root / "docs" / "architecture.md").write_text(
        "# Architecture\nSee [[decision-log]] and [[missing-doc]].\n", encoding="utf-8"
    )
    (root / "docs" / "nested" / "decision-log.md").write_text(
        "# Decision log\nReferenced by [[architecture]].\n", encoding="utf-8"
    )
    (root / "data.json").write_text('{"key": "value"}', encoding="utf-8")
    (root / "data.csv").write_text("id,name\n1,alpha\n", encoding="utf-8")
    (root / "ignored.bin").write_bytes(b"\x00\x01\x02")
    (root / ".hidden").write_text("hidden", encoding="utf-8")
    return root


def test_tree_lists_allowlisted_files_only(vault_root):
    service = VaultService(root=vault_root)
    tree = service.tree()
    assert tree["type"] == "directory"
    names = _collect_names(tree)
    assert "architecture.md" in names
    assert "decision-log.md" in names
    assert "data.json" in names
    assert "data.csv" in names
    assert "ignored.bin" not in names
    assert ".hidden" not in names


def test_read_file_returns_content_and_metadata(vault_root):
    service = VaultService(root=vault_root)
    info = service.read("docs/architecture.md")
    assert info["content"].startswith("# Architecture")
    assert info["line_count"] > 0
    assert info["markdown"] is True
    assert info["path"] == "docs/architecture.md"


def test_read_rejects_path_traversal(vault_root):
    service = VaultService(root=vault_root)
    with pytest.raises(VaultError):
        service.read("../outside.md")
    with pytest.raises(VaultError):
        service.read("docs/../../etc/passwd")


def test_read_rejects_unknown_file_type(vault_root):
    service = VaultService(root=vault_root)
    with pytest.raises(VaultError):
        service.read("ignored.bin")


def test_read_missing_file_raises(vault_root):
    service = VaultService(root=vault_root)
    with pytest.raises(VaultError):
        service.read("docs/does-not-exist.md")


def test_search_finds_literal_hits(vault_root):
    service = VaultService(root=vault_root)
    hits = service.search("architecture", limit=10)
    paths = {hit["path"] for hit in hits}
    assert any("architecture.md" in path for path in paths)
    assert all(hit["line"] >= 1 for hit in hits)
    assert all(hit["snippet"] for hit in hits)


def test_search_rejects_empty_query(vault_root):
    service = VaultService(root=vault_root)
    with pytest.raises(VaultError):
        service.search("   ")


def test_backlinks_resolves_wikilinks(vault_root):
    service = VaultService(root=vault_root)
    backlinks = service.backlinks("docs/nested/decision-log.md")
    assert any("architecture.md" in entry["path"] for entry in backlinks)


def test_backlinks_excludes_self(vault_root):
    service = VaultService(root=vault_root)
    backlinks = service.backlinks("docs/architecture.md")
    assert all("architecture.md" not in entry["path"] for entry in backlinks)


def test_graph_resolves_wikilinks(vault_root):
    service = VaultService(root=vault_root)
    graph = service.graph(limit_nodes=10)
    paths = {node["path"] for node in graph["nodes"]}
    assert any("architecture.md" in path for path in paths)
    sources = {(edge["source"], edge["target"]) for edge in graph["edges"]}
    assert (
        "docs/architecture.md",
        "docs/nested/decision-log.md",
    ) in sources


def test_missing_root_raises(tmp_path):
    with pytest.raises(VaultError):
        VaultService(root=tmp_path / "does-not-exist")


def test_write_roundtrip_outside_archives(vault_root):
    service = VaultService(root=vault_root)
    written = service.write("docs/new-note.md", "# New\nHello [[architecture]].\n")
    assert "# New" in written["content"]
    assert service.read("docs/new-note.md")["content"].startswith("# New")


def test_write_refuses_archives(vault_root):
    (vault_root / "Archives").mkdir()
    (vault_root / "Archives" / "original.md").write_text("archive", encoding="utf-8")
    service = VaultService(root=vault_root)
    with pytest.raises(VaultError):
        service.write("Archives/original.md", "tampered")
    assert (vault_root / "Archives" / "original.md").read_text(encoding="utf-8") == "archive"


def test_write_refuses_traversal(vault_root):
    service = VaultService(root=vault_root)
    with pytest.raises(VaultError):
        service.write("../escape.md", "nope")


def test_resolve_wikilink(vault_root):
    service = VaultService(root=vault_root)
    assert service.resolve_wikilink("architecture")["resolved"] == "docs/architecture.md"
    assert service.resolve_wikilink("decision-log")["resolved"] == "docs/nested/decision-log.md"
    assert service.resolve_wikilink("missing-thing")["resolved"] is None


def _collect_names(node) -> set[str]:
    names: set[str] = set()

    def walk(n):
        for child in n.get("children", []):
            if child["type"] == "file":
                names.add(child["name"])
            else:
                walk(child)

    walk(node)
    return names
