"""Plugin Types — Manifest et états du système Plugins ETHAN.

Un plugin ETHAN est une unité de capacité déclarée par un manifest et
validée par le Core.  Il référence les systèmes existants (ToolRegistry,
Skills, MCP servers) au lieu de les dupliquer :

    Plugin
      ├── Apps / Integrations
      ├── Skills   (références → core.skills)
      ├── Tools    (références → core.tools.registry)
      └── MCP      (références → core.tools.servers)

Les permissions sont déclaratives : un plugin ne peut jamais obtenir plus
de permissions que celles déclarées dans son manifest et accordées.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Statuts Core-arbitrés (compatibles avec les enregistrements historiques
# du domaine `webui_plugins` : "active" | "inactive").
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_AVAILABLE = "available"  # présent au catalogue, non installé


@dataclass
class PluginConfigurationField:
    """Champ de configuration déclaratif (non-secret côté WebUI).

    `secret=True` signifie : la valeur vit dans la couche secret manager
    (env/Vault) — jamais dans les records, jamais dans le frontend.
    """

    key: str
    label: str
    type: str = "string"  # string | number | boolean | select
    required: bool = False
    secret: bool = False
    options: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class PluginAuthentication:
    """Exigences d'authentification d'un plugin.

    `env_vars` liste les variables d'environnement/secret manager que
    l'opérateur doit fournir ; le WebUI ne manipule jamais ces secrets.
    """

    type: str = "none"  # none | api_key | oauth2
    scopes: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    instructions: str = ""


@dataclass
class PluginManifest:
    """Manifest standard d'un plugin ETHAN."""

    id: str
    name: str
    version: str
    description: str
    author: str = "ETHAN"
    icon: str = "Puzzle"  # nom de composant lucide-react côté WebUI
    categories: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)  # ids ToolRegistry
    skills: list[str] = field(default_factory=list)  # ids/références Skills
    mcp: list[str] = field(default_factory=list)  # serveurs MCP attendus
    permissions: list[str] = field(default_factory=list)
    configuration: list[PluginConfigurationField] = field(default_factory=list)
    authentication: PluginAuthentication = field(default_factory=PluginAuthentication)
    featured: bool = False
    source: str = "builtin"  # builtin | custom

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "icon": self.icon,
            "categories": list(self.categories),
            "capabilities": list(self.capabilities),
            "tools": list(self.tools),
            "skills": list(self.skills),
            "mcp": list(self.mcp),
            "permissions": list(self.permissions),
            "configuration": [
                {
                    "key": f.key,
                    "label": f.label,
                    "type": f.type,
                    "required": f.required,
                    "secret": f.secret,
                    "options": list(f.options),
                    "description": f.description,
                }
                for f in self.configuration
            ],
            "authentication": {
                "type": self.authentication.type,
                "scopes": list(self.authentication.scopes),
                "env_vars": list(self.authentication.env_vars),
                "instructions": self.authentication.instructions,
            },
            "featured": self.featured,
            "source": self.source,
        }


__all__ = [
    "PluginManifest",
    "PluginConfigurationField",
    "PluginAuthentication",
    "STATUS_ACTIVE",
    "STATUS_INACTIVE",
    "STATUS_AVAILABLE",
]
