import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from src.brain.llm import QwenLLM, LLMResponse
from config.settings import settings


@dataclass
class WazaSkill:
    name: str
    description: str
    instructions: str
    enabled: bool


@dataclass
class WazaSkillRequest:
    skill: str
    input: str
    context: Optional[Dict[str, Any]] = None


class WazaSkillsManager:
    def __init__(self, llm: QwenLLM, skills_path: Optional[str] = None):
        self.llm = llm
        self.skills_path = skills_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "waza-skills",
        )
        self.skills: Dict[str, WazaSkill] = {}
        self._load_skills()

    def _load_skills(self):
        default_skills = [
            "think",
            "write",
            "design",
            "hunt",
            "learn",
            "read",
            "check",
            "health",
        ]

        for skill_name in default_skills:
            skill_path = os.path.join(self.skills_path, f"{skill_name}.md")

            instructions = ""
            if os.path.exists(skill_path):
                with open(skill_path, "r", encoding="utf-8") as f:
                    instructions = f.read()
            else:
                instructions = self._get_default_skill_instructions(skill_name)

            env_var = f"WAZA_{skill_name.upper()}_ENABLED"
            enabled = getattr(settings, env_var, True)

            self.skills[skill_name] = WazaSkill(
                name=skill_name,
                description=self._get_skill_description(skill_name),
                instructions=instructions,
                enabled=enabled,
            )

    def _get_skill_description(self, skill: str) -> str:
        descriptions = {
            "think": "Deep analysis and systematic problem-solving",
            "write": "Clear technical writing and documentation",
            "design": "System architecture and UI/UX design planning",
            "hunt": "Research and information gathering",
            "learn": "Learning and knowledge synthesis",
            "read": "Content analysis and extraction",
            "check": "Code review and quality assurance",
            "health": "System diagnostics and optimization",
        }
        return descriptions.get(skill, "")

    def _get_default_skill_instructions(self, skill: str) -> str:
        skill_instructions = {
            "think": """# THINK Skill

When activated, follow this workflow:

1. **Deconstruct the Problem**
   - What is being asked?
   - What are the key components?
   - What assumptions are being made?

2. **Analyze Systematically**
   - Break into smaller parts
   - Examine each component
   - Identify relationships and dependencies

3. **Consider Alternatives**
   - What are different approaches?
   - What are trade-offs?
   - What could go wrong?

4. **Synthesize Solution**
   - Combine insights
   - Form clear recommendations
   - Provide actionable next steps

Always explain your reasoning process.""",
            "write": """# WRITE Skill

When activated, follow this workflow:

1. **Understand the Audience**
   - Who will read this?
   - What is their knowledge level?
   - What do they need to know?

2. **Structure the Content**
   - Clear introduction
   - Logical flow of ideas
   - Examples and demonstrations
   - Summary and next steps

3. **Write Clearly**
   - Use simple language
   - Active voice
   - Concrete examples
   - Consistent formatting

4. **Review and Refine**
   - Check for clarity
   - Remove jargon
   - Verify accuracy
   - Ensure completeness""",
            "design": """# DESIGN Skill

When activated, follow this workflow:

1. **Define Requirements**
   - What problem are we solving?
   - Who are the users?
   - What are constraints?
   - What are success criteria?

2. **Architecture Design**
   - High-level system overview
   - Component breakdown
   - Data flow
   - Integration points

3. **Detailed Design**
   - API specifications
   - Database schema
   - UI/UX wireframes
   - Security considerations

4. **Implementation Plan**
   - Development phases
   - Technology choices
   - Testing strategy
   - Deployment approach

Include diagrams when helpful (use ASCII or describe).""",
            "hunt": """# HUNT Skill

When activated, follow this workflow:

1. **Research Planning**
   - What information is needed?
   - What are key questions to answer?
   - Where should we look?

2. **Information Gathering**
   - Search for relevant sources
   - Identify patterns and trends
   - Note contradictions or gaps
   - Verify credibility

3. **Synthesis**
   - Organize findings logically
   - Highlight key insights
   - Connect related information
   - Identify implications

4. **Report**
   - Executive summary
   - Detailed findings
   - Sources and references
   - Recommendations

Always cite sources and note confidence levels.""",
            "learn": """# LEARN Skill

When activated, follow this workflow:

1. **Foundation**
   - Define key terms
   - Explain core concepts
   - Provide context and history
   - Show why it matters

2. **Deep Dive**
   - How it works
   - Key principles
   - Common patterns
   - Real-world examples

3. **Connections**
   - Related concepts
   - Prerequisites
   - Applications
   - Ecosystem

4. **Mastery Path**
   - Common pitfalls
   - Best practices
   - Advanced topics
   - Learning resources

Teach progressively from basics to advanced.""",
            "read": """# READ Skill

When activated, follow this workflow:

1. **Overview**
   - What is this about?
   - Who created it?
   - When was it created?
   - What's the purpose?

2. **Content Analysis**
   - Main ideas
   - Supporting arguments
   - Key data points
   - Notable quotes

3. **Critical Evaluation**
   - Strengths
   - Weaknesses
   - Biases
   - Gaps

4. **Actionable Insights**
   - Key takeaways
   - Practical applications
   - Further reading
   - Questions to explore

Provide structured summary with key points.""",
            "check": """# CHECK Skill

When activated, follow this workflow:

1. **Code Quality**
   - Readability
   - Naming conventions
   - Code organization
   - Documentation

2. **Correctness**
   - Logic errors
   - Edge cases
   - Error handling
   - Input validation

3. **Performance**
   - Time complexity
   - Space complexity
   - Bottlenecks
   - Optimization opportunities

4. **Security**
   - Vulnerabilities
   - Input sanitization
   - Authentication/authorization
   - Data protection

5. **Recommendations**
   - Critical fixes needed
   - Improvements suggested
   - Best practices
   - Refactoring opportunities

Provide specific examples and improved code when possible.""",
            "health": """# HEALTH Skill

When activated, follow this workflow:

1. **System Overview**
   - Current status
   - Resource utilization
   - Performance metrics
   - Error rates

2. **Diagnostics**
   - Check logs
   - Monitor metrics
   - Identify anomalies
   - Trace issues

3. **Optimization**
   - Performance tuning
   - Resource allocation
   - Configuration review
   - Bottleneck resolution

4. **Recommendations**
   - Immediate actions
   - Short-term improvements
   - Long-term strategy
   - Monitoring setup

Provide clear status report with actionable items.""",
        }

        return skill_instructions.get(skill, f"# {skill.upper()} Skill\n\nExecute the {skill} workflow systematically.")

    async def execute_skill(self, request: WazaSkillRequest) -> LLMResponse:
        skill = self.skills.get(request.skill)

        if not skill:
            raise ValueError(f"Skill not found: {request.skill}")

        if not skill.enabled:
            raise ValueError(f"Skill is disabled: {request.skill}")

        # Build prompt with skill instructions
        context_str = ""
        if request.context:
            import json
            context_str = f"\n## Context:\n```json\n{json.dumps(request.context, indent=2)}\n```"

        skill_prompt = f"""# Execute {skill.name.upper()} Skill

## Instructions:
{skill.instructions}

## User Request:
{request.input}
{context_str}

Provide a comprehensive response following the {skill.name} methodology."""

        return await self.llm.query(skill_prompt)

    async def think(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="think", input=input, context=context))

    async def write(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="write", input=input, context=context))

    async def design(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="design", input=input, context=context))

    async def hunt(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="hunt", input=input, context=context))

    async def learn(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="learn", input=input, context=context))

    async def read(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="read", input=input, context=context))

    async def check(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="check", input=input, context=context))

    async def health(self, input: str, context: Optional[Dict[str, Any]] = None) -> LLMResponse:
        return await self.execute_skill(WazaSkillRequest(skill="health", input=input, context=context))

    def get_available_skills(self) -> List[str]:
        return [name for name, skill in self.skills.items() if skill.enabled]

    def get_skill_info(self, skill_name: str) -> Optional[WazaSkill]:
        return self.skills.get(skill_name)

    def list_skills(self) -> List[WazaSkill]:
        return list(self.skills.values())
