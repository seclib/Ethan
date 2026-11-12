"""Système d'extensions unifié — ETHAN Core.

Ce package est la COUCHE de gestion commune à Capabilities, Plugins et
Cookbook. Il ne remplace aucun des trois systèmes : il les **expose** à travers
une API unique, sans jamais réinterpréter leur sémantique.

    ExtensionManager
    ├── CapabilityHandler  -> core.capability_manager  (runtime réel)
    ├── PluginHandler      -> core.plugins              (déclaratif)
    └── CookbookHandler    -> core.cookbook             (records)

Invariants garantis ici :

* le Core est la source de vérité — l'interface n'invente aucun état ;
* le type reste explicite (`kind`), jamais déguisé ;
* aucune opération ne reste bloquée (bornes + réconciliation au démarrage) ;
* la persistance passe par `CoreRecordStore` (durable, pas de mémoire vive).

Première Loi (AGENTS.md) : une capacité d'ETHAN appartient au Core, pas à une
interface. Cette couche est donc dans `core/`, et les interfaces ne font que
l'afficher.
"""

from core.extensions.handlers import (
    CapabilityHandler,
    CookbookHandler,
    ExtensionHandler,
    PluginHandler,
)
from core.extensions.manager import ExtensionManager
from core.extensions.types import (
    ExtensionKind,
    ExtensionOperation,
    ExtensionRuntimeState,
    ExtensionSpec,
    ExtensionState,
    ExtensionStatus,
    OperationStatus,
    TransitionError,
)

__all__ = [
    "CapabilityHandler",
    "CookbookHandler",
    "ExtensionHandler",
    "ExtensionKind",
    "ExtensionManager",
    "ExtensionOperation",
    "ExtensionRuntimeState",
    "ExtensionSpec",
    "ExtensionState",
    "ExtensionStatus",
    "OperationStatus",
    "PluginHandler",
    "TransitionError",
]
