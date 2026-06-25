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
]