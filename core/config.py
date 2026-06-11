"""
core/config.py - Central configuration management
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

class Config:
    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # ── OpenRouter + Video Studio ──────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    VIDEO_STUDIO_MODEL: str = os.getenv("VIDEO_STUDIO_MODEL", "deepseek/deepseek-r1-0528:free")
    VIDEO_STUDIO_MAX_TOKENS: int = int(os.getenv("VIDEO_STUDIO_MAX_TOKENS", "4096"))
    VIDEO_STUDIO_TEMPERATURE: float = float(os.getenv("VIDEO_STUDIO_TEMPERATURE", "0.75"))
    VIDEO_PROJECTS_DIR: "Path" = BASE_DIR / os.getenv("VIDEO_PROJECTS_DIR", "projects/video")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # ── OpenRouter (Video Studio) ──────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ── Video Studio ───────────────────────────────────────────────────────
    VIDEO_STUDIO_MODEL: str = os.getenv("VIDEO_STUDIO_MODEL", "deepseek/deepseek-r1-0528:free")
    VIDEO_STUDIO_MAX_TOKENS: int = int(os.getenv("VIDEO_STUDIO_MAX_TOKENS", "4096"))
    VIDEO_STUDIO_TEMPERATURE: float = float(os.getenv("VIDEO_STUDIO_TEMPERATURE", "0.75"))
    VIDEO_PROJECTS_DIR = BASE_DIR / os.getenv("VIDEO_PROJECTS_DIR", "projects/video")

    # ── API Server ─────────────────────────────────────────────────────────
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Loop limits
    MAX_REPAIR_ITERATIONS: int = int(os.getenv("MAX_REPAIR_ITERATIONS", "5"))
    MAX_BUILD_ITERATIONS: int = int(os.getenv("MAX_BUILD_ITERATIONS", "10"))
    EXECUTION_TIMEOUT: int = int(os.getenv("EXECUTION_TIMEOUT", "30"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Memory
    MEMORY_BACKEND: str = os.getenv("MEMORY_BACKEND", "sqlite")
    CHROMA_PERSIST_DIR: Path = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "memory/chroma_db")
    SQLITE_PATH: Path = BASE_DIR / os.getenv("SQLITE_PATH", "memory/agentjw.db")

    # Sandbox / Projects
    SANDBOX_DIR: Path = BASE_DIR / os.getenv("SANDBOX_DIR", "runtime/sandbox")
    PROJECTS_DIR: Path = BASE_DIR / os.getenv("PROJECTS_DIR", "projects")

    @classmethod
    def ensure_dirs(cls):
        for d in [cls.LOGS_DIR, cls.CHROMA_PERSIST_DIR, cls.SQLITE_PATH.parent,
                  cls.SANDBOX_DIR, cls.PROJECTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_llm_key(cls) -> str:
        if cls.LLM_PROVIDER == "anthropic":
            return cls.ANTHROPIC_API_KEY
        return cls.OPENAI_API_KEY

    @classmethod
    def get_model(cls) -> str:
        if cls.LLM_PROVIDER == "anthropic":
            return cls.ANTHROPIC_MODEL
        return cls.OPENAI_MODEL


    @classmethod
    def has_openrouter(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)

    @classmethod
    def has_video_studio(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)


    @classmethod
    def has_openrouter(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)

    @classmethod
    def has_video_studio(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)


config = Config()
