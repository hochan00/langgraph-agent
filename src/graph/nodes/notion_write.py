from src.graph.state import AgentState
from src.tools.create_or_update_entry import create_or_update_entry


def notion_writer(state: AgentState) -> dict:
    page_url = create_or_update_entry.invoke(
        {
            "repo": state["repo"],
            "date": state["date"],
            "report": state["retro_draft"].report,
        }
    )
    return {"messages": [("assistant", f"노션에 저장했습니다: {page_url}")]}
