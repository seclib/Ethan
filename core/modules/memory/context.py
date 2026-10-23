"""ETHAN Memory Module — context assembly for modules."""
from .store import query_events, query_history
from .semantic import recent_by_source


def assemble_context(session_id, module_name, limit=20):
    """Assemble context window for a module from short-term + long-term memory."""
    context = {
        "session_id": session_id,
        "recent_events": query_events(source=module_name, limit=limit),
        "recent_commands": query_history(interface="cli", limit=limit // 2),
        "recent_semantic": recent_by_source("event", limit=limit // 2),
    }
    return context


def recent_context(module_name, limit=10):
    return {
        "events": query_events(source=module_name, limit=limit),
        "history": query_history(limit=limit),
    }