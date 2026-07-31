"""ETHAN Core — State Manager Module"""

from .interface import StateBackend
from .redis_state import RedisLiveState
from .postgres_state import PostgresPersistentState
from .composite_backend import CompositeStateBackend

__version__ = "1.0.0"
__all__ = ["StateBackend", "RedisLiveState", "PostgresPersistentState", "CompositeStateBackend"]
