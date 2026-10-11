from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.core.llm import get_llm
from src.graph.state import AgentState
from src.tools.fetch_diff import fetch_diff

tools = [fetch_diff]

_DATA = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "prompts" / "AGENT_PROMPT.yaml").read_text(encoding="utf-8")
)

AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _DATA["system"]),
        MessagesPlaceholder("messages"),
    ]
)


def agent(state: AgentState) -> dict:
    """커밋 목록을 보고 diff를 확인할 커밋을 고른다. 도구 호출이 없으면 판단을 마친 것이다."""
    chain = AGENT_PROMPT | get_llm().bind_tools(tools)
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}


def route_agent_result(state: AgentState) -> str:
    return "continue" if state["messages"][-1].tool_calls else "done"
