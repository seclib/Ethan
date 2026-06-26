"""Feedback subsystem: LLM-as-judge scoring and signal aggregation."""

from ethan.learning.optimize.feedback.collector import FeedbackCollector
from ethan.learning.optimize.feedback.judge import TraceJudge

__all__ = ["TraceJudge", "FeedbackCollector"]
