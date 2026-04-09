"""Agent Registry and State Management"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.agents.base_agent import BaseAgent, AgentStatus
from src.agents.message_bus import MessageBus


@dataclass
class AgentRecord:
    """Registry record for an agent"""
    agent_id: str
    name: str
    role: str
    agent: BaseAgent
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    is_healthy: bool = True


class AgentRegistry:
    """Registry of all active agents with health monitoring"""

    def __init__(self):
        self._agents: Dict[str, AgentRecord] = {}

    async def register(self, agent: BaseAgent):
        """Register an agent"""
        record = AgentRecord(
            agent_id=agent.identity.agent_id,
            name=agent.identity.name,
            role=agent.identity.role,
            agent=agent,
        )
        self._agents[agent.identity.agent_id] = record

    async def unregister(self, agent_id: str):
        """Unregister an agent"""
        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        record = self._agents.get(agent_id)
        return record.agent if record else None

    def get_by_role(self, role: str) -> Optional[BaseAgent]:
        """Get agent by role"""
        for record in self._agents.values():
            if record.role == role:
                return record.agent
        return None

    def get_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        for record in self._agents.values():
            if record.name == name:
                return record.agent
        return None

    def list_all(self) -> List[AgentRecord]:
        """List all registered agents"""
        return list(self._agents.values())

    def get_active_agents(self) -> List[BaseAgent]:
        """Get all active (non-offline) agents"""
        return [
            record.agent for record in self._agents.values()
            if record.agent.status != AgentStatus.OFFLINE
        ]

    def update_heartbeat(self, agent_id: str):
        """Update heartbeat timestamp for health monitoring"""
        if agent_id in self._agents:
            self._agents[agent_id].last_heartbeat = datetime.now()

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        return [record.agent.get_status() for record in self._agents.values()]

    def summary(self) -> Dict[str, Any]:
        """Get registry summary"""
        statuses = {}
        for record in self._agents.values():
            status = record.agent.status.value
            statuses[status] = statuses.get(status, 0) + 1

        return {
            "total_agents": len(self._agents),
            "by_status": statuses,
            "healthy": sum(1 for r in self._agents.values() if r.is_healthy),
        }


@dataclass
class TaskRecord:
    """Record of a task in the task board"""
    task_id: str
    description: str
    assigned_agent: str
    assigned_agent_name: str
    status: str
    progress: float
    assigned_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


class TaskBoard:
    """Kanban-style task board for tracking all crew tasks"""

    def __init__(self):
        self._tasks: Dict[str, TaskRecord] = {}

    def add_task(self, task_id: str, description: str, agent_id: str,
                 agent_name: str, status: str = "pending") -> TaskRecord:
        task = TaskRecord(
            task_id=task_id,
            description=description,
            assigned_agent=agent_id,
            assigned_agent_name=agent_name,
            status=status,
            progress=0.0,
            assigned_at=datetime.now(),
        )
        self._tasks[task_id] = task
        return task

    def update_task(self, task_id: str, **kwargs):
        """Update task fields"""
        if task_id in self._tasks:
            for key, value in kwargs.items():
                if hasattr(self._tasks[task_id], key):
                    setattr(self._tasks[task_id], key, value)

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return self._tasks.get(task_id)

    def get_tasks_by_status(self, status: str) -> List[TaskRecord]:
        return [t for t in self._tasks.values() if t.status == status]

    def get_all_tasks(self) -> List[TaskRecord]:
        return list(self._tasks.values())

    def get_active_tasks(self) -> List[TaskRecord]:
        return [t for t in self._tasks.values() if t.status in ("working", "pending", "blocked")]

    def get_completed_tasks(self) -> List[TaskRecord]:
        return [t for t in self._tasks.values() if t.status == "completed"]

    def clear(self):
        """Clear all tasks"""
        self._tasks.clear()

    def summary(self) -> Dict[str, Any]:
        """Get task board summary"""
        by_status = {}
        for task in self._tasks.values():
            by_status[task.status] = by_status.get(task.status, 0) + 1

        return {
            "total_tasks": len(self._tasks),
            "by_status": by_status,
            "active": len(self.get_active_tasks()),
            "completed": len(self.get_completed_tasks()),
        }
