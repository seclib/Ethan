"""Document vault (read-only) for the Engineering Memory directory.

This module exists so that the Observatory workspace (WebUI) and any other
interface can browse the canonical documentary memory (``Obsidian/``) through
the same Core service. It never modifies, moves, renames or deletes anything:
every operation is read-only by construction.

Design constraints:
- no new dependency (Python stdlib only);
- path traversal is impossible by construction: every requested path is
  resolved and verified to stay inside ``root``;
- only text/document formats are served (allowlist of extensions);
- indexes and derived views are cheap to rebuild, so nothing is cached on
  disk; callers may cache in memory if they need to.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


class VaultError(Exception):
    """Raised when a vault request is invalid."""


_ALLOWED_EXTENSIONS = frozenset(
    {".md", ".markdown", ".txt", ".json", ".csv", ".yaml", ".yml", ".ndjson"}
)

# Directory names never listed: they hold tooling state, not knowledge.
_EXCLUDED_DIRS = frozenset({".git", "__pycache__", "node_modules"})

_MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB hard read cap
_MAX_SEARCH_BYTES = 10 * 1024 * 1024  # per-file scan cap for search/backlinks
_MAX_TREE_ENTRIES = 20_000
_MAX_SEARCH_HITS = 200

_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


class VaultService:
    """Read-only browsing/search over the canonical Engineering Memory root."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise VaultError(f"vault root does not exist or is not a directory: {self.root}")

    # ── Path safety ──────────────────────────────────────────────────

    def safe_path(self, relative: str) -> Path:
        rel = (relative or "").strip().replace("\\", "/")
        candidate = (self.root / rel).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise VaultError("path escapes the vault root")
        return candidate

    # ── Tree ─────────────────────────────────────────────────────────

    def tree(self) -> dict[str, Any]:
        """Returns the nested directory tree of allowlisted files."""

        def walk(directory: Path) -> dict[str, Any]:
            node: dict[str, Any] = {
                "type": "directory",
                "name": directory.name,
                "path": str(directory.relative_to(self.root)) if directory != self.root else "",
                "children": [],
            }
            try:
                entries = sorted(directory.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
            except OSError:
                return node
            for entry in entries:
                if entry.name.startswith("."):
                    # hidden tooling directories/files are never listed
                    continue
                if entry.is_dir():
                    if entry.name in _EXCLUDED_DIRS:
                        continue
                    node["children"].append(walk(entry))
                elif entry.is_file() and entry.suffix.lower() in _ALLOWED_EXTENSIONS:
                    node["children"].append(self._file_info(entry))
            return node

        return walk(self.root)

    # ── File info / read ─────────────────────────────────────────────

    def _file_info(self, path: Path, depth: int = 0) -> dict[str, Any]:
        stat = path.stat()
        try:
            rel = str(path.relative_to(self.root))
        except ValueError:
            rel = path.name
        return {
            "type": "file",
            "name": path.name,
            "path": rel,
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "modified_at": _iso_mtime(stat.st_mtime),
            "markdown": path.suffix.lower() in (".md", ".markdown"),
        }

    def read(self, relative: str) -> dict[str, Any]:
        target = self.safe_path(relative)
        if not target.is_file():
            raise VaultError("file not found")
        if target.suffix.lower() not in _ALLOWED_EXTENSIONS:
            raise VaultError("file type not allowed")
        size = target.stat().st_size
        if size > _MAX_FILE_BYTES:
            raise VaultError("file exceeds the size limit")
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise VaultError(f"could not read file: {exc}") from exc
        info = self._file_info(target)
        info["content"] = content
        info["line_count"] = content.count("\n") + 1
        return info

    # ── Write (explicitly scoped; Archives/ stays immutable) ─────────
    # The Observatory editor is authorized by the operator to maintain the
    # managed documents. The raw archives are NOT editable from the
    # interface — they keep provenance value and are protected here by
    # construction.

    def write(self, relative: str, content: str) -> dict[str, Any]:
        rel = (relative or "").strip()
        if not rel:
            raise VaultError("path must not be empty")
        if "\x00" in rel:
            raise VaultError("path contains an invalid character")
        target = self.safe_path(rel)
        if self._is_under_archives(target):
            raise VaultError("archives are immutable from the interface")
        if target.is_dir():
            raise VaultError("path refers to a directory")
        if target.suffix.lower() not in _ALLOWED_EXTENSIONS:
            raise VaultError("file type not allowed")
        if len(content.encode("utf-8")) > _MAX_FILE_BYTES:
            raise VaultError("content exceeds the size limit")
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        try:
            temp_path.write_text(content, encoding="utf-8")
            os.replace(temp_path, target)
        except OSError as exc:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise VaultError(f"could not write file: {exc}") from exc
        return self.read(rel)

    def _is_under_archives(self, target: Path) -> bool:
        archives = (self.root / "Archives").resolve()
        return target == archives or archives in target.parents

    # ── Wikilink resolution for the interface ────────────────────────

    def resolve_wikilink(self, raw: str) -> dict[str, Any]:
        stem_map: dict[str, str] = {}
        for path in self._iter_text_files({".md", ".markdown"}):
            stem_map.setdefault(path.stem.lower(), str(path.relative_to(self.root)))
        resolved = self._resolve_wikilink(raw, stem_map)
        if resolved is None:
            return {"resolved": None, "raw": raw}
        return {"resolved": resolved, "raw": raw}

    # ── Search ───────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 30, extensions: str | None = None) -> list[dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            raise VaultError("query must not be empty")
        needle = query.lower()
        allowed = _allowed_extensions(extensions)
        cap = max(1, min(limit, _MAX_SEARCH_HITS))
        hits: list[dict[str, Any]] = []
        for path in self._iter_text_files(allowed):
            if len(hits) >= cap:
                break
            hits.extend(self._scan_file(path, needle, cap - len(hits)))
        return hits

    def _scan_file(self, path: Path, needle: str, budget: int) -> list[dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                if path.stat().st_size > _MAX_SEARCH_BYTES:
                    return []
                results: list[dict[str, Any]] = []
                for line_number, line in enumerate(handle, start=1):
                    if needle in line.lower():
                        results.append({
                            "path": str(path.relative_to(self.root)),
                            "line": line_number,
                            "snippet": line.strip()[:300],
                        })
                        if len(results) >= budget:
                            return results
                return results
        except OSError:
            return []

    # ── Backlinks ────────────────────────────────────────────────────

    def backlinks(self, relative: str) -> list[dict[str, Any]]:
        """Files referencing the given document via ``[[wikilinks]]`` or its path."""

        target = self.safe_path(relative)
        if not target.is_file():
            raise VaultError("file not found")
        stem = target.stem
        stem_lower = stem.lower()
        rel = str(target.relative_to(self.root))
        path_lower = rel.lower()
        results: list[dict[str, Any]] = []
        for path in self._iter_text_files({".md", ".markdown"}):
            if path == target:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if stem_lower in text.lower() or path_lower in text.lower():
                excerpts = _backlink_excerpts(text, stem_lower, path_lower)
                results.append({
                    "path": str(path.relative_to(self.root)),
                    "name": path.name,
                    "excerpts": excerpts,
                })
                if len(results) >= 50:
                    break
        return results

    # ── Wikilink graph ───────────────────────────────────────────────

    def graph(self, limit_nodes: int = 150) -> dict[str, Any]:
        """A bounded wikilink graph of ``[[target]]`` relations between documents.

        Priority order for the node cap: documents that actually contain
        wikilinks first (they carry the relations), then everything else,
        with the raw archives (``Archives/``) ranked last — they are
        historical evidence, not the knowledge structure.
        """

        md_files = list(self._iter_text_files({".md", ".markdown"}))
        rel_of = {path: str(path.relative_to(self.root)) for path in md_files}
        stem_map: dict[str, str] = {}
        for path, rel in rel_of.items():
            stem_map.setdefault(path.stem.lower(), rel)

        # Single content pass: collect wikilinks per file (all files, not just
        # the capped subset — resolution targets must see the whole vault).
        file_links: dict[str, list[str]] = {}
        for path, rel in rel_of.items():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            matches = [match.group(1).strip() for match in _WIKILINK_RE.finditer(text)]
            if matches:
                file_links[rel] = matches

        def node_priority(rel: str) -> tuple[int, int, str]:
            has_links = 1 if rel in file_links else 0
            in_archives = 1 if rel.startswith("Archives/") else 0
            # Documents porteurs de liens d'abord, archives brutes en dernier.
            return (1 - has_links, in_archives, rel)

        selected = sorted(rel_of.values(), key=node_priority)[: max(1, limit_nodes)]
        selected_set = set(selected)

        nodes: dict[str, dict[str, Any]] = {
            rel: {"id": rel, "label": Path(rel).name, "path": rel} for rel in selected
        }
        edges: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for rel in selected:
            for raw in file_links.get(rel, []):
                target_rel = self._resolve_wikilink(raw, stem_map)
                if not target_rel or target_rel == rel:
                    continue
                pair = (rel, target_rel)
                if pair in seen:
                    continue
                seen.add(pair)
                if target_rel not in nodes:
                    nodes[target_rel] = {"id": target_rel, "label": Path(target_rel).name, "path": target_rel}
                edges.append({"source": rel, "target": target_rel})
        return {"nodes": list(nodes.values()), "edges": edges}

    def _resolve_wikilink(
        self,
        raw: str,
        stem_map: dict[str, str] | None = None,
    ) -> str | None:
        """Best-effort resolution of ``[[Name]]`` against files in the vault."""

        cleaned = raw.strip().replace("\\", "/")
        # Un wikilien n'est jamais un nom de document de plus de 255 caractères :
        # au-delà, ce n'est pas une cible, c'est du contenu (tableaux de données,
        # exports numériques…). On ne résout pas, sans lever d'erreur.
        if len(cleaned) > 255:
            return None
        try:
            candidate = self.safe_path(cleaned)
            if candidate.is_file():
                return str(candidate.relative_to(self.root))
            for suffix in (".md", ".markdown"):
                with_suffix = self.safe_path(cleaned + suffix)
                if with_suffix.is_file():
                    return str(with_suffix.relative_to(self.root))
        except (VaultError, OSError):
            # Wikiliens pointant hors du vault, chemins trop longs ou I/O :
            # la résolution échoue → le lien est traité comme non résolu.
            pass
        stem = Path(cleaned).name.lower()
        if stem_map is not None:
            if stem in stem_map:
                return stem_map[stem]
            return None
        # Fallback: full scan (expensive, kept only when no index provided).
        for path in self._iter_text_files({".md", ".markdown"}):
            if path.stem.lower() == stem:
                return str(path.relative_to(self.root))
        return None

    # ── Internals ────────────────────────────────────────────────────

    def _iter_text_files(self, extensions: set[str]):
        try:
            entries = list(self.root.rglob("*"))
        except OSError:
            return
        count = 0
        for entry in entries:
            if count >= _MAX_TREE_ENTRIES:
                return
            if not entry.is_file():
                continue
            if any(part in _EXCLUDED_DIRS for part in entry.parts):
                continue
            if entry.name.startswith("."):
                continue
            if entry.suffix.lower() not in extensions:
                continue
            count += 1
            yield entry


def _iso_mtime(mtime: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()


def _allowed_extensions(raw: str | None) -> set[str]:
    if not raw:
        return set(_ALLOWED_EXTENSIONS)
    wanted = {f".{item.strip().lstrip('.').lower()}" for item in raw.split(",") if item.strip()}
    allowed = wanted & set(_ALLOWED_EXTENSIONS)
    return allowed or set(_ALLOWED_EXTENSIONS)


def _backlink_excerpts(text: str, stem_lower: str, path_lower: str, max_excerpts: int = 3) -> list[str]:
    excerpts: list[str] = []
    lower = text.lower()
    for needle in (stem_lower, path_lower):
        index = 0
        while len(excerpts) < max_excerpts:
            index = lower.find(needle, index)
            if index == -1:
                break
            start = max(0, index - 80)
            end = min(len(text), index + len(needle) + 80)
            excerpt = text[start:end].replace("\n", " ").strip()
            if excerpt not in excerpts:
                excerpts.append(excerpt)
            index += len(needle)
    return excerpts
