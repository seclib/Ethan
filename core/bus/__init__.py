"""ETHAN Core — Event Bus Module"""

from .nats_bus import Event, EventBus

__version__ = "1.0.0"
__all__ = ["EventBus", "Event"]
