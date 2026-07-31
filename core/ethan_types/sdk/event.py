"""Event schema — Re-exports canonical Event for backward compatibility.

MIGRATION NOTE: This module previously defined its own Event and EventType classes.
All code should use `core.ethan_types.event.Event` and `core.ethan_types.event.EventType`
as the single source of truth. This module now re-exports them for import compatibility.

Old usage:   from core.ethan_types.sdk.event import Event, EventType
New usage:   from core.ethan_types.event import Event, EventType
Both work identically — this is a shim.
"""

from core.ethan_types.event import Event, EventType  # noqa: F401

__all__ = ["Event", "EventType"]
