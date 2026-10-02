from datetime import date

from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from src.core.dates import get_tz
from src.graph.context import DevlogContext
from src.graph.state import AgentState
from src.schemas.activity_schema import Activity
from src.services.github_activity import collect_daily_commits


def format_activity(day: str, activity: Activity) -> str:
    """에이전트에게 줄 커밋 목록. 레포·SHA·메시지는 수집 결과를 그대로 옮긴다."""
    total = sum(len(commits) for commits in activity.values())
    lines = [f"{day} 하루 동안 수집된 커밋입니다. (레포 {len(activity)}개, 커밋 {total}개)"]
    for repo, commits in activity.items():
        lines.append(f"\n## {repo}")
        for commit in commits:
            lines.append(f"- {commit.short_sha} {commit.title}")
            body = commit.message.strip().splitlines()[1:]
            lines.extend(f"    {line}" for line in body if line.strip())
    return "\n".join(lines)


def collect_activity(state: AgentState, runtime: Runtime[DevlogContext]) -> dict:
    """지정한 날짜의 커밋을 코드로 수집한다. 커밋 목록은 LLM이 만들지 않는다."""
    activity = collect_daily_commits(
        runtime.context["github_token"],
        date.fromisoformat(state["date"]),
        get_tz(),
        runtime.context.get("github_login", ""),
    )
    if not activity:
        return {"activity": {}}
    return {
        "activity": activity,
        "messages": [HumanMessage(content=format_activity(state["date"], activity))],
    }


def route_after_collect(state: AgentState) -> str:
    return "has_activity" if state["activity"] else "no_activity"
