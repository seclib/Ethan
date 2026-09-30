"""ETHAN Core — Event Bus Module"""

from core.ethan_types.event import Event

from .nats_bus import EventBus

__version__ = "1.0.0"
__all__ = ["EventBus", "Event"]
