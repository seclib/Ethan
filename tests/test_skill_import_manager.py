"""Tests Core - import_manager.py."""

from __future__ import annotations

import io
import zipfile

import pytest

from core.skills.import_manager import SkillImportManager, expand_uploads
from core.skills.store import SkillStore
from core.state.record_store import CoreRecordStore


def b(value: str) -> bytes:
    return value.encode("utf-8")


@pytest.mark.asyncio
async def test_import_valid_skill_appears_in_store() -> None:
    store = SkillStore(CoreRecordStore())
    manager = SkillImportManager(store)
    files = [("demo/SKILL.md", b("---\nname: demo-skill\ndescription: Demo\ntags:\n- a\n---\n\n# Instructions\n\nCorps\n"))]
    result = await manager.import_files(files)
    assert result["imported"] == 1
    assert result["invalid"] == 0
    skills = await store.list_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "demo-skill"
    assert skills[0]["is_active"] is False
    assert skills[0]["meta"].get("import_checksum")


@pytest.mark.asyncio
async def test_multiple_skills_single_parent_and_invalid() -> None:
    store = SkillStore(CoreRecordStore())
    manager = SkillImportManager(store)
    files = [
        ("skills/a/SKILL.md", b("---\nname: skill-a\ndescription: A\n---\n\ncorps A\n")),
        ("skills/b/SKILL.md", b("---\nname: skill-b\ndescription: B\n---\n\ncorps B\n")),
        ("skills/bad/SKILL.md", b("pas de frontmatter\n")),
        ("skills/notes/readme.md", b("documentation obscure\n")),
    ]
    detection = await manager.scan(files)
    assert detection["detected_skills"] == 3
    assert detection["ambiguous"]
    result = await manager.import_files(files)
    assert result["imported"] == 2
    assert result["invalid"] == 1
    assert result["errors"]


@pytest.mark.asyncio
async def test_duplicates_are_detected_and_not_reimported() -> None:
    store = SkillStore(CoreRecordStore())
    manager = SkillImportManager(store)
    md = b("---\nname: dup-skill\ndescription: D\n---\n\ncorps\n")
    first = await manager.import_files([("dup/SKILL.md", md)])
    assert first["imported"] == 1
    second = await manager.import_files([("dup/SKILL.md", md)])
    assert second["imported"] == 0
    assert second["skipped_existing"] == 1 or second["skipped_conflict"] == 1


def test_expand_uploads_rejects_traversal_in_zip() -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../evil.md", "x")
    _expanded, errors = expand_uploads([("bundle.zip", buf.getvalue())])
    assert errors
    assert any(e.get("code") == 422 for e in errors)


def test_expand_uploads_rejects_unsafe_file_name() -> None:
    _expanded, errors = expand_uploads([("../unsafe/SKILL.md", b("---\nname: x\ndescription: y\n---\n\ncorps\n"))])
    assert errors and errors[0]["code"] == 422


@pytest.mark.asyncio
async def test_scan_does_not_install() -> None:
    store = SkillStore(CoreRecordStore())
    manager = SkillImportManager(store)
    await manager.scan([("s/SKILL.md", b("---\nname: scan-only\ndescription: D\n---\n\ncorps\n"))])
    assert await store.list_skills() == []


@pytest.mark.asyncio
async def test_nested_skills_keep_companions_with_nearest_skill() -> None:
    store = SkillStore(CoreRecordStore())
    manager = SkillImportManager(store)
    files = [
        ("outer/SKILL.md", b("---\nname: outer\ndescription: Outer\n---\n\ncorps\n")),
        ("outer/inner/SKILL.md", b("---\nname: inner\ndescription: Inner\n---\n\ncorps\n")),
        ("outer/inner/resource.txt", b("nested resource\n")),
        ("outer/shared.txt", b("shared resource\n")),
    ]
    detection = await manager.scan(files)
    by_path = {item["source_path"]: item for item in detection["items"]}
    assert by_path["outer/SKILL.md"]["resources"] == ["outer/shared.txt"]
    assert by_path["outer/inner/SKILL.md"]["resources"] == ["outer/inner/resource.txt"]
