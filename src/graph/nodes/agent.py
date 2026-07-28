from src.core.llm import get_llm
from src.graph.state import AgentState
from src.tools.fetch_commits import fetch_commits
from src.tools.list_repo import list_repos

tools = [list_repos, fetch_commits]


def agent(state: AgentState) -> dict:
    llm_with_tools = get_llm().bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def route_agent_result(state: AgentState) -> str:
    if state["messages"][-1].tool_calls:
        return "continue"
    return "end"
