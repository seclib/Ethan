"""PDF Analysis Skill — Compétence d'analyse de PDF."""

from __future__ import annotations

from core.skills.types import Skill, SkillStep
from core.skills.builtin.base import BaseBuiltinSkill


class PDFAnalysisSkill(BaseBuiltinSkill):
    """Skill d'analyse de PDF.
    
    Outils utilisés :
    - pdf_reader : Lire un PDF
    - text_extractor : Extraire le texte
    - summarizer : Résumer le contenu
    """

    def _build_skill(self) -> Skill:
        return Skill(
            id="pdf_analysis",
            name="PDF Analysis",
            description="Analyze PDF documents and extract insights",
            version="1.0.0",
            category="document",
            tags=["pdf", "document", "analysis", "extraction"],
            steps=[
                SkillStep(
                    id="step1",
                    name="Read PDF",
                    description="Load PDF document",
                    tool_id="pdf_reader",
                    parameters={"extract_metadata": True},
                ),
                SkillStep(
                    id="step2",
                    name="Extract text",
                    description="Extract text content",
                    tool_id="text_extractor",
                    parameters={"preserve_formatting": True},
                    depends_on=["step1"],
                ),
                SkillStep(
                    id="step3",
                    name="Analyze content",
                    description="Analyze and summarize",
                    tool_id="summarizer",
                    parameters={"max_length": 1000},
                    depends_on=["step2"],
                ),
            ],
            required_tools=["pdf_reader", "text_extractor", "summarizer"],
            estimated_duration_ms=45000,
            risk_level="low",
            is_builtin=True,
        )