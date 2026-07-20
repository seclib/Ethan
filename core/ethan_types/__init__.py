"""ETHAN Core — Types partagés entre tous les composants.

Ces dataclasses sont le contrat de données du système.
Ils sont utilisés par le Kernel Go, les modules Python, et les interfaces.
"""

from .event import Event, EventType
from .message import ChatMessage, ChatResponse, Message
from .capability import Capability, Dependency
from .goal import Goal, GoalState, GoalPriority
from .plan import Plan, Task, TaskState, TaskDAG
from .module import ModuleConfig, ModuleState
from .result import Result, Error, Progress

__all__ = [
    "Event", "EventType",
    "ChatMessage", "ChatResponse", "Message",
    "Capability", "Dependency",
    "Goal", "GoalState", "GoalPriority",
    "Plan", "Task", "TaskState", "TaskDAG",
    "ModuleConfig", "ModuleState",
    "Result", "Error", "Progress",
]