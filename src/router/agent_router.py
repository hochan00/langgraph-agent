from fastapi import APIRouter

from src.graph.graph import graph
from src.schemas.agent_schema import (
    AgentRequest,
    AgentResponse,
)

router = APIRouter(tags=["Agent"])


def _extract_text(content: str | list) -> str:
    """모델 응답에 따라 content가 문자열이 아니라 블록 리스트로 올 수 있어 텍스트만 추출한다."""
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )


@router.post("/agent", response_model=AgentResponse)
def agent_graph(req: AgentRequest):
    """개발 회고 자동 생성 에이전트"""
    result = graph.invoke(
        {"messages": [("user", req.message)]},
        config={"configurable": {"thread_id": req.thread_id}},
    )

    return AgentResponse(
        message=_extract_text(result["messages"][-1].content),
    )
