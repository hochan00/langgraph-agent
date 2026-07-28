from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_anthropic import ChatAnthropic
from src.core.config import settings


# def get_llm() -> ChatAnthropic:
#    return ChatAnthropic(model=settings.ANTHROPIC_MODEL)
def get_llm(temperature: float | None = None) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        temperature=temperature or settings.GEMINI_TEMPERATURE,
    )
