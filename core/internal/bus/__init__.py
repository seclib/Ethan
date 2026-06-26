"""ETHAN Core — Event Bus Layer.

Bus d'événements abstrait pour la communication inter-modules.
Support NATS en production, InMemory en développement/tests.
"""

from .interface import EventBus, Subscription
from .memory import InMemoryBus
from .nats import NATSBus

__all__ = ["EventBus", "Subscription", "InMemoryBus", "NATSBus"]