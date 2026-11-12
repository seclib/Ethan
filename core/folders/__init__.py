"""Core folders — organisation générique des ressources ETHAN.

Les dossiers sont une capacité du Core : ils organisent les ressources
(knowledge, collections RAG, skills, ...) par des **relations**, jamais par
duplication physique.  Aucun dossier n'est créé ni imposé par le système :
l'utilisateur crée librement son arborescence (nom libre, sous-dossiers,
icônes, ordre) et une ressource peut rester sans dossier.

Persistance (CoreRecordStore partagé) :
- ``folders``            : records dossiers (id, name, parent_id, icon, order…)
- ``folder-memberships`` : relations (folder_id, resource_type, resource_id)

Cette capacité est utilisable sans aucune interface (WebUI, CLI, Desktop).
"""

from core.folders.manager import (
    DEFAULT_RESOURCE_TYPES,
    FolderManager,
    FolderResourceProvider,
)

__all__ = [
    "FolderManager",
    "FolderResourceProvider",
    "DEFAULT_RESOURCE_TYPES",
]
