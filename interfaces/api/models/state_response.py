"""State response model."""

from pydantic import BaseModel


class StateResponse(BaseModel):
    mode: str = "idle"
    active_goal: str | None = None
    running_tasks: int = 0
    modules_active: list[str] = []
    last_event: str | None = None
