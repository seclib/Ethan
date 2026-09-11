"""ETHAN Core — Duplicate Detection domain.

Read-only detection (:class:`DuplicateDetector`) plus a secure resolver
(:class:`DuplicateResolver`) that owns every mutation.  Interfaces (WebUI, CLI)
render reports and send resolution intents through the API — they never classify
or delete directly.
"""

from core.dedup.detector import DuplicateDetector
from core.dedup.resolver import DuplicateResolver, ResolutionResult
from core.dedup.types import (
    DuplicateAction,
    DuplicateCategory,
    DuplicateGroup,
    DuplicateReport,
    ItemDomain,
    ScannedItem,
)

__all__ = [
    "DuplicateDetector",
    "DuplicateResolver",
    "DuplicateReport",
    "DuplicateGroup",
    "DuplicateCategory",
    "DuplicateAction",
    "ScannedItem",
    "ItemDomain",
    "ResolutionResult",
]
