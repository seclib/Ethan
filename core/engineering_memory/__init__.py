"""Engineering Memory for ETHAN.

This package is a curation and traceability layer. It does not replace core
business state. It records and indexes events using the repository's own models.
"""

from __future__ import annotations

from core.engineering_memory.models import (
    MemoryRecord,
    RecordType,
    RecordOrigin,
    SourceOfFactLevel,
    ConfidenceLevel,
)
from core.engineering_memory.service import EngineeringMemoryService

__all__ = [
    "EngineeringMemoryService",
    "MemoryRecord",
    "RecordType",
    "RecordOrigin",
    "RecordStatus",
    "SourceOfFactLevel",
    "ConfidenceLevel",
]
