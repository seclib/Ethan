"""Persistance atomique des archives Engineering Memory."""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
from typing import Iterable

import yaml

from core.engineering_memory.models import MemoryRecord, RecordType
from core.engineering_memory.registry import EngineeringMemoryRegistry
from core.engineering_memory.validators import ValidationError


class DuplicateRecordError(ValidationError):
    """Un enregistrement avec le même identifiant mais un contenu différent existe."""


def _canonical(record: MemoryRecord) -> dict[str, object]:
    return record.to_dict()


def _canonical_json(record: MemoryRecord) -> str:
    """Forme canonique **stable** d'un enregistrement, comparable après aller-retour YAML.

    La comparaison directe des dictionnaires est instable : PyYAML convertit
    une chaîne ressemblant à une date (« 2026-11-12 ») en objet `date` au
    moment de la relecture, ce qui rend un enregistrement identique à lui-même
    différent de sa version relue. La forme canonique sérialise en JSON avec
    `default=str` : la relecture d'une date produit à nouveau la même chaîne,
    et la comparaison reflète l'égalité *logique* du contenu.

    Conséquence directe : la détection de doublon ne peut pas produire de
    faux positif sur une charge utile structurée (P2.8.3).

    Args:
        record: Enregistrement à canoniser.

    Returns:
        Chaîne JSON triée, déterministe.
    """
    return json.dumps(record.to_dict(), sort_keys=True, default=str, ensure_ascii=False)


class ObsidianPersistence:
    """Persistance fichier pour la mémoire Engineering Memory.

    Le dossier racine est la source locale de la mémoire. L'écriture est
    atomique et l'idempotence est garantie par le contenu canonical.
    """

    def __init__(
        self,
        root: Path,
        registry: EngineeringMemoryRegistry | None = None,
        *,
        require_existing_destination: bool = False,
    ):
        self.root = root
        self.registry = registry or EngineeringMemoryRegistry()
        # P2.8.0 — protection anti-duplication du corpus. Activé, l'écriture
        # refuse de créer un répertoire de destination absent : la correction
        # d'une destination logique ne peut plus se traduire par une création
        # physique. Désactivé par défaut, le comportement historique est
        # conservé (racine vide + destination créée à la première écriture).
        self._require_existing_destination = require_existing_destination

    def destination_exists(self, record_type: RecordType | str) -> bool:
        """Indique si la destination d'un type existe déjà sous la racine.

        Méthode **strictement en lecture seule** : elle ne crée, ne déplace et
        ne modifie rien.

        Args:
            record_type: Type d'enregistrement.

        Returns:
            True si le répertoire de destination existe déjà.
        """
        return self.registry.destination_exists(self.root, record_type)

    def relative_path(self, record: MemoryRecord) -> Path:
        return self.registry.relative_path_for(record.record_type, record.id, record.title)

    def full_path(self, record: MemoryRecord) -> Path:
        relative = self.relative_path(record)
        if any(part in ("", ".", "..") for part in relative.parts):
            raise ValidationError("repository path is not safe")
        return self.root.joinpath(relative)

    def write(self, record: MemoryRecord) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.full_path(record)
        if self._require_existing_destination and not path.parent.is_dir():
            raise ValidationError(
                f"destination directory does not exist in the corpus: {path.parent}"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            previous = self._read(record.id, path)
            if _canonical_json(previous) != _canonical_json(record):
                raise DuplicateRecordError(
                    f"a different record with id {record.id} already exists"
                )
            return path

        temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        content = self._render(record)
        try:
            with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
        return path

    def read(self, record_id: str) -> MemoryRecord | None:
        for candidate in self._all_markdown_files():
            try:
                record = self._read(record_id, candidate)
                if record is not None and record.id == record_id:
                    return record
            except ValidationError:
                continue
        return None

    def list_records(self, record_type: str | None = None) -> list[MemoryRecord]:
        results: list[MemoryRecord] = []
        for path in self._all_markdown_files():
            try:
                record = self._read(None, path)
            except ValidationError:
                continue
            if record is None:
                continue
            if record_type is not None and record.record_type.value != record_type:
                continue
            results.append(record)
        return sorted(results, key=lambda item: (item.created_at, item.id))

    def integrity_report(self) -> dict[str, int | list[str]]:
        valid = 0
        invalid_paths: list[str] = []
        for path in self._all_markdown_files():
            try:
                self._read(None, path)
                valid += 1
            except ValidationError as error:
                invalid_paths.append(f"{path}: {error}")
        return {
            "root": str(self.root),
            "markdown_files": len(list(self._all_markdown_files())),
            "valid_records": valid,
            "invalid_records": invalid_paths,
        }

    def _all_markdown_files(self) -> Iterable[Path]:
        if not self.root.exists():
            return []
        return self.root.rglob("*.md")

    def _read(self, expected_id: str | None, path: Path) -> MemoryRecord | None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            # Un document illisible (permissions, encodage) ne doit pas
            # interrompre la lecture du corpus : il est signale comme
            # invalide, et les autres documents restent accessibles.
            raise ValidationError(f"{path}: unreadable ({error.strerror or error})") from error
        frontmatter = self._split_frontmatter(text, path)
        try:
            data = yaml.safe_load(frontmatter)
        except yaml.YAMLError as error:
            raise ValidationError(f"{path}: {error}") from error
        if not isinstance(data, dict):
            raise ValidationError(f"{path}: frontmatter must be an object")
        try:
            from core.engineering_memory.models import (
                ConfidenceLevel,
                MemoryRecord,
                RecordOrigin,
                RecordType,
                SourceOfFactLevel,
            )
            if "record_type" in data:
                data["record_type"] = RecordType(data["record_type"])
            if "provenance_level" in data:
                data["provenance_level"] = SourceOfFactLevel(data["provenance_level"])
            if "origin" in data:
                data["origin"] = RecordOrigin(data["origin"])
            if "confidence" in data:
                data["confidence"] = ConfidenceLevel(data["confidence"])
            record = MemoryRecord(**data)
        except (TypeError, ValueError) as error:
            raise ValidationError(f"{path}: {error}") from error
        if expected_id is not None and record.id != expected_id:
            return None
        record.repository_path = path
        return record

    @staticmethod
    def _split_frontmatter(text: str, path: Path) -> str:
        """Extrait le frontmatter YAML d'un document Markdown.

        Le frontmatter est delimite par deux lignes ``---`` situees en
        colonne 0. Un decoupage naïf sur la chaine ``"---"`` est invalide :
        toute valeur contenant ``---`` (un tableau Markdown ``|---|...|``, un
        separateur de section) tronquerait le frontmatter et rendrait le
        document **illisible** alors qu'il est parfaitement valide. Le
        delimiteur est donc recherche ligne par ligne, en colonne 0, ce qui
        reste fiable : un bloc YAML scalaire indente ne peut pas contenir une
        ligne ``---`` non indentee.

        Args:
            text: Contenu complet du document.
            path: Chemin du document (pour le message d'erreur).

        Returns:
            Le frontmatter YAML, sans ses delimiteurs.

        Raises:
            ValidationError: Si le frontmatter est absent ou incomplet.
        """
        lines = text.split("\n")
        if not lines or lines[0].strip() != "---":
            raise ValidationError(f"{path} has no YAML frontmatter")
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return "\n".join(lines[1:index])
        raise ValidationError(f"{path} has incomplete frontmatter")

    def _render(self, record: MemoryRecord) -> str:
        frontmatter = yaml.safe_dump(record.to_dict(), sort_keys=False, allow_unicode=True, default_flow_style=False)
        if not frontmatter.endswith("\n"):
            frontmatter += "\n"
        return f"---\n{frontmatter}---\n\n{record.text_body()}"
