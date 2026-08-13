"""Agent Base — Façade de compatibilité.

Réexporte `Agent` depuis `core.modules.base` et `AgentConfig` depuis
`core.config.schema` pour maintenir la compatibilité avec les imports
existants (`from core.agents.base import Agent, AgentConfig`).
"""

from core.modules.base import Agent
from core.config.schema import AgentConfig

__all__ = ["Agent", "AgentConfig"]