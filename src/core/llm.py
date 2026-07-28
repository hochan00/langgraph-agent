from langchain_anthropic import ChatAnthropic

from src.core.config import settings


def get_llm() -> ChatAnthropic:
    return ChatAnthropic(model=settings.ANTHROPIC_MODEL)
