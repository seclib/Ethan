"""Core domains — spécialités fonctionnelles des ressources ETHAN.

Un Domain regroupe par **spécialité** (OSINT, Recon, Forensic, Code,
Security, Research, Personal, ...) des ressources Core : knowledge,
collections RAG, skills, sources.  Comme les dossiers (core/folders), un
domain est une **relation**, jamais une duplication : les ressources
restent possédées par leurs managers Core d'origine.

Différences avec les dossiers :
- un domain est **plat** (pas d'arborescence) ;
- le nom est **unique** (identité fonctionnelle, pas un simple label) ;
- une ressource peut appartenir à **plusieurs domains** ou à **aucun** ;
- aucun domain n'est seedé ni imposé par le système.

Persistance (CoreRecordStore partagé — PG durable + Redis + fallback
mémoire) :
- ``domains``            : records domain (id, name, description, icon…)
- ``domain-memberships`` : relations (domain_id, resource_type, resource_id)

Cette capacité est utilisable sans aucune interface (WebUI, CLI, Desktop)
et prépare la sélection explicite de domains par les agents (``domain_ids``
sur les définitions d'agents — résolu en ressources réelles à l'exécution).
"""

from core.domains.manager import (
    DEFAULT_RESOURCE_TYPES,
    DomainManager,
    DomainResourceProvider,
)

__all__ = [
    "DomainManager",
    "DomainResourceProvider",
    "DEFAULT_RESOURCE_TYPES",
]
