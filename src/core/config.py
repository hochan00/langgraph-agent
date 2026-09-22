from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GOOGLE_API_KEY: str = ""
    LANGSMITH_TRACING: bool = True
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "langgraph-agent"

    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    GITHUB_TOKEN: str = ""
    GITHUB_LOGIN: str = ""  # 비우면 토큰 소유자

    TIMEZONE: str = "Asia/Seoul"

    OBSIDIAN_VAULT_PATH: str = ""
    OBSIDIAN_DAILY_DIR: str = "개발기록"
    OBSIDIAN_NOTE_FORMAT: str = "%y.%m.%d"


settings = Settings()
