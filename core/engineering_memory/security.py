"""Sécurité applicative de l'Engineering Memory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class SecurityPolicyError(Exception):
    """Violation de politique de sécurité."""


class Permission(StrEnum):
    READ = "read"
    PROPOSE = "propose"
    RECORD = "record"
    MODIFY = "modify"
    ARCHIVE = "archive"
    VALIDATE = "validate"
    HUMAN_APPROVE = "human_approve"
    ADMINISTER = "administer"


class Role(StrEnum):
    READER = "reader"
    PROPOSER = "proposer"
    RECORDER = "recorder"
    VALIDATOR = "validator"
    HUMAN_AUTHORITY = "human_authority"
    ADMIN = "admin"


PERMISSION_MATRIX: dict[Role, frozenset[Permission]] = {
    Role.READER: frozenset({Permission.READ}),
    Role.PROPOSER: frozenset({Permission.READ, Permission.PROPOSE}),
    Role.RECORDER: frozenset({Permission.READ, Permission.PROPOSE, Permission.RECORD}),
    Role.VALIDATOR: frozenset({Permission.READ, Permission.PROPOSE, Permission.RECORD, Permission.VALIDATE}),
    Role.HUMAN_AUTHORITY: frozenset(
        {
            Permission.READ,
            Permission.PROPOSE,
            Permission.RECORD,
            Permission.VALIDATE,
            Permission.MODIFY,
            Permission.ARCHIVE,
            Permission.HUMAN_APPROVE,
        }
    ),
    Role.ADMIN: frozenset(Permission),
}

PRIVILEGED_OPERATIONS: frozenset[str] = frozenset(
    {"approve_decision", "archive_secret_record", "publish_memory", "purge_record"}
)


class SecurityPolicy:
    """Politique de données et de chemins pour la mémoire EM."""

    SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"(?i)(?:password|token|secret|api[_-]?key)\s*[=:]\s*(?!\[REDACTE)\S+"),
        re.compile(r"(?i)authorization:\s*bearer\s+(?!\[REDACTE)\S+"),
        re.compile(r"(?i)private[_-]?key\s*[:=]\s*(?!\[REDACTE)\S+"),
    )

    @classmethod
    def validate_record(cls, record: object) -> None:
        texts = [str(getattr(record, field, "")) for field in ("id", "title", "source_of_fact", "notes")]
        try:
            texts.extend(str(component) for component in getattr(record, "components", []))
        except Exception:  # never hide validation failure behind broad fallback
            raise
        for text in texts:
            if not isinstance(text, str):
                raise SecurityPolicyError("record fields must be text")
            for pattern in cls.SECRET_PATTERNS:
                if pattern.search(text):
                    raise SecurityPolicyError("secret-like value must not be persisted in Engineering Memory")
        # P2.8.3 — la charge utile structurée est une surface de persistance
        # supplémentaire : elle doit être contrôlée au même titre que `notes`,
        # sinon un secret glissé dans une section structurée contournerait la
        # politique de sécurité.
        for text in cls._iter_metadata_texts(getattr(record, "metadata", None)):
            for pattern in cls.SECRET_PATTERNS:
                if pattern.search(text):
                    raise SecurityPolicyError(
                        "secret-like value must not be persisted in Engineering Memory"
                    )

    @classmethod
    def _iter_metadata_texts(cls, metadata: object):
        """Parcourt récursivement les valeurs textuelles d'une charge utile.

        Args:
            metadata: Charge utile structurée (dict, listes, scalaires).

        Yields:
            Chaque valeur textuelle encountered.
        """
        if metadata is None:
            return
        if isinstance(metadata, str):
            yield metadata
            return
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                yield from cls._iter_metadata_texts(key)
                yield from cls._iter_metadata_texts(value)
            return
        if isinstance(metadata, (list, tuple, set)):
            for item in metadata:
                yield from cls._iter_metadata_texts(item)
            return
        if isinstance(metadata, (int, float, bool)):
            return
        yield str(metadata)

    @classmethod
    def ensure_path_in_root(cls, root: Path, candidate: Path) -> None:
        root_resolved = root.resolve()
        candidate_resolved = candidate.resolve()
        if candidate_resolved != root_resolved and root_resolved not in candidate_resolved.parents:
            raise SecurityPolicyError("path escapes the Engineering Memory root")

    @staticmethod
    def can(role: Role, permission: Permission) -> bool:
        return permission in PERMISSION_MATRIX.get(role, frozenset())

    @staticmethod
    def requires_human_approval(operation: str) -> bool:
        return operation in PRIVILEGED_OPERATIONS


@dataclass(frozen=True)
class PermissionMatrix:
    """Lecture structurée de la matrice pour l'audit."""

    matrix: dict[Role, frozenset[Permission]]
