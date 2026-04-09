"""Base Agent - Core agent abstraction"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from src.agents.message_bus import MessageBus, Message, MessageType


class AgentStatus(str, Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentIdentity:
    """Agent identity information"""
    name: str
    role: str
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model: str = "qwen3.5:cloud"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentTask:
    """A task assigned to an agent"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assigned_by: str = ""
    assigned_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0-100
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """Base class for all agents in the crew"""

    def __init__(
        self,
        name: str,
        role: str,
        message_bus: MessageBus,
        model: str = "qwen3.5:cloud",
        system_prompt: str = "",
    ):
        self.identity = AgentIdentity(
            name=name,
            role=role,
            model=model,
        )
        self.message_bus = message_bus
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.status = AgentStatus.IDLE
        self.current_task: Optional[AgentTask] = None
        self.task_history: List[AgentTask] = []
        self._running = False
        self._initialized = False

    def _default_system_prompt(self) -> str:
        return f"""You are {self.identity.name}, an AI agent with role: {self.identity.role}.
You are part of a multi-agent crew working collaboratively on tasks.
Always respond in English only.
Be precise, structured, and actionable."""

    async def initialize(self):
        """Initialize the agent - register with message bus"""
        if not self._initialized:
            await self.message_bus.register_agent(self.identity.agent_id, self._handle_message)
            self._initialized = True

    async def _handle_message(self, message: Message):
        """Handle incoming messages - override in subclasses"""
        if message.type == MessageType.STATUS_REQUEST:
            await self._handle_status_request(message)
        elif message.type == MessageType.TASK_ASSIGN:
            await self._handle_task_assign(message)

    async def _handle_status_request(self, message: Message):
        """Respond to status inquiries"""
        status_data = {
            "agent_id": self.identity.agent_id,
            "name": self.identity.name,
            "role": self.identity.role,
            "status": self.status.value,
            "current_task": self.current_task.description if self.current_task else None,
            "progress": self.current_task.progress if self.current_task else 0,
        }
        reply = message.reply(
            MessageType.STATUS_RESPONSE,
            content="",
            metadata=status_data,
        )
        await self.message_bus.publish(reply)

    async def _handle_task_assign(self, message: Message):
        """Handle task assignment - override in subclasses"""
        task_desc = message.metadata.get("task_description", "")
        task_id = message.metadata.get("task_id", str(uuid.uuid4()))

        self.current_task = AgentTask(
            task_id=task_id,
            description=task_desc,
            assigned_by=message.sender,
            dependencies=message.metadata.get("dependencies", []),
        )
        self.status = AgentStatus.WORKING
        self.current_task.started_at = datetime.now()
        self.current_task.status = "working"

        # Acknowledge receipt
        ack = message.reply(
            MessageType.LOG,
            content=f"{self.identity.name} received task: {task_desc[:100]}",
            metadata={"task_id": task_id},
        )
        await self.message_bus.publish(ack)

    async def assign_task(self, description: str, assigned_by: str = "supervisor",
                          task_id: Optional[str] = None, dependencies: Optional[List[str]] = None):
        """Assign a task to this agent"""
        await self.message_bus.send_to(
            recipient=self.identity.agent_id,
            sender=assigned_by,
            message_type=MessageType.TASK_ASSIGN,
            content=description,
            metadata={
                "task_description": description,
                "task_id": task_id or str(uuid.uuid4()),
                "dependencies": dependencies or [],
            },
        )

    async def report_progress(self, progress: float, detail: str = ""):
        """Report progress on current task"""
        if self.current_task:
            self.current_task.progress = progress

        await self.message_bus.send_to(
            recipient="broadcast",
            sender=self.identity.agent_id,
            message_type=MessageType.PROGRESS_UPDATE,
            content=detail,
            metadata={
                "task_id": self.current_task.task_id if self.current_task else None,
                "progress": progress,
                "agent": self.identity.name,
            },
        )

    async def report_completion(self, result: str):
        """Report task completion"""
        if self.current_task:
            self.current_task.completed_at = datetime.now()
            self.current_task.progress = 100.0
            self.current_task.status = "completed"
            self.current_task.result = result
            self.task_history.append(self.current_task)

        await self.message_bus.send_to(
            recipient="broadcast",
            sender=self.identity.agent_id,
            message_type=MessageType.TASK_COMPLETE,
            content=result,
            metadata={
                "task_id": self.current_task.task_id if self.current_task else None,
                "agent": self.identity.name,
                "result": result,
            },
        )

        self.status = AgentStatus.DONE
        self.current_task = None

    async def report_blocker(self, blocker: str, needs_help_from: Optional[str] = None):
        """Report a blocker"""
        if self.current_task:
            self.current_task.status = "blocked"
            self.current_task.error = blocker

        self.status = AgentStatus.BLOCKED

        metadata = {
            "task_id": self.current_task.task_id if self.current_task else None,
            "agent": self.identity.name,
            "blocker": blocker,
        }
        if needs_help_from:
            metadata["needs_help_from"] = needs_help_from

        await self.message_bus.send_to(
            recipient="broadcast" if not needs_help_from else needs_help_from,
            sender=self.identity.agent_id,
            message_type=MessageType.BLOCKER,
            content=blocker,
            metadata=metadata,
        )

    async def report_failure(self, error: str):
        """Report a task failure"""
        if self.current_task:
            self.current_task.status = "failed"
            self.current_task.error = error
            self.current_task.completed_at = datetime.now()
            self.task_history.append(self.current_task)

        self.status = AgentStatus.ERROR

        await self.message_bus.send_to(
            recipient="broadcast",
            sender=self.identity.agent_id,
            message_type=MessageType.TASK_FAILED,
            content=error,
            metadata={
                "task_id": self.current_task.task_id if self.current_task else None,
                "agent": self.identity.name,
                "error": error,
            },
        )

        self.current_task = None

    async def shutdown(self):
        """Shutdown the agent"""
        self._running = False
        self.status = AgentStatus.OFFLINE
        await self.message_bus.unregister_agent(
            self.identity.agent_id,
            self._handle_message,
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status as dict"""
        return {
            "agent_id": self.identity.agent_id,
            "name": self.identity.name,
            "role": self.identity.role,
            "model": self.identity.model,
            "status": self.status.value,
            "current_task": self.current_task.description if self.current_task else None,
            "progress": self.current_task.progress if self.current_task else 0,
            "tasks_completed": len([t for t in self.task_history if t.status == "completed"]),
            "tasks_failed": len([t for t in self.task_history if t.status == "failed"]),
        }
