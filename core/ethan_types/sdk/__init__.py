"""ETHAN SDK — Types partagés entre le Kernel, les modules et les interfaces.

Ce module fournit le contrat de données pour tous les événements NATS
utilisés par le système cognitif ETHAN.
"""

from .event import Event, EventType

__all__ = ["Event", "EventType"]
