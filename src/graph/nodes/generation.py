from langchain_core.output_parsers import StrOutputParser

from src.core.llm import get_llm
from src.graph.state import GraphState
from src.services.prompts import RAG_PROMPT
from src.services.utils import format_docs


def generate(state: GraphState) -> dict:
    question = state["question"]
    documents = state["documents"]

    llm = get_llm()
    chain = RAG_PROMPT | llm | StrOutputParser()
    generation = chain.invoke({"context": format_docs(documents), "question": question})
    return {"generation": generation}


def refuse_answer(state: GraphState) -> dict:
    return {"generation": "문서 근거가 부족하여 답변할 수 없습니다."}
