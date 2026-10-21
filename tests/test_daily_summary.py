from datetime import date

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.jobs.daily_summary import count_diff_checks, parse_args, render_analysis
from src.schemas.activity_schema import CommitInfo, DailyActivity, RepoActivity


def test_parse_args_date_and_dry_run():
    args = parse_args(["--date", "2026-10-20", "--dry-run"])
    assert args.date == date(2026, 10, 20)
    assert args.dry_run


def test_parse_args_requires_dry_run_until_save_exists():
    with pytest.raises(SystemExit):
        parse_args([])


def test_count_diff_checks_excludes_rejected_calls():
    messages = [
        HumanMessage(content="커밋 목록"),
        AIMessage(content=""),
        ToolMessage(content="[o/r@abcdef1]\nfile_name: a.py", tool_call_id="1"),
        ToolMessage(content="거부: x/y는 이 날짜에 수집된 레포가 아닙니다.", tool_call_id="2"),
    ]
    assert count_diff_checks(messages) == 1


def test_render_analysis_uses_collected_commits():
    activity = {
        "o/r": [CommitInfo(sha="abcdef1234", message="feat: 수집\n\n본문", authored_at="2026-10-20T10:00:00+09:00")]
    }
    daily = DailyActivity(repos=[RepoActivity(repo="o/r", summary="수집 노드를 추가했다.", key_changes=["수집 노드"])])

    assert render_analysis(daily, activity) == "\n".join(
        [
            "### o/r",
            "",
            "수집 노드를 추가했다.",
            "",
            "**주요 변경사항**",
            "",
            "- 수집 노드",
            "",
            "**커밋**",
            "",
            "- `abcdef1` feat: 수집",
        ]
    )
