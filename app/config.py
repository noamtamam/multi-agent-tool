from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = Path(__file__).resolve().parent


def _env_files() -> tuple[str, ...]:
    """Load .env from repo root and app/ (later files override earlier)."""
    candidates = (_PROJECT_ROOT / ".env", _APP_DIR / ".env")
    return tuple(str(p) for p in candidates if p.is_file())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files() or (str(_PROJECT_ROOT / ".env"), str(_APP_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/agent.db"
    # Append-only JSONL audit (full trace per line); set to "" to disable.
    task_jsonl_path: str = "data/task_events.jsonl"
    openai_api_key: str = ""  # OPENAI_API_KEY in .env
    openai_model: str = "gpt-4o-mini"  # OPENAI_MODEL in .env
    request_timeout_seconds: float = 120.0


settings = Settings()
