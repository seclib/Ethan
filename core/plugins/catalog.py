"""Plugin Catalogue — manifestes des plugins ETHAN.

Chaque plugin référence les capacités ETHAN existantes (ToolRegistry,
Skills builtin, serveurs MCP attendus) au lieu de recréer une logique
parallèle.  Le Core reste la source de vérité : ce catalogue décrit,
il n'exécute pas.
"""

from __future__ import annotations

from .types import PluginAuthentication, PluginConfigurationField, PluginManifest

BUILTIN_PLUGINS: list[PluginManifest] = [
    PluginManifest(
        id="github",
        name="GitHub",
        version="1.0.0",
        description=(
            "Work with repositories, issues and pull requests: search code, "
            "read files, create issues and track pull requests."
        ),
        author="ETHAN",
        icon="Github",
        categories=["development", "productivity"],
        capabilities=["search", "read", "create", "update", "execute"],
        mcp=["github-mcp"],
        permissions=["read_data", "search", "create", "modify", "external_network"],
        configuration=[
            PluginConfigurationField(
                key="default_repo",
                label="Dépôt par défaut",
                type="string",
                description="Propriétaire/nom du dépôt pré-sélectionné.",
            ),
        ],
        authentication=PluginAuthentication(
            type="api_key",
            scopes=["repo", "read:org"],
            env_vars=["GITHUB_TOKEN"],
            instructions=(
                "Fournir GITHUB_TOKEN via la couche secret manager "
                "(variable d'environnement ou Vault). Le token n'est jamais "
                "stocké dans les records ni dans le navigateur."
            ),
        ),
        featured=True,
    ),
    PluginManifest(
        id="web-search",
        name="Web Search",
        version="1.0.0",
        description=(
            "Recherche web en temps réel pour les conversations, la recherche "
            "documentaire et la veille."
        ),
        icon="Globe",
        categories=["research", "productivity"],
        capabilities=["search", "read"],
        tools=["builtin_web_search"],
        skills=["web_search"],
    PluginManifest(
        id="knowledge",
        name="Knowledge",
        version="1.0.0",
        description=(
            "Interroger les collections Knowledge et le pipeline RAG ETHAN : "
            "retrieval, citations et sources dans le chat."
        ),
        icon="BookOpen",
        categories=["knowledge", "research"],
        capabilities=["search", "read"],
        permissions=["read_data", "local_files"],
        featured=True,
    ),
    PluginManifest(
        id="code-interpreter",
        name="Code Interpreter",
        version="1.0.0",
        description=(
            "Exécuter du code Python dans un environnement contrôlé pour "
            "analyser des données, calculer et prototyper."
        ),
        icon="Code2",
        categories=["development", "automation"],
        capabilities=["execute", "create"],
        tools=["builtin_code_interpreter"],
        skills=["programming"],
        permissions=["execute", "local_files"],
        featured=True,
    ),
    PluginManifest(
        id="image-generation",
        name="Image Generation",
        version="1.0.0",
        description="Générer des images à partir de descriptions textuelles.",
        icon="ImagePlus",
        categories=["productivity", "automation"],
        capabilities=["create"],
        tools=["builtin_image_generation"],
        permissions=["external_network"],
    ),
    PluginManifest(
        id="pdf-analysis",
        name="PDF Analysis",
        version="1.0.0",
        description=(
            "Lire, analyser et extraire l'information de documents PDF "
            "(résumés, tableaux, métadonnées)."
        ),
        icon="FileText",
        categories=["files", "knowledge"],
        capabilities=["read", "search"],
        skills=["pdf_analysis"],
        permissions=["local_files", "read_data"],
    PluginManifest(
        id="email",
        name="Email Reader",
        version="1.0.0",
        description=(
            "Consulter et trier la boîte de réception : lecture des messages, "
            "recherche et synthèse des fils."
        ),
        icon="Mail",
        categories=["communication", "productivity"],
        capabilities=["read", "search"],
        skills=["email_reader"],
        permissions=["read_data", "external_network"],
        configuration=[
            PluginConfigurationField(
                key="mailbox",
                label="Boîte par défaut",
                type="string",
                description="Adresse ou alias de la boîte consultée.",
            ),
        ],
        authentication=PluginAuthentication(
            type="api_key",
            scopes=["imap_read"],
            env_vars=["ETHAN_EMAIL_USER", "ETHAN_EMAIL_PASSWORD"],
            instructions=(
                "Identifiants IMAP via secret manager uniquement "
                "(ETHAN_EMAIL_USER / ETHAN_EMAIL_PASSWORD)."
            ),
        ),
    ),
    PluginManifest(
        id="projects",
        name="Project Creator",
        version="1.0.0",
        description=(
            "Créer et structurer des projets ETHAN à partir d'une intention : "
            "squelette, instructions et organisation."
        ),
        icon="FolderKanban",
        categories=["productivity", "automation"],
        capabilities=["create", "update"],
        skills=["project_creator"],
        permissions=["local_files", "create", "modify"],
    ),
    PluginManifest(
        id="current-time",
        name="Horloge",
        version="1.0.0",
        description="Donner l'heure et la date exactes au modèle dans les conversations.",
        icon="Clock",
        categories=["local", "productivity"],
        capabilities=["execute"],
        tools=["builtin_current_time"],
        permissions=[],
    ),
    PluginManifest(
        id="slack",
        name="Slack Notifier",
        version="1.2.0",
        description="Envoyer des notifications et messages vers des canaux Slack.",
        icon="MessageSquare",
        categories=["communication", "automation"],
        capabilities=["create", "execute"],
        mcp=["slack-mcp"],
        permissions=["external_network", "create"],
        authentication=PluginAuthentication(
            type="api_key",
            scopes=["chat:write"],
            env_vars=["SLACK_BOT_TOKEN"],
            instructions="Fournir SLACK_BOT_TOKEN via secret manager.",
        ),
    ),
    PluginManifest(
        id="files",
        name="Files & Library",
        version="1.0.0",
        description=(
            "Parcourir, classer et joindre les fichiers de la Library et des "
            "dossiers ETHAN aux conversations."
        ),
        icon="FolderOpen",
        categories=["files", "productivity"],
        capabilities=["read", "create", "update", "search"],
        permissions=["local_files", "read_data", "modify"],
    ),
]


def find_manifest(plugin_id: str) -> PluginManifest | None:
    for manifest in BUILTIN_PLUGINS:
        if manifest.id == plugin_id:
            return manifest
    return None


def catalogue_categories() -> list[dict[str, str]]:
    """Catégories dynamiques dérivées du catalogue (pas de liste codée en dur)."""
    counts: dict[str, int] = {}
    for manifest in BUILTIN_PLUGINS:
        for category in manifest.categories:
            counts[category] = counts.get(category, 0) + 1
    return [
        {"id": category, "label": category.capitalize(), "count": str(counts[category])}
        for category in sorted(counts)
    ]


__all__ = ["BUILTIN_PLUGINS", "find_manifest", "catalogue_categories"]

    ),

        permissions=["external_network", "read_data"],
        featured=True,
    ),
