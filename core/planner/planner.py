"""ETHAN Planner — Goal decomposition and task planning"""

import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from core.registry import CapabilityRegistry


@dataclass
class Goal:
    """A high-level goal"""
    id: str = field(default_factory=lambda: f"goal-{uuid.uuid4().hex[:8]}")
    description: str = ""
    state: str = "created"  # created, active, completed, failed, cancelled
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class Plan:
    """An execution plan (DAG of tasks)"""
    id: str = field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    goal_id: str = ""
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "created"  # created, executing, completed, failed
    created_at: float = field(default_factory=time.time)


class Planner:
    """Planner — decomposes goals into executable tasks"""
    
    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        self._registry = registry or CapabilityRegistry()
        self._goals: Dict[str, Goal] = {}
        self._plans: Dict[str, Plan] = {}
        self._running = False
        self._patterns: Dict[str, List[Dict[str, Any]]] = self._init_patterns()
        
    def _init_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize task decomposition patterns"""
        return {
            "status": [
                {"capability": "system.status", "params": {}, "depends_on": []},
            ],
            "health": [
                {"capability": "system.health", "params": {}, "depends_on": []},
            ],
            "message": [
                {"capability": "message.echo", "params": {"type": "message"}, "depends_on": []},
            ],
        }
    
    async def start(self) -> None:
        """Start the planner"""
        self._running = True
        
    async def stop(self) -> None:
        """Stop the planner"""
        self._running = False
    
    def create_goal(self, description: str, priority: int = 0, **metadata) -> Goal:
        """Create a new goal"""
        goal = Goal(
            description=description,
            priority=priority,
            metadata=metadata,
        )
        self._goals[goal.id] = goal
        return goal
    
    def decompose(self, goal: Goal) -> Optional[Plan]:
        """Decompose a goal into a plan (DAG of tasks)"""
        goal.state = "active"
        
        # Find matching pattern
        pattern = self._find_pattern(goal.description)
        if not pattern:
            return None
        
        # Create tasks from pattern
        tasks = []
        for step in pattern:
            task = {
                "id": f"task-{uuid.uuid4().hex[:8]}",
                "capability": step["capability"],
                "params": {**step["params"]},
                "depends_on": step.get("depends_on", []),
            }
            task["params"]["goal_id"] = goal.id
            tasks.append(task)
        
        # Create plan
        plan = Plan(
            goal_id=goal.id,
            tasks=tasks,
        )
        self._plans[plan.id] = plan
        
        return plan
    
    def _find_pattern(self, description: str) -> Optional[List[Dict[str, Any]]]:
        """Find a decomposition pattern for a goal"""
        desc_lower = description.lower()
        
        # Direct pattern matches
        for key, pattern in self._patterns.items():
            if key in desc_lower:
                return pattern
        
        # Search registry for matching capabilities
        capabilities = self._registry.find(desc_lower)
        if capabilities:
            return [
                {"capability": cap.name, "params": {}, "depends_on": []}
                for cap in capabilities[:3]  # Max 3 tasks
            ]
        
        return self._patterns.get("message")
    
    def add_pattern(self, name: str, tasks: List[Dict[str, Any]]) -> None:
        """Add a task decomposition pattern"""
        self._patterns[name] = tasks
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID"""
        return self._goals.get(goal_id)
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by ID"""
        return self._plans.get(plan_id)
    
    def get_active_goals(self) -> List[Goal]:
        """Get active goals"""
        return [g for g in self._goals.values() if g.state == "active"]
    
    def get_goals_by_state(self, state: str) -> List[Goal]:
        """Get goals by state"""
        return [g for g in self._goals.values() if g.state == state]
    
    def complete_goal(self, goal_id: str) -> None:
        """Mark a goal as completed"""
        goal = self._goals.get(goal_id)
        if goal:
            goal.state = "completed"
    
    def fail_goal(self, goal_id: str, reason: str = "") -> None:
        """Mark a goal as failed"""
        goal = self._goals.get(goal_id)
        if goal:
            goal.state = "failed"
            if reason:
                goal.metadata["fail_reason"] = reason
    
    @property
    def goals_count(self) -> int:
        return len(self._goals)
    
    @property
    def plans_count(self) -> int:
        return len(self._plans)
    
    @property
    def active_goals_count(self) -> int:
        return len(self.get_active_goals())