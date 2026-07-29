from datetime import datetime
from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.core.llm import get_llm
from src.graph.state import AgentState
from src.schemas.retro_schema import RetroDraft
from src.tools.fetch_commits import fetch_commits
from src.tools.fetch_diff import fetch_diff
from src.tools.list_repo import list_repos

tools = [list_repos, fetch_commits, fetch_diff]

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

    updates: dict = {"messages": [response]}
    for call in response.tool_calls:
        if call["name"] == "fetch_commits":
            updates["repo"] = call["args"]["repo"]
    return updates


def route_agent_result(state: AgentState) -> str:
    if state["messages"][-1].tool_calls:
        return "continue"
    if state.get("repo"):
        return "end"
    return "wait"


def _extract_text(content: str | list) -> str:
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def finalize(state: AgentState) -> dict:
    retro_draft = RetroDraft(report=_extract_text(state["messages"][-1].content))

    return {
        "retro_draft": retro_draft,
        "repo": state.get("repo", ""),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
