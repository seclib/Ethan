"""Capability types — Contrat pour les capacités des modules."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Dependency:
    """Dépendance vers une autre capacité."""
    name: str
    version: str = "*"
    optional: bool = False


@dataclass
class Capability:
    """Capabilité déclarée par un module.

    Une capabilité est un contrat : le module promet de savoir
    traiter un certain type d'inputs et produire des outputs.
    """
    name: str
    version: str = "1.0.0"
    module: str = ""
    description: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    state_reads: list[str] = field(default_factory=list)
    state_writes: list[str] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    shared: bool = False