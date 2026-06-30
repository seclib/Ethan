"""ETHAN Core — Cost & Budget Module

Contrôle budgétaire multi-scope (global/projet/run) avec alertes warn et hard-stop.
"""

from .budget import BudgetGuard
from .tracker import CostTracker
from .types import BudgetScope, BudgetStatus, BudgetAlert

__version__ = "1.0.0"
__all__ = ["BudgetGuard", "CostTracker", "BudgetScope", "BudgetStatus", "BudgetAlert"]