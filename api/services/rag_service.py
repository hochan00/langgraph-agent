import logging
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from api.core.llm import get_llm
from api.services.document_store import get_retriever
from api.services.prompts import RAG_PROMPT
from api.services.utils import format_docs

logger = logging.getLogger(__name__)


async def query_rag(question: str) -> dict[str, Any]:
    llm = get_llm()
    retriever = get_retriever()

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke(question)

    docs = retriever.invoke(question)
    sources = list({doc.metadata.get("source", "") for doc in docs})

    return {"answer": answer, "sources": sources}
