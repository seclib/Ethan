"""Builtin Skills — Skills intégrées à ETHAN."""

from .programming import ProgrammingSkill
from .web_search import WebSearchSkill
from .pdf_analysis import PDFAnalysisSkill
from .email_reader import EmailReaderSkill
from .project_creator import ProjectCreatorSkill

__all__ = [
    "ProgrammingSkill",
    "WebSearchSkill",
    "PDFAnalysisSkill",
    "EmailReaderSkill",
    "ProjectCreatorSkill",
    "iter_builtin_skill_specs",
]


def iter_builtin_skill_specs() -> list[dict]:
    """Sérialise les skills builtin pour le SkillStore (kind="pipeline").

    Le code reste la source de vérité de la définition ; cette fonction
    produit les records persistés par ``SkillStore.sync_builtin_skills``
    (visibles dans ``/v1/skills``, associables aux Agents, classables
    dans les dossiers/domains).  Le ``content`` est généré depuis les
    étapes : il décrit le pipeline sans jamais exécuter de code.
    """
    specs: list[dict] = []
    for cls in (
        ProgrammingSkill,
        WebSearchSkill,
        PDFAnalysisSkill,
        EmailReaderSkill,
        ProjectCreatorSkill,
    ):
        skill = cls().get_skill()
        steps = [
            {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "tool_id": step.tool_id,
                "parameters": dict(step.parameters),
                "depends_on": list(step.depends_on),
                "optional": bool(step.optional),
            }
            for step in skill.steps
        ]
        required_tools = list(skill.required_tools) or sorted(
            {s["tool_id"] for s in steps if s.get("tool_id")}
        )
        content_lines = [f"{skill.name} — {skill.description}", "Pipeline d'étapes :"]
        content_lines += [
            f"- {s['name']} (outil: {s['tool_id']})" for s in steps if s.get("tool_id")
        ]
        if required_tools:
            content_lines.append(f"Outils requis : {', '.join(required_tools)}")
        specs.append(
            {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "version": skill.version,
                "tags": list(skill.tags),
                "kind": "pipeline",
                "steps": steps,
                "required_tools": required_tools,
                "content": "\n".join(content_lines),
                "author": "system",
                "is_builtin": True,
            }
        )
    return specs
