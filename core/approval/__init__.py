"""ETHAN Core — Approval Module

Système de validation humaine asynchrone pour les actions sensibles.
Les modules peuvent demander une approbation et attendre la réponse de manière asynchrone.
"""

from .engine import ApprovalEngine
from .types import ApprovalRequest, ApprovalResponse, ApprovalStatus, ApprovalCategory

__version__ = "1.0.0"
__all__ = ["ApprovalEngine", "ApprovalRequest", "ApprovalResponse", "ApprovalStatus", "ApprovalCategory"]