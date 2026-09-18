from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
    )
