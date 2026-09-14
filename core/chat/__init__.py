"""ETHAN Core — Chat Pipeline module.

Core-owned orchestration for chat completions: conversation tree persistence,
context resolution (skills, RAG), LLM generation and event emission.

Modules :
    pipeline        orchestration (mode, contextes, compaction, génération)
    modes           Plan/Act/Debug — types, profils, permissions, reasoning
    session         réglages de session (global / conversation / mode / requête)
    compaction      Auto Compact (§14) — compaction préservante (§16)
    context_sources Add Context typé (§10) — sérialisation bornée par le Core
"""

from core.chat.pipeline import ChatPipeline

__all__ = ["ChatPipeline"]