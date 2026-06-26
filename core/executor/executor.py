"""ETHAN Executor — Task execution and management"""

import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Task:
    """A task to be executed"""
    id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    capability: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed, cancelled
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    status: str  # completed, failed, cancelled, timeout
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class Executor:
    """Task executor with retry and timeout support"""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        
    async def start(self) -> None:
        """Start the executor"""
        self._running = True
        
    async def stop(self) -> None:
        """Stop the executor"""
        self._running = False
        
    def register_handler(self, capability: str, handler: Callable) -> None:
        """Register a handler for a capability"""
        self._handlers[capability] = handler
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute a task with retry and timeout"""
        self._tasks[task.id] = task
        task.status = "running"
        task.started_at = time.time()
        
        # Check dependencies
        for dep_id in task.depends_on:
            if dep_id in self._tasks:
                dep = self._tasks[dep_id]
                if dep.status != "completed":
                    return TaskResult(
                        task_id=task.id,
                        status="failed",
                        error=f"Dependency {dep_id} not completed (status: {dep.status})"
                    )
        
        # Execute with retry
        for attempt in range(task.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._execute_task(task),
                    timeout=task.timeout
                )
                task.status = "completed"
                task.completed_at = time.time()
                return result
                
            except asyncio.TimeoutError:
                task.retry_count += 1
                if attempt < task.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                task.status = "timeout"
                task.completed_at = time.time()
                return TaskResult(
                    task_id=task.id,
                    status="timeout",
                    error=f"Task timed out after {task.timeout}s"
                )
                
            except Exception as e:
                task.retry_count += 1
                if attempt < task.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                task.status = "failed"
                task.completed_at = time.time()
                return TaskResult(
                    task_id=task.id,
                    status="failed",
                    error=str(e)
                )
        
        return TaskResult(
            task_id=task.id,
            status="failed",
            error="Max retries exceeded"
        )
    
    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute a single task"""
        handler = self._handlers.get(task.capability)
        if not handler:
            return TaskResult(
                task_id=task.id,
                status="failed",
                error=f"No handler for capability: {task.capability}"
            )
        
        result = await handler(task.params)
        
        return TaskResult(
            task_id=task.id,
            status="completed",
            data=result,
            duration_ms=(time.time() - task.started_at) * 1000 if task.started_at else 0
        )
    
    async def execute_parallel(self, tasks: List[Task]) -> List[TaskResult]:
        """Execute tasks in parallel"""
        results = await asyncio.gather(
            *[self.execute(task) for task in tasks],
            return_exceptions=True
        )
        
        task_results = []
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                task_results.append(TaskResult(
                    task_id=task.id,
                    status="failed",
                    error=str(result)
                ))
            else:
                task_results.append(result)
        
        return task_results
    
    def cancel(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id in self._tasks:
            self._tasks[task_id].status = "cancelled"
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self._tasks.get(task_id)
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks by status"""
        return [t for t in self._tasks.values() if t.status == status]
    
    @property
    def active_tasks(self) -> List[Task]:
        return self.get_tasks_by_status("running")
    
    @property
    def pending_tasks(self) -> List[Task]:
        return self.get_tasks_by_status("pending")
    
    @property
    def completed_tasks(self) -> List[Task]:
        return self.get_tasks_by_status("completed")
    
    @property
    def failed_tasks(self) -> List[Task]:
        return [t for t in self._tasks.values() if t.status in ("failed", "timeout")]
    
    @property
    def count(self) -> int:
        return len(self._tasks)