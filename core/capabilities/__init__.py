"""Capability Model — Ethan OS

Toute action est une Capability.
Le Core ne connaît que des capacités, jamais des outils ou des technologies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class CapabilityStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CapabilityContext:
    """Contexte d'exécution d'une Capability."""
    user_id: str
    session_id: str
    trace_id: str
    permissions: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: dict = field(default_factory=dict)


@dataclass
class CapabilityResult:
    """Résultat d'exécution d'une Capability."""
    status: CapabilityStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class Capability(ABC):
    """Interface abstraite pour toutes les Capabilities.
    
    Une Capability est :
    - autonome
    - interchangeable
    - isolée
    - testable
    
    Le Core ne connaît que cette interface.
    """

    name: str = "base"
    description: str = "Base capability"
    version: str = "1.0.0"
    risk_level: RiskLevel = RiskLevel.LOW

    @abstractmethod
    async def validate(self, context: CapabilityContext) -> bool:
        """Valide que la capability peut être exécutée dans ce contexte.
        
        Vérifie :
        - permissions de l'utilisateur
        - risque acceptable
        - prérequis remplis
        """
        pass

    @abstractmethod
    async def execute(self, context: CapabilityContext, **kwargs) -> CapabilityResult:
        """Exécute l'action. Retourne un résultat."""
        pass

    @abstractmethod
    async def observe(self, result: CapabilityResult) -> dict:
        """Analyse le résultat et produit une observation.
        
        Retourne un dict d'observations pour la mémoire.
        """
        pass

    async def pre_execute(self, context: CapabilityContext) -> None:
        """Hook appelé avant execute(). Override si nécessaire."""
        pass

    async def post_execute(self, context: CapabilityContext, result: CapabilityResult) -> None:
        """Hook appelé après execute(). Override si nécessaire."""
        pass