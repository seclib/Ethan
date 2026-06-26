"""External-framework subprocess backends (Hermes Agent, OpenClaw)."""

from ethan.evals.backends.external.hermes_agent import HermesBackend
from ethan.evals.backends.external.openclaw import OpenClawBackend

__all__ = ["HermesBackend", "OpenClawBackend"]
