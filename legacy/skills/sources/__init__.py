"""Skill source resolvers — Hermes, OpenClaw, generic GitHub."""

from ethan.skills.sources.base import ResolvedSkill, SourceResolver
from ethan.skills.sources.github import GitHubResolver
from ethan.skills.sources.hermes import HERMES_REPO_URL, HermesResolver
from ethan.skills.sources.openclaw import OPENCLAW_REPO_URL, OpenClawResolver

__all__ = [
    "GitHubResolver",
    "HERMES_REPO_URL",
    "HermesResolver",
    "OPENCLAW_REPO_URL",
    "OpenClawResolver",
    "ResolvedSkill",
    "SourceResolver",
]
