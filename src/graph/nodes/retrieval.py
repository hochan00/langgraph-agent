from langchain_core.output_parsers import StrOutputParser

from src.core.llm import get_llm
from src.graph.state import GraphState
from src.services.document_store import get_retriever
from src.services.prompts import TRANSFORM_QUERY


def retrieve(state: GraphState) -> dict:
    query = state.get("query", state["question"])

    retriever = get_retriever()
    documents = retriever.invoke(query)

    return {"documents": documents}


def transform_query(state: GraphState) -> dict:
    question = state["question"]

    llm = get_llm()
    chain = TRANSFORM_QUERY | llm | StrOutputParser()
    new_query = chain.invoke({"query": question})

    return {"query": new_query}
