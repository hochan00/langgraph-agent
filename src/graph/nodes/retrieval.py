from src.graph.state import GraphState
from src.services.document_store import get_retriever


def retrieve(state: GraphState) -> dict:
    query = state.get("query", state["question"])
    retriever = get_retriever()
    documents = retriever.invoke(query)
    return {"documents": documents}
