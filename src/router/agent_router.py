from fastapi import APIRouter

from src.graph.graph import graph
from src.schemas.agent_schema import (
    AgentRequest,
    AgentResponse,
)

router = APIRouter(tags=["Agent"])


@router.post("/agent", response_model=AgentResponse)
def agent_graph(req: AgentRequest):
    """개발 회고 자동 생성 에이전트"""
    result = graph.invoke(
        {"messages": [("user", req.message)]},
        config={"configurable": {"thread_id": req.thread_id}},
    )

    return AgentResponse(
        message=result["messages"][-1].content,
    )
