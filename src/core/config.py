import re

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    NOTION_PARENT_PAGE_ID: str = Field(
        default="", validation_alias="NOTION_PARENT_PAGE_URL"
    )

    @field_validator("NOTION_PARENT_PAGE_ID")
    def extract_page_id(v: str) -> str:
        if not v:
            return v
        cleaned = v.split("?")[0]
        no_dash = re.sub(r"-", "", cleaned)
        match = re.search(r"[0-9a-fA-F]{32}$", no_dash)
        if not match:
            raise ValueError(f"페이지 ID를 URL에서 찾을 수 없음: {v}")
        return match.group(0)

    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LANGSMITH_TRACING: bool = True
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "langgraph-agent"

    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_TEMPERATURE: float = 0

    ANTHROPIC_MODEL: str = "claude-sonnet-5"
    ANTHROPIC_TEMPERATURE: float = 0.3

    NOTION_API_KEY: str = ""
    GITHUB_TOKEN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
