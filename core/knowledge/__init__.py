"""ETHAN Core — Knowledge Module.

Connaissance persistante, sources, relations et accès RAG.
"""

from core.knowledge.collections import KnowledgeCollectionManager
from core.knowledge.manager import KnowledgeManager
from core.knowledge.types import KnowledgeNode, KnowledgeConnection, KnowledgeType

__all__ = [
    "KnowledgeCollectionManager",
    "KnowledgeManager",
    "KnowledgeNode",
    "KnowledgeConnection",
    "KnowledgeType",
]
