from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings


def get_llm(temperature: float | None = None) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        temperature=temperature or settings.GEMINI_TEMPERATURE,
    )
