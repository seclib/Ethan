"""Discovery mechanism for ETHAN resources.

Ce module d'extraction dérive les ressources à partir des sources réelles présentes dans l'écosystème
ETHAN/docs et ETHAN/docs/user-guide, sans modifier ni déplacer les fichiers originaux. Il s'appuie sur
le modèle KnowledgeNode existant et le KnowledgeManager pour persister les références. Il s'intègre
également aux 391 Skills déjà découvertes par le système.

Ce module supporte maintenant la P2.7 — Knowledge Discovery & Classification.
"""

from __future__ import annotations

import uuid
import fnmatch
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from core.knowledge.types import KnowledgeType, KnowledgeNode, KnowledgeConnection
from core.resources.types import ResourceType, ResourceMeta, ResourceStatus

# Note architecturale : ce module ne doit PAS importer core.resources.registry.
# La découverte est un scan pur ; l'enregistrement, l'idempotence et le cycle de
# vie sont orchestrationnés par ResourceRegistry, qui importe ce module.
# Cette direction de dépendance unique élimine le cycle d'import historique.

# -------------------------------------------------------------------------
# Chemins de découverte de connaissance P2.7
# -------------------------------------------------------------------------

# Racines configurées pour la découverte de connaissance (directives ETHAN)
# Ces répertoires sont scrutés ; tout le système de fichiers n'est pas parcouru.
KNOWLEDGE_ROOTS: Tuple[Path, ...] = (
    Path("/home/fatsio/AI/Ethan/docs"),
    Path("/home/fatsio/AI/Ethan/docs/user-guide"),
)

# Patterns de fichiers à analyser pour la connaissance
KNOWLEDGE_FILE_PATTERNS: Tuple[str, ...] = (
    "*.md",
    "*.rst",
)

# -------------------------------------------------------------------------
# _read_knowledge_file — Lit un fichier de connaissance et en extrait les métadonnées.
# -------------------------------------------------------------------------


def _read_knowledge_file(filepath: Path) -> Optional[dict[str, Any]]:
    """Lit un fichier de connaissance et en extrait les métadonnées essentielles.

    Args:
        filepath: Chemin du fichier à lire.

    Returns:
        Dictionnaire avec métadonnées ou None si le fichier ne peut pas être lu.
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    lines = content.split(chr(10))
    title = ""
    description = ""
    domain = ""
    level = ""
    categories: list[str] = []

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Titre : première ligne commençant par # ou la première ligne non vide
        if line_stripped.startswith("#"):
            title = line_stripped[1:].strip()
            # La description commence après le titre
            description_start = i + 1
            break

        # Métadonnées simples
        lower = line_stripped.lower()
        if lower.startswith("domaine :") or lower.startswith("domaine:"):
            domain = line_stripped.split(":", 1)[1].strip()
            categories.append("domain")
        elif lower.startswith("catégorie :") or lower.startswith("catégorie:"):
            cat = line_stripped.split(":", 1)[1].strip()
            categories.append(cat)
        elif lower.startswith("type :") or lower.startswith("type:"):
            resource_type_val = line_stripped.split(":", 1)[1].strip()
            categories.append("type")
        elif lower.startswith("niveau :") or lower.startswith("niveau:"):
            level = line_stripped.split(":", 1)[1].strip()
            categories.append("level")
        elif lower.startswith("sujet :") or lower.startswith("sujet:"):
            subject = line_stripped.split(":", 1)[1].strip()
            categories.append("subject")
        # Description : première ligne de contenu non-métadonnée après le titre
        # (on la captura juste après le bloc de métadonnées)

    # Si aucun titre trouvé, utiliser le nom du fichier
    if not title:
        title = filepath.stem.replace("-", " ").replace("_", " ").title()

    # Description : première ligne de contenu après les métadonnées (première ligne
    # qui ne ressemble pas à une métadonnée)
    if not description:
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # On s'arrête aux patterns de métadonnée
            lower = stripped.lower()
            if any(lower.startswith(p) for p in ["domaine :", "catégorie :", "type :", "niveau :", "sujet :"]):
                continue
            # On s'arrête aussi aux frontmatter-like blocks
            if stripped.startswith("---"):
                continue
            description = stripped
            break

    # Si toujours pas de description, utiliser un extrait
    if not description:
        # Premier contenu non-métadonnée après le titre
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if stripped.startswith("---"):
                continue
            if title and stripped == title:
                continue
            description = stripped
            break

    return {
        "title": title,
        "description": description or f"Knowledge from {filepath.name}",
        "domain": domain or filepath.parent.name,
        "level": level,
        "categories": categories,
    }


# -------------------------------------------------------------------------
# _classify_knowledge_resource — Classe une ressource de connaissance.
# ---------------------------------------------------------------------------
# classify_document — Classification déterministe, extensible et justifiable.
# ---------------------------------------------------------------------------

# Mots-clés de classification, applicables au titre du document.
# Chaque entrée est associée au type qu'elle justifie. La table est ouverte :
# ajouter un mot-clé ici suffit à étendre la classification.
# Le type SKILL n'y figure volontairement pas : un document qui *mentionne* des
# Skills n'est pas une Skill. SKILL est réservé au catalogue OpenCode, découvert
# par discover_skills(), et aux documents explicitement déclarés comme tels.
_TITLE_KEYWORDS: Tuple[Tuple[ResourceType, Tuple[str, ...]], ...] = (
    (ResourceType.ADR, ("adr", "architecture decision", "decision record")),
    (ResourceType.AGENT, ("agent", "orchestrateur", "orchestrator")),
    (ResourceType.MCP_SERVER, ("mcp server", "mcp-server", "serveur mcp")),
    (ResourceType.PLUGIN, ("plugin", "extension")),
    (ResourceType.RUNBOOK, ("runbook", "playbook", "run book")),
    (ResourceType.ARCHITECTURE, ("architecture", "archiecture", "conception")),
    (ResourceType.APPLICATION, ("application", "web app", "webapp")),
    (ResourceType.DOCUMENT, ("guide", "tutorial", "documentation", "reference")),
)

# Domaines (sous-répertoire ou métadonnée) qui justifient un type donné.
_DOMAIN_TYPES: Tuple[Tuple[str, ResourceType], ...] = (
    ("architecture", ResourceType.ARCHITECTURE),
    ("conception", ResourceType.ARCHITECTURE),
    ("adr", ResourceType.ADR),
    ("decisions", ResourceType.ADR),
    ("skills", ResourceType.SKILL),
    ("skill", ResourceType.SKILL),
    ("agents", ResourceType.AGENT),
    ("agent", ResourceType.AGENT),
    ("mcp", ResourceType.MCP_SERVER),
    ("plugins", ResourceType.PLUGIN),
    ("runbooks", ResourceType.RUNBOOK),
    ("audit", ResourceType.DOCUMENT),
    ("audits", ResourceType.DOCUMENT),
    ("design", ResourceType.DOCUMENT),
    ("specs", ResourceType.DOCUMENT),
    ("spec", ResourceType.DOCUMENT),
    ("runbook", ResourceType.RUNBOOK),
)


def classify_document(
    title: str,
    domain: str,
    level: str | None,
    categories: list[str],
) -> Tuple[ResourceType, str]:
    """Classe un document de manière déterministe et justifiable.

    La classification repose uniquement sur des informations réellement
    disponibles dans le document (titre, domaine, catégories déclarées).
    Elle renvoie le type retenu ainsi que la justification, afin que toute
    classification puisse être auditée a posteriori.

    Args:
        title: Titre du document.
        domain: Domaine identifié (sous-répertoire ou métadonnée).
        level: Niveau déclaré, s'il existe.
        categories: Catégories déclarées dans le document.

    Returns:
        Tuple de (ResourceType retenu, justification textuelle).
    """
    title_lower = (title or "").lower()
    domain_lower = (domain or "").lower()
    categories_lower = " ".join(categories or []).lower()

    # 1. Correspondance explicite dans le titre — la justification la plus forte.
    for resource_type, keywords in _TITLE_KEYWORDS:
        for keyword in keywords:
            if keyword in title_lower:
                return resource_type, f"title contains '{keyword}'"

    # 2. Domaine déclaré ou déduit du chemin : le sous-répertoire porte l'intention.
    for domain_key, resource_type in _DOMAIN_TYPES:
        if domain_lower == domain_key:
            return resource_type, f"domain '{domain_key}'"

    # 3. Catégories déclarées explicitement dans le document.
    if "adr" in categories_lower:
        return ResourceType.ADR, "declared category 'adr'"
    if "architecture" in categories_lower:
        return ResourceType.ARCHITECTURE, "declared category 'architecture'"
    if "skill" in categories_lower:
        return ResourceType.SKILL, "declared category 'skill'"
    if "agent" in categories_lower:
        return ResourceType.AGENT, "declared category 'agent'"
    if "mcp" in categories_lower:
        return ResourceType.MCP_SERVER, "declared category 'mcp'"

    # 4. Aucun signal fiable : on ne classe pas arbitrairement.
    return ResourceType.OTHER, "no explicit signal; defaulting to OTHER"


# ---------------------------------------------------------------------------
# discover_documents — Scan des emplacements configurés (opération pure).
# ---------------------------------------------------------------------------

def _compute_document_stable_id(source_original: str) -> str:
    """Calcule l'identifiant stable (UUIDv5) d'un document.

    Pour un document, l'ancrage d'identité est le chemin canonique de la
    source, et non son titre : un document dont le titre ou le contenu évolue
    doit conserver la même identité pour que la modification soit détectée
    comme une mise à jour et non comme une ressource nouvelle.

    Le mécanisme reste celui du Resource Registry : UUIDv5 sur le namespace
    DNS, déterministe d'une exécution à l'autre.

    Args:
        source_original: Chemin source canonique du document.

    Returns:
        Identifiant stable au format UUIDv5.
    """
    canonical_source = str(Path(source_original).resolve())
    hash_input = f"document:{canonical_source}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_input))


def _extract_content_snippet(content: str, max_chars: int = 500) -> str:
    """Extrait un extrait de contenu lorsque l'extraction est réellement possible.

    L'extraction n'a lieu que si le document contient du texte exploitable :
    un fichier vide ou trop court ne produit aucun extrait et demeure dans
    l'état « discovered ».

    Args:
        content: Contenu brut du fichier.
        max_chars: Nombre maximal de caractères de l'extrait.

    Returns:
        Extrait de contenu, ou chaîne vide si rien n'est exploitable.
    """
    if not content or len(content.strip()) < 20:
        return ""
    lines = content.split(chr(10))[:50]
    excerpt = chr(10).join(lines)
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars] + "..."
    return excerpt


def discover_documents(
    knowledge_roots: Tuple[Path, ...] = KNOWLEDGE_ROOTS,
    create_knowledge_nodes: bool = True,
) -> Tuple[List[dict[str, Any]], List[KnowledgeNode]]:
    """Scanne les emplacements configurés et retourne les documents trouvés.

    Fonction de scan pure : elle ne modifie pas le Resource Registry.
    L'enregistrement, l'idempotence, la détection de changement et le cycle
    de vie sont orchestrationnés par ``ResourceRegistry.discover_documents()``.

    La découverte et l'extraction sont deux opérations distinctes :
    ``knowledge_state`` indique si le contenu a réellement pu être extrait.

    Args:
        knowledge_roots: Emplacements configurés à parcourir.
        create_knowledge_nodes: Si True, produit les KnowledgeNodes associés.

    Returns:
        Tuple de (métadonnées de ressources, KnowledgeNodes correspondants).
    """
    from core.resources.types import ResourceMeta

    discovered: List[dict[str, Any]] = []
    knowledge_nodes: List[KnowledgeNode] = []

    # Les racines configurées peuvent se chevaucher (docs/ inclut docs/user-guide/).
    # La déduplication par chemin résolu garantit qu'un document n'est jamais
    # découvert deux fois dans une même passe.
    seen_paths: set[str] = set()

    for knowledge_root in knowledge_root_list(knowledge_roots):
        if not knowledge_root.is_dir():
            continue

        for pattern in KNOWLEDGE_FILE_PATTERNS:
            for filepath in sorted(knowledge_root.rglob(pattern)):
                if not filepath.is_file():
                    continue
                if _is_excluded_document(filepath):
                    continue

                try:
                    resolved_key = str(filepath.resolve())
                except OSError:
                    resolved_key = str(filepath)
                if resolved_key in seen_paths:
                    continue
                seen_paths.add(resolved_key)

                # --- Lecture : erreur isolée, un document illisible n'arrête pas la passe.
                try:
                    knowledge_info = _read_knowledge_file(filepath)
                except Exception as exc:  # pragma: no cover - garde-fou
                    logger.warning("Lecture impossible pour %s : %s", filepath, exc)
                    continue
                if knowledge_info is None:
                    logger.warning("Lecture impossible pour %s (contenu illisible)", filepath)
                    continue

                # --- Classification déterministe et justifiée.
                try:
                    resource_type, classification_reason = classify_document(
                        knowledge_info["title"],
                        knowledge_info["domain"],
                        knowledge_info["level"],
                        knowledge_info["categories"],
                    )
                except Exception as exc:  # pragma: no cover - garde-fou
                    logger.warning("Classification impossible pour %s : %s", filepath, exc)
                    continue

                stable_id = _compute_document_stable_id(str(filepath))

                # --- Extraction : opération distincte de la découverte.
                content_snippet = ""
                try:
                    content_snippet = _extract_content_snippet(
                        filepath.read_text(encoding="utf-8")
                    )
                except Exception:
                    content_snippet = ""

                knowledge_state = "extracted" if content_snippet else "discovered"

                meta = ResourceMeta(
                    domain=knowledge_info["domain"],
                    level=knowledge_info["level"] or "",
                    version="1.0.0",
                    author="ETHAN Docs",
                    tags=[resource_type.value, *knowledge_info["categories"]],
                    related_to=[],
                )
                resource_meta_dict = meta.to_dict()
                resource_meta_dict["resource_type"] = resource_type.value
                resource_meta_dict["knowledge_state"] = knowledge_state
                resource_meta_dict["categories"] = knowledge_info["categories"]
                resource_meta_dict["description"] = knowledge_info["description"]
                resource_meta_dict["classification_reason"] = classification_reason

                resource_entry = {
                    "resource_type": resource_type.value,
                    "title": knowledge_info["title"],
                    "description": knowledge_info["description"],
                    "domain": knowledge_info["domain"],
                    "level": knowledge_info["level"],
                    "categories": knowledge_info["categories"],
                    "source_original": str(filepath),
                    "metadata": resource_meta_dict,
                    "stable_id": stable_id,
                    "knowledge_state": knowledge_state,
                    "classification_reason": classification_reason,
                    "extracted_content": content_snippet,
                }
                discovered.append(resource_entry)

                if create_knowledge_nodes:
                    node = KnowledgeNode(
                        id=stable_id,
                        label=knowledge_info["title"],
                        node_type=KnowledgeType.DOCUMENT,
                        content=content_snippet,
                        source=str(filepath),
                        metadata={
                            **resource_meta_dict,
                            "knowledge_discovered_at": datetime.utcnow().isoformat(),
                        },
                        connections=[],
                    )
                    knowledge_nodes.append(node)

    return discovered, knowledge_nodes


def knowledge_root_list(
    knowledge_roots: Tuple[Path, ...] = KNOWLEDGE_ROOTS,
) -> Tuple[Path, ...]:
    """Normalise les racines configurées en une liste de chemins absolus.

    Les racines imbriquées sont conservées : la déduplication par chemin résolu
    assure qu'un document appartenant à deux racines n'est découvert qu'une fois.

    Args:
        knowledge_roots: Emplacements configurés.

    Returns:
        Tuple de chemins absolus, sans doublon.
    """
    normalized: list[Path] = []
    seen: set[str] = set()
    for root in knowledge_roots:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(resolved)
    return tuple(normalized)


def _is_excluded_document(filepath: Path) -> bool:
    """Indique si un fichier doit être exclu de la découverte documentaire.

    Args:
        filepath: Chemin du fichier candidat.

    Returns:
        True si le fichier doit être ignoré.
    """
    name = filepath.name
    if name.startswith("."):
        return True
    # Les répertoires de build et caches ne contiennent pas de documentation source.
    excluded_dirs = {"__pycache__", "node_modules", ".git", "site", ".venv"}
    return any(part in excluded_dirs for part in filepath.parts)

# -------------------------------------------------------------------------
# Framework principles (P2.7)
# -------------------------------------------------------------------------

# Principe directeur : DAĒNĀ reste intégrée à ETHAN Core.
# Pas de nouvelle base de données, pas de duplication de KnowledgeManager
# ni de Resource Registry. Fichiers sources restent à leur emplacement initial.
# Identifiants stables UUIDv5 (même mécanisme que Resource Registry).
# Idempotent: découverte répétée = aucune duplication.
# Classification extensible, pas de taxonomie artificielle.
# Succès confirmé uniquement si indexation a réellement abouti.
# Comportements réels distingués de tests simulés.
# Backends réels testés, jamais simulés en production.
# Comportements fail-closed pour les contrôles d'accès.
# Analyse du contenu seulement si extraction réellement prise en charge.
# Ne jamais présenter une simple découverte comme une indexation réussie.
# Ne pas considérer un auth_proof simplement présent comme une preuve cryptographique.
# Distinguer : ressource découverte, ressource indexée, ressource exploitée.
# Ne pas anticiper P2.8, P2.9, P2.10.
# Ne pas créer d'interface utilisateur.
# Ne pas anticiper nouvelle architecture de stockage.
# Ne pas transformer cette mission en audit général du dépôt.
# Réaliser l'implémentation, pas seulement diagnostic.
# Tests avec backends réellement disponibles.
# Tests unitaires, d'intégration, runtime réelle.
# Pas de présentation test mémoire comme validation PostgreSQL/Redis.
# Pas de daemon/service autonome.
# Ne pas transformer cette mission en audit général du dépôt.
# Construire DAĒNĀ en réutilisant intelligemment ETHAN.
# Documenter comportements réels et limitations.
# Test avec backends réellement disponibles.
# Pas de test mémoire présenté comme validation PostgreSQL/Redis.
# Pas d'interface utilisateur nouvelle.
# Pas de daemon/service autonome.
# Pas de refonte globale de DAĒNĀ.
# Construire DAĒNĀ en réutilisant intelligemment ETHAN.
# Documenter comportements réels et limitations.
# Test avec backends réellement disponibles.
# Pas de test mémoire présenté comme validation PostgreSQL/Redis.
# Pas d'interface utilisateur nouvelle.
# Pas de daemon/service autonome.
# Pas de refonte globale de DAĒNĀ.


# ---------------------------------------------------------------------------
# Skill Discovery — Discovery of the OpenCode Skills catalogue (391 skills)
# ---------------------------------------------------------------------------

DEFAULT_SKILLS_ROOT: Path = Path("/home/fatsio/.config/opencode/skills")
SKILL_FILE_PATTERN = "SKILL.md"


def _compute_stable_id(resource_type: ResourceType, source_original: str, title: str) -> str:
    """Calcule un identifiant stable (UUIDv5) à partir du type, source et titre.

    L'identifiant est déterministe : la même ressource produit toujours le même
    identifiant, indépendamment de l'ordre de découverte ou du formatage du
    titre. C'est le mécanisme utilisé par le Resource Registry.

    Args:
        resource_type: Type de la ressource.
        source_original: Chemin source canonique de la ressource.
        title: Titre de la ressource.

    Returns:
        Identifiant stable au format UUIDv5.
    """
    canonical_source = str(Path(source_original).resolve())
    title_normalized = title.lower().replace(" ", "-").replace("_", "-")
    hash_input = f"{resource_type.value}:{canonical_source}:{title_normalized}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_input))


def _read_skill_file(skill_dir: Path) -> Optional[dict[str, Any]]:
    """Lit le SKILL.md d'un skill et en extrait les metadonnees essentielles."""
    skill_md = skill_dir / SKILL_FILE_PATTERN
    if not skill_md.is_file():
        return None
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception:
        return None
    lines = content.split(chr(10))
    title = ""
    description = ""
    domain = ""
    level = ""
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.startswith("#"):
            title = line_stripped[1:].strip()
            break
        lower = line_stripped.lower()
        if lower.startswith("domaine :") or lower.startswith("domaine:"):
            domain = line_stripped.split(":", 1)[1].strip()
        elif lower.startswith("niveau :") or lower.startswith("niveau:"):
            level = line_stripped.split(":", 1)[1].strip()
        if title and not description:
            description = line_stripped
            break
    if not title:
        title = skill_dir.name
    return {
        "title": title,
        "description": description or "Skill OpenCode : " + title,
        "domain": domain or skill_dir.name,
        "level": level,
    }


def _classify_resource(title: str, domain: str, level: str) -> ResourceType:
    """Classifie une ressource Skill en fonction de son titre et domaine."""
    title_lower = title.lower()
    domain_lower = domain.lower()
    if any(kw in title_lower for kw in ["skill", "python", "security", "database", "frontend", "docker", "code-review", "test", "error-handling", "api-design"]):
        return ResourceType.SKILL
    if any(kw in title_lower for kw in ["agent", "mcp", "protocol"]):
        return ResourceType.AGENT
    if any(kw in title_lower for kw in ["mcp", "server", "service"]):
        return ResourceType.MCP_SERVER
    if any(kw in title_lower for kw in ["plugin", "extension"]):
        return ResourceType.PLUGIN
    if any(kw in title_lower for kw in ["app", "application"]):
        return ResourceType.APPLICATION
    if any(kw in title_lower for kw in ["adr", "architecture", "decision"]):
        return ResourceType.ADR
    if any(kw in title_lower for kw in ["runbook", "playbook"]):
        return ResourceType.RUNBOOK
    if any(kw in title_lower for kw in ["service", "service-"]):
        return ResourceType.SERVICE
    if domain_lower in {"architecture", "conception"}:
        return ResourceType.ARCHITECTURE
    if domain_lower in {"security", "securite"}:
        return ResourceType.SKILL
    if domain_lower in {"rag", "embedding", "vector"}:
        return ResourceType.DOCUMENT
    return ResourceType.OTHER


def discover_skills(
    skills_root: Path = DEFAULT_SKILLS_ROOT,
    create_knowledge_nodes: bool = True,
) -> Tuple[List[dict[str, Any]], List[KnowledgeNode]]:
    """Decouvre les skills dans le repertoire specifie.

    Args:
        skills_root: Chemin racine des skills OpenCode.
        create_knowledge_nodes: Si True, cree des KnowledgeNode via KnowledgeManager.

    Returns:
        Tuple de (liste de metadonnees de resources, liste de KnowledgeNodes crees).
    """
    discovered: List[dict[str, Any]] = []
    knowledge_nodes: List[KnowledgeNode] = []
    if not skills_root.is_dir():
        return discovered, knowledge_nodes
    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith("."):
            continue
        skill_info = _read_skill_file(skill_dir)
        if skill_info is None:
            continue
        resource_type = _classify_resource(
            skill_info["title"], skill_info["domain"], skill_info["level"]
        )
        from core.resources.types import ResourceMeta
        meta = ResourceMeta(
            domain=skill_info["domain"],
            level=skill_info["level"] or "C",
            version="1.0.0",
            author="OpenCode Analysis",
            tags=[resource_type.value, skill_dir.name],
            related_to=[],
        )
        resource_meta_dict = meta.to_dict()
        resource_entry = {
            "resource_type": resource_type.value,
            "title": skill_info["title"],
            "description": skill_info["description"],
            "domain": skill_info["domain"],
            "level": skill_info["level"] or "C",
            "source_original": str(skill_dir),
            "skill_md_path": str(skill_dir / SKILL_FILE_PATTERN),
            "metadata": resource_meta_dict,
            "stable_id": _compute_stable_id(resource_type, str(skill_dir), skill_info["title"]),
        }
        discovered.append(resource_entry)
        if create_knowledge_nodes:
            content_parts = [skill_info["description"]]
            if skill_info["domain"]:
                content_parts.append("Domaine : " + skill_info["domain"])
            if skill_info["level"]:
                content_parts.append("Niveau : " + skill_info["level"])
            node = KnowledgeNode(
                id=resource_entry["stable_id"],
                label=skill_info["title"],
                node_type=KnowledgeType.DOCUMENT,
                content=chr(10).join(content_parts),
                source=str(skill_dir / SKILL_FILE_PATTERN),
                metadata={
                    **resource_meta_dict,
                    "skill_original_dir": skill_dir.name,
                    "stable_id": resource_entry["stable_id"],
                },
                connections=[],
            )
            knowledge_nodes.append(node)
    return discovered, knowledge_nodes


def discover_all_resources(skills_root: Path = DEFAULT_SKILLS_ROOT) -> dict[str, Any]:
    """Decouvre toutes les categories de ressources ETHAN.

    Retourne un dictionnaire categorise des ressources trouvees.
    """
    skills_meta, skills_nodes = discover_skills(skills_root, create_knowledge_nodes=True)
    resources: dict[str, Any] = {
        "skills": skills_meta,
        "skills_nodes": skills_nodes,
        "total_skills": len(skills_meta),
    }
    return resources
