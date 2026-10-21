"""하루치 개발 작업 정리 실행기.

    uv run python -m src.jobs.daily_summary --dry-run                     # 어제(TIMEZONE 기준)
    uv run python -m src.jobs.daily_summary --date 2026-10-20 --dry-run   # 특정 날짜
"""

from dotenv import load_dotenv

load_dotenv()

import argparse
import sys
from datetime import date

from langchain_core.messages import ToolMessage

from src.core.dates import get_tz, yesterday
from src.graph.runner import run_devlog
from src.schemas.activity_schema import Activity, DailyActivity


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GitHub 커밋을 근거로 하루 개발 작업을 정리한다.")
    parser.add_argument("--date", type=date.fromisoformat, help="정리할 날짜 YYYY-MM-DD (기본: 어제)")
    parser.add_argument("--dry-run", action="store_true", help="저장하지 않고 결과만 출력한다")
    args = parser.parse_args(argv)
    if not args.dry_run:
        parser.error("저장 기능은 아직 없습니다. --dry-run으로 실행하세요.")
    return args


def count_diff_checks(messages: list) -> int:
    """fetch_diff로 실제 diff를 확인한 횟수 (거부된 호출 제외)."""
    return sum(
        1
        for m in messages
        if isinstance(m, ToolMessage) and not str(m.content).startswith("거부")
    )


def render_analysis(daily: DailyActivity, activity: Activity) -> str:
    """레포별 분석에 수집한 커밋 목록을 붙인다. 커밋 목록은 LLM 출력이 아니라 수집 결과다."""
    lines: list[str] = []
    for repo_activity in daily.repos:
        lines += [f"### {repo_activity.repo}", "", repo_activity.summary or "(분석 없음)", ""]
        if repo_activity.key_changes:
            lines += ["**주요 변경사항**", "", *(f"- {c}" for c in repo_activity.key_changes), ""]
        lines += ["**커밋**", "", *(f"- `{c.short_sha}` {c.title}" for c in activity[repo_activity.repo]), ""]
    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    day = args.date or yesterday(get_tz())

    try:
        state = run_devlog(day)
    except RuntimeError as e:
        print(f"[{day}] 실행 실패: {e}", file=sys.stderr)
        return 1

    activity = state.get("activity") or {}
    if not activity:
        print(f"[{day}] 활동 없음")
        return 0

    total = sum(len(commits) for commits in activity.values())
    diffs = count_diff_checks(state["messages"])
    print(f"[{day}] 레포 {len(activity)}개 · 커밋 {total}개 · diff 확인 {diffs}건")
    print()
    print(render_analysis(state["daily_activity"], activity))
    return 0


if __name__ == "__main__":
    sys.exit(main())
