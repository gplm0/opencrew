"""Supervisor Agent - Task decomposition and orchestration"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentStatus
from src.agents.message_bus import MessageBus, Message, MessageType
from src.agents.registry import AgentRegistry, TaskBoard
from src.brain.llm import QwenLLM


@dataclass
class SubTask:
    """A subtask decomposed from the main task"""
    skill: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    task_id: str = ""


@dataclass
class TaskPlan:
    """A plan for executing a task"""
    original_task: str
    subtasks: List[SubTask] = field(default_factory=list)
    execution_order: List[List[str]] = field(default_factory=list)  # Groups of parallel tasks
    reasoning: str = ""


class SupervisorAgent(BaseAgent):
    """The supervisor that decomposes tasks and orchestrates specialist agents"""

    def __init__(self, message_bus: MessageBus, llm: QwenLLM, registry: AgentRegistry):
        self.llm = llm
        self.registry = registry
        self.task_board = TaskBoard()
        self.current_plan: Optional[TaskPlan] = None
        self.completed_results: Dict[str, str] = {}

        system_prompt = """You are the Supervisor agent - the orchestrator of a multi-agent crew.
Your responsibilities:
1. Decompose complex tasks into subtasks for specialist agents
2. Assign subtasks to the appropriate specialists
3. Monitor progress and resolve blockers
4. Consolidate results into a comprehensive final response

Available specialist skills: think, write, design, hunt, learn, read, check, health

When decomposing tasks:
- Identify which skills are needed
- Determine dependencies (what must be done first)
- Group independent tasks for parallel execution
- Be specific in task descriptions
- Always think about the logical flow of work

Always respond in English only. Be strategic and decisive."""

        super().__init__(
            name="Supervisor",
            role="supervisor",
            message_bus=message_bus,
            model=llm.model,
            system_prompt=system_prompt,
        )

    async def plan_task(self, task_description: str) -> TaskPlan:
        """Decompose a task into a plan with subtasks"""
        available_skills = self._get_available_skills()

        planning_prompt = f"""You are planning a multi-agent execution for this task:

TASK: {task_description}

Available specialist skills: {', '.join(available_skills)}

Decompose this task into subtasks. For each subtask, specify:
1. Which skill should handle it
2. A clear, specific description of what to do
3. What other subtasks it depends on (if any)

Think about the logical order of work. Some tasks can run in parallel, others must be sequential.

Respond ONLY with a JSON object in this exact format:
```json
{{
  "reasoning": "Brief explanation of your approach",
  "subtasks": [
    {{
      "skill": "skill_name",
      "description": "What this agent should do",
      "dependencies": []  // list of subtask indices this depends on (empty if independent)
    }}
  ],
  "execution_order": [[0, 1], [2, 3]]  // groups of subtask indices that can run in parallel
}}
```

Keep subtask descriptions specific and actionable. Use the minimum number of subtasks needed."""

        response = await self.llm.query(planning_prompt)

        # Parse the plan from response
        raw_plan = self._parse_plan(response.content)

        # Convert dict subtasks to SubTask objects
        subtasks = []
        for st in raw_plan.get("subtasks", []):
            subtasks.append(SubTask(
                skill=st.get("skill", "think"),
                description=st.get("description", ""),
                dependencies=st.get("dependencies", []),
            ))

        plan = TaskPlan(
            original_task=task_description,
            subtasks=subtasks,
            execution_order=raw_plan.get("execution_order", []),
            reasoning=raw_plan.get("reasoning", ""),
        )
        self.current_plan = plan

        return self.current_plan

    def _parse_plan(self, response: str) -> Dict[str, Any]:
        """Extract JSON plan from LLM response"""
        # Try to find JSON in code block or raw
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.index("```") + 3
            end = response.index("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: create a simple plan with think skill
            return {
                "reasoning": "Could not parse structured plan, using default approach",
                "subtasks": [
                    {
                        "skill": "think",
                        "description": response[:500],
                        "dependencies": []
                    }
                ],
                "execution_order": [[0]]
            }

    async def execute_plan(self, plan: TaskPlan) -> str:
        """Execute a plan by assigning tasks to specialist agents"""
        self.completed_results.clear()
        self.task_board.clear()

        # Broadcast plan start
        await self.message_bus.broadcast(
            sender=self.identity.agent_id,
            message_type=MessageType.SESSION_START,
            content=f"Starting execution: {plan.original_task}",
            metadata={
                "num_subtasks": len(plan.subtasks),
                "reasoning": plan.reasoning,
            },
        )

        # Execute tasks in order (respecting dependencies)
        for phase in plan.execution_order:
            phase_coroutines = []

            # Assign all tasks in this phase (they can run in parallel)
            for subtask_idx in phase:
                if subtask_idx >= len(plan.subtasks):
                    continue

                subtask = plan.subtasks[subtask_idx]
                specialist = self.registry.get_by_role(subtask.skill)

                if not specialist:
                    # Fallback: use think agent
                    specialist = self.registry.get_by_role("think")

                if specialist:
                    task_id = f"task-{subtask_idx}"
                    self.task_board.add_task(
                        task_id=task_id,
                        description=subtask.description,
                        agent_id=specialist.identity.agent_id,
                        agent_name=specialist.identity.name,
                        status="working",
                    )

                    # Execute specialist directly (await completion)
                    phase_coroutines.append((subtask_idx, task_id, specialist, subtask))

            # Run all tasks in this phase concurrently
            import asyncio
            results = await asyncio.gather(
                *[self._execute_specialist_task(specialist, subtask) for _, _, specialist, subtask in phase_coroutines],
                return_exceptions=True,
            )

            # Process results
            for (subtask_idx, task_id, _, _), result in zip(phase_coroutines, results):
                if isinstance(result, Exception):
                    self.task_board.update_task(task_id, status="failed", error=str(result))
                elif result is None:
                    self.task_board.update_task(task_id, status="failed")
                else:
                    self.completed_results[str(subtask_idx)] = result
                    self.task_board.update_task(task_id, status="completed", result=result, progress=100.0)

        # Consolidate results
        final_result = await self._consolidate_results(plan)

        await self.message_bus.broadcast(
            sender=self.identity.agent_id,
            message_type=MessageType.SESSION_END,
            content=f"Completed: {plan.original_task}",
            metadata={"result": final_result},
        )

        return final_result

    async def _execute_specialist_task(self, specialist, subtask) -> Optional[str]:
        """Execute a task on a specialist agent and wait for completion"""
        try:
            result = await specialist.execute_direct(subtask.description)
            return result
        except Exception as e:
            print(f"[Supervisor] Task failed for {specialist.identity.name}: {e}")
            return None

    async def _consolidate_results(self, plan: TaskPlan) -> str:
        """Use LLM to consolidate all subtask results into a final response"""
        if not self.completed_results:
            return "No results were produced during execution."

        consolidation_prompt = f"""You are the Supervisor agent consolidating results from a multi-agent execution.

ORIGINAL TASK: {plan.original_task}

APPROACH: {plan.reasoning}

SUBTASK RESULTS:
"""
        for idx, result in self.completed_results.items():
            subtask = plan.subtasks[int(idx)] if int(idx) < len(plan.subtasks) else None
            skill_name = subtask.skill if subtask else "unknown"
            consolidation_prompt += f"\n--- {skill_name.upper()} (Subtask {idx}) ---\n{result}\n"

        consolidation_prompt += """
Now consolidate these results into a comprehensive, well-structured response to the original task.
Synthesize the findings, resolve any contradictions, and present a coherent final answer.
Use markdown formatting for readability."""

        response = await self.llm.query(consolidation_prompt)
        return response.content

    def _get_available_skills(self) -> List[str]:
        """Get list of available specialist skills from registry"""
        skills = []
        for record in self.registry.list_all():
            if record.role not in ("supervisor",):
                skills.append(record.role)
        return skills if skills else ["think", "write", "design", "hunt", "learn", "read", "check", "health"]

    async def generate_vision(self) -> Dict[str, Any]:
        """Generate a vision/dashboard summary of current state"""
        agent_statuses = self.registry.get_all_statuses()
        task_summary = self.task_board.summary()

        vision = {
            "timestamp": datetime.now().isoformat(),
            "agents": agent_statuses,
            "tasks": task_summary,
            "plan": {
                "original_task": self.current_plan.original_task if self.current_plan else None,
                "reasoning": self.current_plan.reasoning if self.current_plan else None,
                "num_subtasks": len(self.current_plan.subtasks) if self.current_plan else 0,
            } if self.current_plan else None,
            "completed_results": len(self.completed_results),
        }

        return vision

    def get_status(self) -> Dict[str, Any]:
        """Get supervisor status"""
        status = super().get_status()
        status["task_board"] = self.task_board.summary()
        status["completed_results"] = len(self.completed_results)
        status["has_plan"] = self.current_plan is not None
        return status
