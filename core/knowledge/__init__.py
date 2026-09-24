"""ETHAN Core — Knowledge Module.

Connaissance persistante, sources, relations et accès RAG.
"""

from core.knowledge.collections import KnowledgeCollectionManager
from core.knowledge.manager import KnowledgeManager
from core.knowledge.types import KnowledgeConnection, KnowledgeNode, KnowledgeType

__all__ = [
    "KnowledgeCollectionManager",
    "KnowledgeManager",
    "KnowledgeNode",
    "KnowledgeConnection",
    "KnowledgeType",
]
