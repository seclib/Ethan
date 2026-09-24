"""Cognitive Kernel — Phase 0.2

Ethan Cognitive Operating System Kernel.
Orchestrates cognitive modules via NATS event bus.

Technology independence (ADR-1005) : toute technologie vit derrière une
abstraction (providers LLM, memory backends, state stores, transports) —
le raisonnement du Core reste interchangeable, l'infrastructure remplaçable.
"""

__version__ = "0.2.0"
