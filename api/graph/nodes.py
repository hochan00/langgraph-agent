from langchain_core.output_parsers import StrOutputParser

from api.core.llm import get_llm
from api.graph.state import GraphState
from api.services.document_store import get_retriever
from api.services.prompts import RAG_PROMPT
from api.services.utils import format_docs


def retrieve(state: GraphState) -> dict:
    question = state["question"]
    retriever = get_retriever()
    documents = retriever.invoke(question)
    return {"documents": documents}


def generate(state: GraphState) -> dict:
    question = state["question"]
    documents = state["documents"]

    llm = get_llm()
    chain = RAG_PROMPT | llm | StrOutputParser()
    generation = chain.invoke({"context": format_docs(documents), "question": question})
    return {"generation": generation}
