from langchain_core.output_parsers import StrOutputParser

from api.core.config import settings
from api.core.llm import get_llm
from api.graph.state import GraphState
from api.services.rag_service import RAG_PROMPT, format_docs, get_vectorstore


def retrieve(state: GraphState) -> dict:
    question = state["question"]
    retriever = get_vectorstore().as_retriever(search_kwargs={"k": settings.RAG_TOP_K})
    documents = retriever.invoke(question)
    return {"documents": documents}


def generate(state: GraphState) -> dict:
    question = state["question"]
    documents = state["documents"]

    llm = get_llm()
    chain = RAG_PROMPT | llm | StrOutputParser()
    generation = chain.invoke({"context": format_docs(documents), "question": question})
    return {"generation": generation}
