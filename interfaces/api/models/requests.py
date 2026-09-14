"""Pydantic request/response models for the API Gateway."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """Incoming user message."""
    input: str = Field(..., description="User input text")
    session_id: Optional[str] = Field("", description="Optional session identifier")
    user_id: Optional[str] = Field("anonymous", description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Response after emitting the event to the system."""
    success: bool = True
    event_id: str = ""
    goal_id: str = ""
    message: str = "Event emitted into cognitive system"


class IntentRequest(BaseModel):
    """Structured intent from external systems."""
    source: str = Field("api", description="Source of the intent")
    input: str = Field(..., description="Intent input")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: Optional[str] = Field("")
    user_id: Optional[str] = Field("anonymous")