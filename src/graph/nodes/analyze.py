from pathlib import Path

import yaml

from src.core.llm import get_llm
from src.graph.state import AgentState
from src.schemas.activity_schema import Activity, DailyActivity, RepoActivity

_DATA = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "prompts" / "ANALYZE_PROMPT.yaml").read_text(encoding="utf-8")
)


def align_with_activity(daily: DailyActivity, activity: Activity) -> DailyActivity:
    """LLM 분석의 레포 목록을 수집 결과에 맞춘다.
    수집되지 않은 레포는 버리고, 빠진 레포는 빈 분석으로 채우며, 순서는 수집 결과를 따른다."""
    by_repo: dict[str, RepoActivity] = {}
    for repo_activity in daily.repos:
        by_repo.setdefault(repo_activity.repo, repo_activity)
    return DailyActivity(
        repos=[
            by_repo.get(repo) or RepoActivity(repo=repo, summary="", key_changes=[])
            for repo in activity
        ]
    )


def analyze_activity(state: AgentState) -> dict:
    """지금까지의 커밋 목록·diff 확인 결과를 레포별 구조화 분석(DailyActivity)으로 정리한다."""
    analyzer = get_llm().with_structured_output(DailyActivity)
    daily = analyzer.invoke(list(state["messages"]) + [("user", _DATA["instruction"])])
    return {"daily_activity": align_with_activity(daily or DailyActivity(repos=[]), state["activity"])}
