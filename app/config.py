from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/agent.db"
    # Append-only JSONL audit (full trace per line); set to "" to disable.
    task_jsonl_path: str = "data/task_events.jsonl"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    request_timeout_seconds: float = 120.0


settings = Settings()
