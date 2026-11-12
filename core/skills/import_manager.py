"""Skill import manager — bundles detection, preview and installation.

Core owns Skill import semantics (as it owns the SkillStore).  The WebUI
only exchanges bytes and display names; it never parses frontmatter or
mutates skill records itself.

Supported input shapes:
- a single ``SKILL.md`` (with optional companion resources in the same
  directory);
- a directory containing one Skill (root-level ``SKILL.md``);
- a directory containing several sibling Skills (each sub-directory with
  its own ``SKILL.md``);
- a ``.zip`` archive whose members preserve the relative directory layout.

The manager is intentionally deterministic: it never executes imported
content, never follows absolute/escaping paths and never activates imported
skills.  A detection that cannot be interpreted conservatively is reported
as invalid rather than guessed.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from typing import Any

import yaml

_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MiB per member
_MAX_FILES = 5_000
_MAX_ARCHIVE_BYTES = 100 * 1024 * 1024


def _safe_relpath(raw: str) -> str | None:
    """Return a normalised RELATIVE path or None when it is unsafe."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.replace("\\", "/")
    # Strip leading "./", absolute prefixes or drive letters.
    parts = []
    for seg in value.split("/"):
        if seg in ("", ".",):
            continue
        if seg == "..":
            return None
        # Reject URL/Windows drive components and null bytes.
        if "\x00" in seg or ":" in seg:
            return None
        parts.append(seg)
    if not parts:
        return None
    if len(parts) > 64:
        return None
    return "/".join(parts)


def expand_uploads(
    files: list[tuple[str, bytes]],
    *,
    max_files: int = _MAX_FILES,
    max_file_size: int = _MAX_FILE_SIZE,
) -> tuple[list[tuple[str, bytes]], list[dict[str, Any]]]:
    """Expand archives and validate upload inputs.  Returns (files, errors)."""
    out: list[tuple[str, bytes]] = []
    errors: list[dict[str, Any]] = []

    for filename, raw in files:
        if not isinstance(raw, (bytes, bytearray)):
            errors.append(
                {"filename": str(filename), "code": 422, "detail": "File content must be bytes"}
            )
            continue
        data = bytes(raw)
        if len(data) == 0:
            errors.append({"filename": str(filename), "code": 422, "detail": "Empty file"})
            continue
        if len(data) > max_file_size:
            errors.append(
                {
                    "filename": str(filename),
                    "code": 413,
                    "detail": f"File too large ({len(data)} bytes, max {max_file_size})",
                }
            )
            continue
        rel = _safe_relpath(str(filename))
        if rel is None:
            errors.append(
                {"filename": str(filename), "code": 422, "detail": "Unsafe file name path"}
            )
            continue
        if _is_archive(rel):
            # Expand in-memory.  Failures are reported per archive, not fatal.
            try:
                expanded = _expand_archive(rel, data)
            except Exception as exc:  # noqa: BLE001 - archives can be malformed
                errors.append({"filename": rel, "code": 422, "detail": f"Invalid archive: {exc}"})
                continue
            if not expanded:
                errors.append(
                    {
                        "filename": rel,
                        "code": 422,
                        "detail": "Archive is empty or has no supported members",
                    }
                )
                continue
            # Enforce a global bound on the number of expanded members.
            if len(out) + len(expanded) > max_files:
                errors.append(
                    {
                        "filename": rel,
                        "code": 413,
                        "detail": f"Archive expands to too many files (limit {max_files})",
                    }
                )
                continue
            out.extend(expanded)
        else:
            if len(out) >= max_files:
                errors.append(
                {
                    "filename": rel,
                    "code": 413,
                    "detail": f"Too many files (limit {max_files})",
                }
            )
                continue
            out.append((rel, data))

    # Deduplicate by exact path while keeping the first occurrence.
    dedup: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for path, raw in out:
        if path in seen:
            continue
        seen.add(path)
        dedup.append((path, raw))
    return dedup, errors


def _is_archive(path: str) -> bool:
    return path.lower().endswith(".zip")


def _expand_archive(filename: str, data: bytes) -> list[tuple[str, bytes]]:
    if len(data) > _MAX_ARCHIVE_BYTES:
        raise ValueError("Archive too large")
    result: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        total_size = 0
        for info in zf.infolist():
            if info.is_dir():
                continue
            safe = _safe_relpath(info.filename)
            if safe is None:
                raise ValueError(f"Unsafe archive member: {info.filename!r}")
            member = zf.read(info)
            total_size += len(member)
            if total_size > _MAX_ARCHIVE_BYTES:
                raise ValueError("Archive expands beyond size limit (potential zip bomb)")
            if len(member) > _MAX_FILE_SIZE:
                raise ValueError(f"Archive member too large: {info.filename!r}")
            result.append((f"{_archive_stem(filename)}/{safe}", member))
    return result


def _archive_stem(filename: str) -> str:
    import os

    return os.path.splitext(filename)[0] or "archive"


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str] | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None
    return fm, parts[2].strip()


def _parse_skill(path: str, raw: bytes) -> dict[str, Any]:
    """Parse one SKILL.md.  Returns a dict with status/errors/data."""
    rel_name = path
    result: dict[str, Any] = {
        "source_path": rel_name,
        "status": "invalid",
        "errors": [],
        "name": None,
        "description": "",
        "version": "1.0.0",
        "author": "user",
        "tags": [],
        "content": "",
        "kind": "prompt",
        "steps": [],
        "required_tools": [],
        "valves": {},
        "meta": {},
        "resources": [],
        "preview": "",
    }

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        result["errors"].append("SKILL.md is not valid UTF-8")
        return result

    parsed = _parse_frontmatter(text)
    if parsed is None:
        result["errors"].append("Missing YAML frontmatter")
        return result
    fm, body = parsed

    if not isinstance(fm, dict):
        result["errors"].append("Frontmatter must be a mapping")
        return result

    directory = rel_name.rsplit("/", 1)[0] if "/" in rel_name else ""
    stem = directory.rstrip("/").split("/")[-1] if directory else rel_name.split(".")[0]
    fm_name = fm.get("name")
    name = str(fm_name).strip() if (fm_name is not None and str(fm_name).strip()) else stem
    if not name:
        result["errors"].append("Missing required field: name")
        return result

    description = fm.get("description", "")
    if description is None:
        description = ""
    description = str(description).strip()[:5000]
    if not description:
        result["errors"].append("Missing required field: description")
        return result

    kind = fm.get("kind", "prompt")
    if kind not in ("prompt", "pipeline"):
        result["errors"].append(f"Unsupported skill kind: {kind!r}")
        return result
    body = body.strip()
    if not body and kind == "prompt":
        result["errors"].append("Skill content body is required for prompt skills")
        return result
    if kind == "pipeline":
        raw_steps = fm.get("steps") or []
        if not isinstance(raw_steps, list):
            result["errors"].append("'steps' must be a list")
            return result
        steps = [s for s in raw_steps if isinstance(s, dict)]
        if not steps:
            result["errors"].append("Pipeline skills require non-empty 'steps'")
            return result
    else:
        steps = []

    tools = fm.get("required_tools") or []
    if not isinstance(tools, list):
        result["errors"].append("'required_tools' must be a list")
        return result
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    if not isinstance(tags, list):
        tags = []
    valves = fm.get("valves", {}) or {}
    if not isinstance(valves, dict):
        result["errors"].append("'valves' must be an object")
        return result

    author = fm.get("author")
    author = str(author).strip() if (author is not None and str(author).strip()) else "user"
    version = fm.get("version")
    version = str(version).strip() if (version is not None and str(version).strip()) else "1.0.0"

    meta: dict[str, Any] = dict(fm.get("meta") or {}) if isinstance(fm.get("meta"), dict) else {}
    meta["source_path"] = rel_name
    checksum = hashlib.sha256((name + "\n" + body + "\n" + repr(steps)).encode("utf-8")).hexdigest()
    meta["import_checksum"] = checksum

    payload = {
        "name": name,
        "description": description,
        "content": body,
        "version": version,
        "tags": [str(t).strip() for t in tags if str(t).strip()],
        "meta": meta,
        "kind": kind,
        "steps": steps,
        "required_tools": [str(t).strip() for t in tools if str(t).strip()],
        "valves": valves,
        "author": author,
        "is_active": False,
    }

    result.update(
        {
            "status": "valid",
            "errors": [],
            "name": name,
            "description": description,
            "version": version,
            "author": author,
            "tags": payload["tags"],
            "content": body,
            "kind": kind,
            "steps": steps,
            "required_tools": payload["required_tools"],
            "valves": valves,
            "meta": meta,
            "checksum": checksum,
            "payload": payload,
            "preview": body[:1000],
        }
    )
    return result


def _nearest_skill(path: str, skill_paths: set[str]) -> str | None:
    """Return the closest SKILL.md anchored above ``path`` (or None)."""
    parent = path.rsplit("/", 1)[0] if "/" in path else ""
    current = parent
    # Guard depth with visited set; path length is already bounded.
    while True:
        candidate = f"{current}/SKILL.md" if current else "SKILL.md"
        if candidate in skill_paths:
            return candidate
        if not current:
            break
        current = current.rsplit("/", 1)[0] if "/" in current else ""
    return None


class SkillImportManager:
    """Owns Skill bundle detection, preview and installation."""

    def __init__(self, store: Any = None) -> None:
        self._store = store

    # ── Detection helpers ───────────────────────────────────────────────

    def _detect(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        """Classify uploaded files without writing to the store."""
        expanded, errors = expand_uploads(files)

        # Group companion files (resources) by parent directory.  A skill is
        # anchored on one SKILL.md; everything else in its directory is a
        # resource sibling.
        result_items: list[dict[str, Any]] = []
        candidate_skills: list[dict[str, Any]] = []
        all_paths = {path for path, _ in expanded}
        skill_paths = {
            path for path, _ in expanded
            if path == "SKILL.md" or path.endswith("/SKILL.md")
        }

        # Assign every non-skill file to its NEAREST enclosing SKILL.md so
        # a nested or sibling skill never steals another skill's companion
        # resources.
        resources_by_skill: dict[str, list[str]] = {path: [] for path in skill_paths}
        for companion in all_paths:
            if companion in skill_paths:
                continue
            anchor = _nearest_skill(companion, skill_paths)
            if anchor is not None:
                resources_by_skill[anchor].append(companion)

        # Parse anchors.
        parsed_by_path: dict[str, dict[str, Any]] = {}
        for path, raw in expanded:
            if path == "SKILL.md" or path.endswith("/SKILL.md"):
                parsed = _parse_skill(path, raw)
                parsed_by_path[path] = parsed
                parsed["resources"] = sorted(resources_by_skill.get(path, []))
                candidate_skills.append(parsed)

        # Detect folders that contain no SKILL.md but look like a single skill
        # by having a README.md — leave them as suggested Knowledge, no
        # promotion to Skill without user confirmation.
        unknown_files: list[str] = []
        skill_paths = {p for p in all_paths if p == "SKILL.md" or p.endswith("/SKILL.md")}
        for path, _ in expanded:
            if path in skill_paths:
                continue
            if path.rsplit("/", 1)[-1].lower().endswith(".md"):
                unknown_files.append(path)

        # Compute duplicates against the store.
        # Store listing is async — manager returns a sync preview of names only,
        # filled by async methods later. Keep empty here; async augment in scan().
        for parsed in candidate_skills:
            item = {
                "source_path": parsed["source_path"],
                "name": parsed["name"],
                "status": parsed["status"],
                "errors": list(parsed["errors"]),
                "description": parsed["description"],
                "version": parsed["version"],
                "author": parsed["author"],
                "tags": parsed["tags"],
                "kind": parsed["kind"],
                "content_preview": parsed["preview"],
                "resources": parsed["resources"],
                "checksum": parsed.get("checksum"),
                "requires_classification": False,
            }
            if parsed["status"] == "invalid":
                item["suggested_target"] = "none"
            else:
                item["suggested_target"] = "skill"
            result_items.append(item)

        # Propose classification for stray markdown documents.
        for path in unknown_files:
            result_items.append(
                {
                    "source_path": path,
                    "name": path.rsplit("/", 1)[-1],
                    "status": "ambiguous",
                    "errors": [],
                    "description": "Markdown document without SKILL.md",
                    "version": None,
                    "author": None,
                    "tags": [],
                    "kind": None,
                    "content_preview": "",
                    "resources": [],
                    "checksum": None,
                    "requires_classification": True,
                    "suggested_target": "knowledge",
                }
            )

        proposed_skill_files = len(candidate_skills)
        return {
            "expanded_files": len(expanded),
            "detected_skills": len(candidate_skills),
            "invalid": sum(
                1 for item in result_items
                if item["status"] != "valid" and item.get("suggested_target") == "skill"
            ),
            "ambiguous": [item for item in result_items if item["status"] == "ambiguous"],
            "errors": errors,
            "items": result_items,
            "proposed_skill_files": proposed_skill_files,
        }

    async def scan(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        """Preview a bundle without installing anything."""
        detection = self._detect(files)
        # Augment with store-side duplicate info.
        await self._annotate_duplicates(detection)
        return detection

    async def import_files(
        self, files: list[tuple[str, bytes]], selected: list[str] | None = None
    ) -> dict[str, Any]:
        """Import all valid (or selected) skills from a bundle."""
        detection = self._detect(files)
        await self._annotate_duplicates(detection)
        selected_set = set(selected or [])
        imported = 0
        skipped = 0
        skipped_existing = 0
        skipped_conflict = 0
        invalid = 0
        errors = list(detection["errors"])
        conflicts: list[dict[str, Any]] = []
        imported_ids: list[str] = []

        # Map source_path -> parsed payload. Parse again for payload consistency.
        parsed_map = {}
        expanded, _ = expand_uploads(files)
        for path, raw in expanded:
            if path == "SKILL.md" or path.endswith("/SKILL.md"):
                parsed_map[path] = _parse_skill(path, raw)

        for item in detection["items"]:
            if item.get("status") == "ambiguous":
                continue
            if item.get("status") != "valid":
                invalid += 1
                errors.extend(item.get("errors", []))
                continue
            if selected_set and item["source_path"] not in selected_set:
                continue
            if item.get("duplicate_status") == "identical":
                skipped_existing += 1
                skipped += 1
                continue
            if item.get("duplicate_status") == "conflict":
                skipped_conflict += 1
                skipped += 1
                conflicts.append(
                    {
                        "name": item["name"],
                        "path": item["source_path"],
                        "reason": item.get("conflict_reason", "Existing skill conflicts."),
                    }
                )
                continue
            parsed = parsed_map.get(item["source_path"])
            if not parsed or not parsed.get("payload"):
                invalid += 1
                errors.append(f"Could not reconstruct skill from {item['source_path']}")
                continue
            payload = parsed["payload"]
            # Preserve provenance and any companion resource filenames.
            payload["meta"] = dict(payload.get("meta", {}))
            payload["meta"]["source"] = payload["meta"].get("source", "skill-import")
            payload["meta"]["source_path"] = item["source_path"]
            payload["meta"]["resource_files"] = item.get("resources", [])
            payload["is_active"] = False

            if self._store is None:
                errors.append("Skill store unavailable")
                skipped += 1
                continue
            try:
                created = await self._store.create_skill(payload)
                imported += 1
                imported_ids.append(str(created.get("id", "")))
            except ValueError as exc:
                skipped += 1
                errors.append(str(exc))
            except Exception as exc:  # noqa: BLE001 - isolate failures
                skipped += 1
                errors.append(str(exc)[:300])

        return {
            "discovered": len(parsed_map),
            "imported": imported,
            "skipped": skipped,
            "skipped_existing": skipped_existing,
            "skipped_conflict": skipped_conflict,
            "invalid": invalid,
            "errors": errors,
            "conflicts": conflicts,
            "imported_ids": imported_ids,
            "items": detection["items"],
        }

    async def _annotate_duplicates(self, detection: dict[str, Any]) -> None:
        existing = []
        if self._store is not None:
            try:
                existing = await self._store.list_skills()
            except Exception:  # noqa: BLE001
                existing = []
        existing_by_name = {
            str(s.get("name", "")).casefold(): s for s in existing
        }
        existing_by_checksum: dict[str, dict[str, Any]] = {}
        for skill in existing:
            checksum = str((skill.get("meta") or {}).get("import_checksum", ""))
            if checksum:
                existing_by_checksum[checksum] = skill
        for item in detection["items"]:
            if item.get("status") != "valid":
                item["duplicate_status"] = "none"
                continue
            name_key = str(item.get("name", "")).casefold()
            if name_key in existing_by_name:
                existing_skill = existing_by_name[name_key]
                checksum_match = None
                if item.get("checksum"):
                    checksum_match = existing_by_checksum.get(str(item["checksum"]))
                if item.get("checksum") and checksum_match is existing_skill:
                    item["duplicate_status"] = "identical"
                    item["duplicate_of"] = existing_skill.get("id")
                    item["conflict_reason"] = "An identical imported skill already exists."
                else:
                    item["duplicate_status"] = "conflict"
                    item["duplicate_of"] = existing_skill.get("id")
                    item["conflict_reason"] = "A skill with the same name exists."
                continue
            if item.get("checksum") and item["checksum"] in existing_by_checksum:
                item["duplicate_status"] = "identical"
                item["duplicate_of"] = existing_by_checksum[item["checksum"]].get("id")
                item["conflict_reason"] = "An identical imported skill already exists."
            else:
                item["duplicate_status"] = "none"


__all__ = ["SkillImportManager", "expand_uploads"]
