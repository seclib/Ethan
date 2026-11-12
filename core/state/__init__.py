"""ETHAN Core — state contracts and persistence helpers.

Optional infrastructure clients are imported lazily so a standalone Core
domain can still run with the in-process record fallback when Redis or
PostgreSQL client packages are intentionally absent.
"""

from .interface import StateBackend
from .record_store import CoreRecordStore

__version__ = "1.0.0"
__all__ = [
    "StateBackend",
    "RedisLiveState",
    "PostgresPersistentState",
    "CompositeStateBackend",
    "CoreRecordStore",
    "CoreWebUIStore",
]


def __getattr__(name: str):
    """Lazily expose infrastructure-backed state implementations."""
    if name == "CoreWebUIStore":
        from .webui_store import CoreWebUIStore

        return CoreWebUIStore
    if name == "RedisLiveState":
        from .redis_state import RedisLiveState

        return RedisLiveState
    if name == "PostgresPersistentState":
        from .postgres_state import PostgresPersistentState

        return PostgresPersistentState
    if name == "CompositeStateBackend":
        from .composite_backend import CompositeStateBackend

        return CompositeStateBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
