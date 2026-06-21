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
from .planner import PlannerAgent
from .research import ResearchAgent
from .developer import DeveloperAgent
from .memory import MemoryAgent
from .vision import VisionAgent
from .voice import VoiceAgent
from .browser import BrowserAgent
from .automation import AutomationAgent
from .security import SecurityAgent

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
    "VoiceAgent",
    "BrowserAgent",
    "AutomationAgent",
    "SecurityAgent",
]