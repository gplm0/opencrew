"""Orchestrator - Main entry point for multi-agent mode"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from config.settings import settings
from src.agents.message_bus import MessageBus, Message, MessageType
from src.agents.base_agent import BaseAgent, AgentStatus
from src.agents.specialist_agent import SpecialistAgent, SKILL_DESCRIPTIONS
from src.agents.supervisor import SupervisorAgent
from src.agents.registry import AgentRegistry
from src.brain.llm import QwenLLM
from src.brain.waza_skills import WazaSkillsManager


class Orchestrator:
    """Main orchestrator - sets up and runs the multi-agent crew"""

    def __init__(self, llm: Optional[QwenLLM] = None):
        self.llm = llm or QwenLLM(
            api_type=settings.QWEN_API_TYPE,
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.TEMPERATURE,
            top_p=settings.TOP_P,
            max_tokens=settings.MAX_TOKENS,
        )

        self.message_bus = MessageBus()
        self.registry = AgentRegistry()
        self.supervisor: Optional[SupervisorAgent] = None
        self.specialists: Dict[str, SpecialistAgent] = {}
        self._running = False
        self._progress_callbacks: List[Callable] = []
        self._initialized = False

    async def initialize(self, skills: Optional[List[str]] = None):
        """Initialize all agents"""
        if self._initialized:
            return

        # Create supervisor
        self.supervisor = SupervisorAgent(
            message_bus=self.message_bus,
            llm=self.llm,
            registry=self.registry,
        )
        await self.supervisor.initialize()
        await self.registry.register(self.supervisor)

        # Create specialist agents
        skill_list = skills or ["think", "write", "design", "hunt", "learn", "read", "check", "health"]

        for skill_name in skill_list:
            specialist = SpecialistAgent(
                skill_name=skill_name,
                message_bus=self.message_bus,
                llm=self.llm,
            )
            await specialist.initialize()
            await self.registry.register(specialist)
            self.specialists[skill_name] = specialist

        self._initialized = True
        self._running = True

    def on_progress(self, callback: Callable):
        """Register a callback for progress updates"""
        self._progress_callbacks.append(callback)

    async def run(self, task: str, stream: bool = False) -> str:
        """Run a task through the multi-agent crew

        Args:
            task: The task description
            stream: If True, yield progress updates

        Returns:
            The final consolidated result
        """
        if not self._initialized:
            await self.initialize()

        # Phase 1: Planning
        if stream:
            await self._emit_progress("🧠 Supervisor analyzing task...", "planning")

        plan = await self.supervisor.plan_task(task)

        if stream:
            await self._emit_progress(f"📋 Plan: {plan.reasoning}", "plan")
            await self._emit_progress(
                f"📊 {len(plan.subtasks)} subtasks in {len(plan.execution_order)} phases",
                "plan"
            )

        # Phase 2: Execution
        if stream:
            await self._emit_progress("⚡ Executing plan...", "execution")

        result = await self.supervisor.execute_plan(plan)

        if stream:
            await self._emit_progress("✅ Task complete!", "complete")

        return result

    async def get_vision(self) -> Dict[str, Any]:
        """Get a vision/dashboard of current crew state"""
        if not self._initialized:
            await self.initialize()

        vision = await self.supervisor.generate_vision()

        # Add agent details
        agent_details = []
        for record in self.registry.list_all():
            agent_details.append({
                "name": record.name,
                "role": record.role,
                "status": record.agent.status.value,
                "current_task": record.agent.current_task.description if record.agent.current_task else "Idle",
                "progress": record.agent.current_task.progress if record.agent.current_task else 0,
            })

        vision["agent_details"] = agent_details

        # Add task board
        vision["task_board"] = []
        for task in self.supervisor.task_board.get_all_tasks():
            vision["task_board"].append({
                "task_id": task.task_id,
                "description": task.description[:80],
                "agent": task.assigned_agent,
                "status": task.status,
                "progress": task.progress,
            })

        return vision

    async def get_status(self) -> Dict[str, Any]:
        """Get crew status"""
        if not self._initialized:
            return {"status": "not_initialized"}

        return {
            "running": self._running,
            "supervisor": self.supervisor.get_status(),
            "specialists": {
                name: agent.get_status()
                for name, agent in self.specialists.items()
            },
            "registry_summary": self.registry.summary(),
        }

    async def shutdown(self):
        """Shutdown all agents"""
        self._running = False

        if self.supervisor:
            await self.supervisor.shutdown()

        for specialist in self.specialists.values():
            await specialist.shutdown()

        await self.message_bus.clear()

    async def _emit_progress(self, message: str, stage: str = "info"):
        """Emit progress update to callbacks"""
        update = {
            "message": message,
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
        }
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception:
                pass
