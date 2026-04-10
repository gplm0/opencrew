from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Qwen Configuration
    QWEN_API_TYPE: str = "dashscope"  # or "ollama"
    QWEN_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-plus"
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # For local Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen:7b"
    
    # Waza Skills
    WAZA_THINK_ENABLED: bool = True
    WAZA_WRITE_ENABLED: bool = True
    WAZA_DESIGN_ENABLED: bool = True
    WAZA_HUNT_ENABLED: bool = True
    WAZA_LEARN_ENABLED: bool = True
    WAZA_READ_ENABLED: bool = True
    WAZA_CHECK_ENABLED: bool = True
    WAZA_HEALTH_ENABLED: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./jarvis.db"

    # LLM Parameters
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    MAX_TOKENS: int = 2000

    # Multi-Agent Crew Configuration
    CREW_MAX_AGENTS: int = 10
    CREW_TIMEOUT_MINUTES: int = 30
    CREW_STREAM_OUTPUT: bool = True
    CREW_LOG_LEVEL: str = "info"
    CREW_DEFAULT_SKILLS: str = "think,write,design,hunt,learn,read,check,health"

    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        case_sensitive = True


settings = Settings()
