from langchain_anthropic import ChatAnthropic

from src.core.config import settings


def get_llm(temperature: float | None = None) -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.ANTHROPIC_MODEL,
        temperature=temperature or settings.ANTHROPIC_TEMPERATURE,
    )
