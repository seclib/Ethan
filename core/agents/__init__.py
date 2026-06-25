"""Jarvis OS — Agent System

Système d'agents spécialisés, indépendants, communiquant via Event Bus.

Architecture:
    Agent (ABC)
    ├── PlannerAgent      — Planification de tâches complexes
    ├── ResearchAgent     — Recherche et synthèse d'information
    ├── DeveloperAgent    — Génération et analyse de code
    ├── MemoryAgent       — Gestion de la mémoire persistante
    ├── VisionAgent       — Analyse d'images et vidéo
    ├── VoiceAgent        — Traitement vocal (STT/TTS)
    ├── BrowserAgent      — Navigation web automatisée
    ├── AutomationAgent   — Exécution de workflows
    └── SecurityAgent     — Analyse et validation de sécurité

Communication:
    - Tous les agents communiquent via core/events/ (Event Bus)
    - Chaque agent publie des événements sur son canal
    - Les autres agents peuvent y répondre
    - Monitoring via core/metrics/ (Prometheus)
"""

from .base import Agent, AgentConfig, AgentStatus, AgentRegistry

# Imports conditionnels pour la rétrocompatibilité
try:
    from .planner import PlannerAgent
except ImportError:
    PlannerAgent = None  # type: ignore

try:
    from .research import ResearchAgent
except ImportError:
    ResearchAgent = None  # type: ignore

try:
    from .developer import DeveloperAgent
except ImportError:
    DeveloperAgent = None  # type: ignore

try:
    from .memory import MemoryAgent
except ImportError:
    MemoryAgent = None  # type: ignore

try:
    from .vision import VisionAgent
except ImportError:
    VisionAgent = None  # type: ignore

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentStatus",
    "AgentRegistry",
    "PlannerAgent",
    "ResearchAgent",
    "DeveloperAgent",
    "MemoryAgent",
    "VisionAgent",
]
