import httpx
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

from config.settings import settings


class Message(BaseModel):
    role: str
    content: str


class TokenUsage(BaseModel):
    input: int
    output: int


class LLMResponse(BaseModel):
    id: str
    content: str
    tokens: TokenUsage
    model: str
    timestamp: datetime


class QwenLLM:
    def __init__(
        self,
        api_type: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.api_type = api_type or settings.QWEN_API_TYPE
        self.api_key = api_key or settings.QWEN_API_KEY
        self.base_url = base_url or (
            settings.QWEN_BASE_URL
            if self.api_type == "dashscope"
            else settings.OLLAMA_BASE_URL
        )
        self.model = model or (
            settings.QWEN_MODEL
            if self.api_type == "dashscope"
            else settings.OLLAMA_MODEL
        )
        self.temperature = temperature if temperature is not None else settings.TEMPERATURE
        self.top_p = top_p if top_p is not None else settings.TOP_P
        self.max_tokens = max_tokens if max_tokens is not None else settings.MAX_TOKENS
        
        self.conversation_history: List[Message] = []
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """You are Jarvis, a sophisticated AI assistant with engineering expertise.

IMPORTANT: Always respond in English only. Never use Chinese, Japanese, or any other language.

You have access to the following skill modules:
- /think: Deep analysis and problem-solving
- /write: Clear technical writing and documentation
- /design: System architecture and UI/UX design
- /hunt: Research and information gathering
- /learn: Learning and knowledge synthesis
- /read: Content analysis and extraction
- /check: Code review and quality assurance
- /health: System diagnostics and optimization

When asked a question, you can:
1. Use these skills to provide comprehensive responses
2. Break down complex problems systematically
3. Provide actionable solutions with clear reasoning
4. Always explain your approach and thinking process

Be helpful, precise, and thoughtful in your responses."""

    async def query(self, user_message: str, use_waza_skills: bool = True) -> LLMResponse:
        try:
            # Add user message to history
            self.conversation_history.append(Message(role="user", content=user_message))

            # Prepare request
            messages = [
                Message(role="system", content=self.system_prompt),
                *self.conversation_history,
            ]

            response = await self._call_llm(messages)

            # Add assistant response to history
            self.conversation_history.append(
                Message(role="assistant", content=response.content)
            )

            return response
        except Exception as e:
            print(f"LLM Query Error: {e}")
            raise e

    async def _call_llm(self, messages: List[Message]) -> LLMResponse:
        request_id = str(uuid.uuid4())

        if self.api_type == "dashscope":
            return await self._call_dashscope(messages, request_id)
        elif self.api_type == "ollama":
            return await self._call_ollama(messages, request_id)
        else:
            raise ValueError(f"Unsupported API type: {self.api_type}")

    async def _call_dashscope(self, messages: List[Message], request_id: str) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return LLMResponse(
            id=request_id,
            content=data["choices"][0]["message"]["content"],
            tokens=TokenUsage(
                input=data.get("usage", {}).get("prompt_tokens", 0),
                output=data.get("usage", {}).get("completion_tokens", 0),
            ),
            model=self.model,
            timestamp=datetime.now(),
        )

    async def _call_ollama(self, messages: List[Message], request_id: str) -> LLMResponse:
        # Use native Ollama API endpoint (/api/chat) for better control
        payload = {
            "model": self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": False,
            "keep_alive": "5m",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url.replace('/v1', '')}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return LLMResponse(
            id=request_id,
            content=data.get("message", {}).get("content", "No response"),
            tokens=TokenUsage(input=0, output=0),
            model=self.model,
            timestamp=datetime.now(),
        )

    async def query_with_skill(self, user_message: str, skill: str) -> LLMResponse:
        skill_prompt = self._get_skill_prompt(skill)
        enhanced_message = f"{user_message}\n\n[Using {skill} skill]\n{skill_prompt}"
        return await self.query(enhanced_message)

    def _get_skill_prompt(self, skill: str) -> str:
        skill_prompts = {
            "think": """Analyze this deeply. Break it down systematically.
- Challenge assumptions
- Consider edge cases
- Pressure-test the logic
- Provide clear reasoning""",
            "write": """Write clear, concise documentation or explanation.
- Use simple language
- Structure clearly
- Include examples
- Be specific and actionable""",
            "design": """Design a solution with clear architecture.
- Define the problem
- Sketch the design
- Explain trade-offs
- Provide implementation path""",
            "hunt": """Research and gather information thoroughly.
- Find relevant sources
- Summarize key findings
- Identify patterns
- Note important details""",
            "learn": """Teach me about this topic systematically.
- Explain the fundamentals
- Provide context and examples
- Show how it connects to other concepts
- Suggest next steps""",
            "read": """Analyze and extract key information.
- Summarize the content
- Extract main ideas
- Note important details
- Provide actionable insights""",
            "check": """Review and provide quality assurance.
- Check for correctness
- Suggest improvements
- Identify potential issues
- Provide constructive feedback""",
            "health": """Diagnose and optimize the system.
- Identify issues
- Check configuration
- Suggest optimizations
- Provide health status""",
        }
        return skill_prompts.get(skill, "")

    def clear_history(self):
        self.conversation_history = []

    def get_history(self) -> List[Message]:
        return self.conversation_history.copy()

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt
