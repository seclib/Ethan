"""ETHAN Core — Types partagés entre tous les composants.

Ces dataclasses sont le contrat de données du système.
Ils sont utilisés par le Kernel Go, les modules Python, et les interfaces.
"""

from .event import Event, EventType

__all__ = [
    "Event", "EventType",
]