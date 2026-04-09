"""Specialist Agent - Skill-based specialist worker"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from src.agents.base_agent import BaseAgent, AgentStatus
from src.agents.message_bus import MessageBus, Message, MessageType
from src.brain.llm import QwenLLM, LLMResponse
from src.brain.waza_skills import WazaSkill, WazaSkillRequest


# Skill-specific system prompts
SKILL_SYSTEM_PROMPTS = {
    "think": """You are the Think agent - a deep analyst and systematic problem-solver.
When given a task, you:
1. Deconstruct the problem into components
2. Challenge assumptions and identify edge cases
3. Consider alternative approaches
4. Provide structured reasoning with clear conclusions
Always be thorough but concise.""",

    "write": """You are the Write agent - a technical writer and documentation expert.
When given a task, you:
1. Understand the audience and purpose
2. Structure content logically
3. Use clear, simple language
4. Include examples and actionable steps
Always produce publication-quality content.""",

    "design": """You are the Design agent - a system architect and UI/UX expert.
When given a task, you:
1. Define requirements and constraints
2. Create architecture diagrams (ASCII) or clear descriptions
3. Explain trade-offs and alternatives
4. Provide implementation roadmaps
Always think in terms of scalability and maintainability.""",

    "hunt": """You are the Hunt agent - a researcher and information gatherer.
When given a task, you:
1. Identify key questions to answer
2. Systematically gather relevant information
3. Synthesize findings from multiple angles
4. Provide sourced, credible conclusions
Always note confidence levels and cite reasoning.""",

    "learn": """You are the Learn agent - a teacher and knowledge synthesizer.
When given a task, you:
1. Start from fundamentals
2. Build up complexity progressively
3. Use concrete examples and analogies
4. Suggest next steps and resources
Always teach, don't just inform.""",

    "read": """You are the Read agent - a content analyst and extractor.
When given content to analyze, you:
1. Identify main ideas and supporting arguments
2. Extract key data points and insights
3. Evaluate strengths, weaknesses, and biases
4. Provide structured summaries
Always be objective and thorough.""",

    "check": """You are the Check agent - a code reviewer and QA specialist.
When given code or a plan to review, you:
1. Check for correctness and edge cases
2. Identify security vulnerabilities
3. Suggest performance improvements
4. Recommend best practices
Always provide specific examples and fixes.""",

    "health": """You are the Health agent - a system diagnostics and optimization expert.
When given a system to analyze, you:
1. Assess current status and health
2. Identify anomalies and potential issues
3. Suggest optimizations and improvements
4. Provide actionable recommendations
Always prioritize critical issues first.""",
}

SKILL_DESCRIPTIONS = {
    "think": "Deep analysis and systematic problem-solving",
    "write": "Technical writing and documentation",
    "design": "System architecture and UI/UX design",
    "hunt": "Research and information gathering",
    "learn": "Teaching and knowledge synthesis",
    "read": "Content analysis and extraction",
    "check": "Code review and quality assurance",
    "health": "System diagnostics and optimization",
}


class SpecialistAgent(BaseAgent):
    """A specialist agent that owns a specific skill/domain"""

    def __init__(
        self,
        skill_name: str,
        message_bus: MessageBus,
        llm: QwenLLM,
        skill_info: Optional[WazaSkill] = None,
    ):
        self.skill_name = skill_name
        self.llm = llm
        self.skill_info = skill_info

        system_prompt = SKILL_SYSTEM_PROMPTS.get(skill_name, "")

        super().__init__(
            name=f"{skill_name.capitalize()} Agent",
            role=skill_name,
            message_bus=message_bus,
            model=llm.model,
            system_prompt=system_prompt,
        )

    def _default_system_prompt(self) -> str:
        return SKILL_SYSTEM_PROMPTS.get(self.skill_name, super()._default_system_prompt())

    async def _handle_task_assign(self, message: Message):
        """Override to execute the task using the LLM"""
        await super()._handle_task_assign(message)

        task_description = message.content
        context = message.metadata.get("context", "")

        # Build the prompt
        prompt = self._build_task_prompt(task_description, context)

        try:
            await self.report_progress(10.0, f"Starting {self.skill_name} analysis...")

            # Query the LLM
            response = await self.llm.query(prompt)

            await self.report_progress(80.0, f"Completed analysis, structuring response...")

            # Report completion
            await self.report_completion(response.content)

        except Exception as e:
            await self.report_failure(f"Error executing {self.skill_name} task: {str(e)}")

    def _build_task_prompt(self, task_description: str, context: str = "") -> str:
        """Build a prompt incorporating skill instructions and task context"""
        skill_instructions = ""
        if self.skill_info and self.skill_info.instructions:
            skill_instructions = self.skill_info.instructions

        context_section = f"\n## Context:\n{context}" if context else ""

        return f"""# {self.skill_name.upper()} Task

## Your Role:
{self.system_prompt}

## Skill Instructions:
{skill_instructions}

## Task:{task_description}
{context_section}

Execute this task following the {self.skill_name} methodology.
Provide a comprehensive, structured response."""

    async def execute_direct(self, task_description: str, context: str = "") -> str:
        """Execute a task directly and return result (for non-orchestrated use)"""
        prompt = self._build_task_prompt(task_description, context)
        response = await self.llm.query(prompt)
        return response.content

    def get_status(self) -> Dict[str, Any]:
        """Get status with skill-specific info"""
        status = super().get_status()
        status["skill"] = self.skill_name
        status["skill_description"] = SKILL_DESCRIPTIONS.get(self.skill_name, "")
        return status
