"""Web Search Skill — Compétence de recherche web."""

from __future__ import annotations

from core.skills.types import Skill, SkillStep
from core.skills.builtin.base import BaseBuiltinSkill


class WebSearchSkill(BaseBuiltinSkill):
    """Skill de recherche web.
    
    Outils utilisés :
    - web_search : Rechercher sur Internet
    - web_scraper : Extraire le contenu
    - content_summarizer : Résumer le contenu
    """

    def _build_skill(self) -> Skill:
        return Skill(
            id="web_search",
            name="Web Search",
            description="Search the web and extract relevant information",
            version="1.0.0",
            category="research",
            tags=["web", "search", "internet", "research"],
            steps=[
                SkillStep(
                    id="step1",
                    name="Search web",
                    description="Perform web search",
                    tool_id="web_search",
                    parameters={"max_results": 5},
                ),
                SkillStep(
                    id="step2",
                    name="Extract content",
                    description="Extract content from top results",
                    tool_id="web_scraper",
                    parameters={"extract_text": True},
                    depends_on=["step1"],
                ),
                SkillStep(
                    id="step3",
                    name="Summarize findings",
                    description="Summarize extracted content",
                    tool_id="content_summarizer",
                    parameters={"max_length": 500},
                    depends_on=["step2"],
                ),
            ],
            required_tools=["web_search", "web_scraper", "content_summarizer"],
            estimated_duration_ms=30000,
            risk_level="low",
            is_builtin=True,
        )