from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.core.llm import get_llm
from src.graph.state import AgentState
from src.tools.fetch_commits import fetch_commits
from src.tools.list_repo import list_repos

tools = [list_repos, fetch_commits]

_DATA = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "prompts" / "AGENT_PROMPT.yaml").read_text()
)

AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _DATA["system"]),
        MessagesPlaceholder("messages"),
    ]
)


def agent(state: AgentState) -> dict:
    llm_with_tools = get_llm().bind_tools(tools)
    chain = AGENT_PROMPT | llm_with_tools
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}


def route_agent_result(state: AgentState) -> str:
    if state["messages"][-1].tool_calls:
        return "continue"
    return "end"
