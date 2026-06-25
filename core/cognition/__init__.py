"""ETHAN Core — Cognition Module.

Le cerveau d'ETHAN. Système cognitif autonome qui reçoit des requêtes abstraites
et produit des réponses intelligentes.

Architecture :
    CognitionModule
    ├── IntentionAnalyzer   — Comprendre les requêtes
    ├── ContextManager      — Assembler le contexte
    ├── MemoryManager       — Gérer les mémoires multiples
    ├── Reasoner            — Raisonner (LLM)
    ├── Planner             — Planifier (DAG)
    ├── Executor            — Exécuter les actions
    └── Reflector           — Réfléchir et évaluer

Communication :
    - Reçoit : ethan.cognition.request
    - Publie : ethan.cognition.* (tous les événements cognitifs)
"""

from .module import CognitionModule

__all__ = ["CognitionModule"]