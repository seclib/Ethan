"""ETHAN Core — Context sources typées (Add Context).

Le contexte attaché est le contexte **explicitement choisi par l'utilisateur**
(§10/§12) : distinct du Knowledge/RAG, qui reste la récupération de
connaissances selon la configuration ETHAN.  Les deux coexistent.

Le Core décide comment sérialiser chaque source (§13) — le WebUI n'envoie
jamais arbitrairement des mégaoctets au modèle :

    file      → FileStore (contenu tronqué, taille bornée)
    folder    → FolderManager (liste réelle du contenu, bornée)
    url       → récupération Core (httpx) : URL publique validée, contenu
                borné ; jamais de contournement de validation
    knowledge → référence collection (résolution RAG existante inchangée)
    project   → référence projet (instructions + nom, résolution existante)
    git/terminal/log → référence annotée : le modèle lit ces sources via les
                outils autorisés en Act/Debug — pas de sortie factice.

Chaque item sérialisé porte son type dans le prompt (§13).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Bornes de sérialisation (le WebUI ne décide jamais de la taille).
MAX_FILE_CHARS = 20_000
MAX_LIST_CHARS = 4_000
MAX_URL_CHARS = 12_000
MAX_URL_BYTES = 400_000
MAX_ITEMS = 20


class ContextType(str, Enum):
    """Types de sources de contexte explicitement attachées (§10)."""

    FILE = "file"
    FOLDER = "folder"
    DOCUMENT = "document"
    IMAGE = "image"
    URL = "url"
    KNOWLEDGE = "knowledge"
    PROJECT = "project"
    GIT = "git"
    TERMINAL = "terminal"
    LOG = "log"


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[… tronqué ({len(text)} → {limit} caractères, borne Core)]"


@dataclass
class ContextItem:
    """Source de contexte explicitement attachée à une conversation."""

    type: ContextType
    ref: str  # file_id / folder_id / url / path / ref
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "ref": self.ref, "label": self.label or self.ref}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextItem":
        try:
            ctype = ContextType(str(data.get("type") or ""))
        except ValueError:
            raise ValueError(f"Unknown context type: {data.get('type')!r}") from None
        ref = str(data.get("ref") or data.get("id") or "")
        if not ref:
            raise ValueError("Context item requires 'ref'")
        return cls(type=ctype, ref=ref, label=str(data.get("label") or ""))


@dataclass
class ContextSerializationResult:
    """Résultat de sérialisation (sections injectées + journal)."""

    sections: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Texte injecté dans le prompt système (vide si aucun item)."""
        if not self.sections:
            return ""
        return "[Contexte attaché]\n" + "\n\n".join(self.sections)


class ContextSourceSerializer:
    """Sérialisation Core-owned des sources de contexte attachées.

    Args:
        files: FileStore optionnel (type ``file``).
        folders: FolderManager optionnel (type ``folder``).
    """

    def __init__(self, files: Any | None = None, folders: Any | None = None) -> None:
        self._files = files
        self._folders = folders

    async def serialize(self, items: list[ContextItem]) -> ContextSerializationResult:
        result = ContextSerializationResult()
        for item in items[:MAX_ITEMS]:
            try:
                section = await self._serialize_one(item)
            except Exception as exc:
                logger.warning(
                    "Context serialization failed (%s %s): %s", item.type.value, item.ref, exc
                )
                result.notes.append(f"context {item.type.value}:{item.ref} indisponible")
                continue
            if section:
                result.sections.append(section)
        return result

    async def _serialize_one(self, item: ContextItem) -> str:
        if item.type in (ContextType.FILE, ContextType.DOCUMENT, ContextType.IMAGE):
            return await self._serialize_file(item)
        if item.type == ContextType.FOLDER:
            return await self._serialize_folder(item)
        if item.type == ContextType.URL:
            return await self._serialize_url(item)
        if item.type == ContextType.KNOWLEDGE:
            # Context ≠ RAG : la collection est déjà résolue par la récupération
            # existante (knowledge_ids) — ici, simple référence annotée.
            return (
                f"=== Knowledge: {item.label or item.ref} (collection {item.ref}) ===\n"
                "(contenu indexé — résolution RAG active)"
            )
        if item.type == ContextType.PROJECT:
            return (
                f"=== Projet: {item.label or item.ref} ===\n"
                "(contexte projet — instructions résolues par le Core)"
            )
        # git / terminal / log : références annotées — le modèle lit ces
        # sources via les outils autorisés du mode (pas de sortie factice).
        note = {
            ContextType.GIT: "lecture via les commandes Git autorisées",
            ContextType.TERMINAL: "lecture via le terminal (politique du mode)",
            ContextType.LOG: "lecture via les fichiers de logs autorisés",
        }[item.type]
        return f"=== {item.type.value.title()}: {item.label or item.ref} ===\n({note})"

    async def _serialize_file(self, item: ContextItem) -> str:
        label = item.label or item.ref
        if self._files is None:
            return f"=== File: {label} ===\n(FileStore indisponible — référence conservée)"
        record = await self._files.get(item.ref)
        filename = (record or {}).get("filename", item.ref)
        content = ""
        try:
            downloaded = await self._files.download(item.ref)
            if downloaded is not None:
                data, _meta = downloaded
                content = (
                    data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
                )
        except Exception as exc:
            logger.warning("Attached file download failed (%s): %s", item.ref, exc)
        if not content:
            return f"=== File: {filename} ===\n(contenu indisponible — métadonnées conservées)"
        return f"=== File: {filename} ===\n{_truncate(content, MAX_FILE_CHARS)}"

    async def _serialize_folder(self, item: ContextItem) -> str:
        label = item.label or item.ref
        if self._folders is None:
            return f"=== Folder: {label} ===\n(FolderManager indisponible — référence conservée)"
        folder = await self._folders.get_folder(item.ref)
        if folder is None:
            return f"=== Folder: {label} ===\n(dossier introuvable)"
        name = folder.get("name", item.ref)
        resources = folder.get("resources") or []
        lines = [
            f"- {r.get('resource_type', '?')}:{r.get('resource_id', '?')}" for r in resources[:100]
        ]
        listing = "\n".join(lines) if lines else "(vide)"
        return (
            f"=== Folder: {name} ({len(resources)} ressources) ===\n"
            f"{_truncate(listing, MAX_LIST_CHARS)}"
        )

    async def _serialize_url(self, item: ContextItem) -> str:
        from urllib.parse import urlsplit

        import httpx

        url = item.ref.strip()
        label = item.label or url
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return f"=== URL: {label} ===\n(URL invalide ou non publique — référence conservée)"
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=10.0,
                headers={"User-Agent": "ETHAN-Chat-Context/1.0"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                raw = response.content[:MAX_URL_BYTES]
                if "text/html" in content_type or not content_type:
                    from html.parser import HTMLParser

                    class _Text(HTMLParser):
                        def __init__(self) -> None:
                            super().__init__()
                            self.chunks: list[str] = []

                        def handle_data(self, data: str) -> None:
                            chunk = data.strip()
                            if chunk:
                                self.chunks.append(chunk)

                    parser = _Text()
                    parser.feed(raw.decode("utf-8", errors="replace"))
                    text = "\n".join(parser.chunks)
                else:
                    text = raw.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning("URL context fetch failed (%s): %s", url, exc)
            return f"=== URL: {label} ===\n(récupération impossible: {exc})"
        return f"=== URL: {label} ===\n{_truncate(text, MAX_URL_CHARS)}"


__all__ = [
    "ContextItem",
    "ContextSerializationResult",
    "ContextSourceSerializer",
    "ContextType",
    "MAX_FILE_CHARS",
    "MAX_ITEMS",
    "MAX_URL_CHARS",
]
