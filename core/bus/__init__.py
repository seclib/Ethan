"""ETHAN Core — Event Bus Module"""

from .nats_bus import NATSBus, Event

__version__ = "1.0.0"
__all__ = ["NATSBus", "Event"]