"""Email Reader Skill — Compétence de lecture d'emails."""

from __future__ import annotations

from core.skills.types import Skill, SkillStep
from core.skills.builtin.base import BaseBuiltinSkill


class EmailReaderSkill(BaseBuiltinSkill):
    """Skill de lecture d'emails.
    
    Outils utilisés :
    - email_client : Se connecter à la boîte mail
    - email_fetcher : Récupérer les emails
    - email_parser : Parser le contenu
    """

    def _build_skill(self) -> Skill:
        return Skill(
            id="email_reader",
            name="Email Reader",
            description="Read and analyze emails from inbox",
            version="1.0.0",
            category="communication",
            tags=["email", "mail", "communication", "inbox"],
            steps=[
                SkillStep(
                    id="step1",
                    name="Connect to mailbox",
                    description="Authenticate and connect",
                    tool_id="email_client",
                    parameters={"read_only": True},
                ),
                SkillStep(
                    id="step2",
                    name="Fetch emails",
                    description="Retrieve recent emails",
                    tool_id="email_fetcher",
                    parameters={"limit": 10, "unread_only": True},
                    depends_on=["step1"],
                ),
                SkillStep(
                    id="step3",
                    name="Parse content",
                    description="Extract and structure content",
                    tool_id="email_parser",
                    parameters={"extract_attachments": False},
                    depends_on=["step2"],
                ),
            ],
            required_tools=["email_client", "email_fetcher", "email_parser"],
            estimated_duration_ms=20000,
            risk_level="medium",
            is_builtin=True,
        )