from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_anthropic import ChatAnthropic
from src.core.config import settings


# def get_llm() -> ChatAnthropic:
#    return ChatAnthropic(model=settings.ANTHROPIC_MODEL)
def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        temperature=settings.GEMINI_TEMPERATURE,
    )
