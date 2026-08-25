"""ETHAN Core — Chat Pipeline module.

Core-owned orchestration for chat completions: conversation tree persistence,
context resolution (skills, RAG), LLM generation and event emission.
"""

from core.chat.pipeline import ChatPipeline

__all__ = ["ChatPipeline"]