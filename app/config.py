"""환경 변수(.env)를 읽어 설정 객체 하나로 모아 두는 곳."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-4-argon")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-6-luna")

    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'bluearchive_chat.db'}")
    token_days: int = int(os.getenv("TOKEN_DAYS", "14"))
    summary_trigger: int = int(os.getenv("SUMMARY_TRIGGER", "30"))
    keep_recent: int = int(os.getenv("KEEP_RECENT", "12"))

    data_dir: Path = ROOT / "data"
    frontend_dir: Path = ROOT / "frontend"


settings = Settings()
