from collections.abc import Iterable, Iterator
from datetime import date, timedelta, timezone
from zoneinfo import ZoneInfo

from github import Github

from src.core.dates import search_date_range, today
from src.schemas.activity_schema import Activity, CommitInfo


def build_search_query(login: str, start: date, tz: ZoneInfo, end: date | None = None) -> str:
    return f"author:{login} author-date:{search_date_range(start, tz, end)}"


def group_by_repo(items: Iterable[tuple[str, CommitInfo]]) -> Activity:
    """SHA 기준으로 중복을 제거하고 레포별로 묶는다. 레포는 이름순, 커밋은 작성 시각 순으로 정렬한다."""
    seen: set[str] = set()
    grouped: Activity = {}
    for repo, commit in items:
        if commit.sha in seen:
            continue
        seen.add(commit.sha)
        grouped.setdefault(repo, []).append(commit)
    return {
        repo: sorted(commits, key=lambda c: c.authored_at)
        for repo, commits in sorted(grouped.items())
    }


def count_by_day(activity: Activity) -> list[dict]:
    """날짜별 커밋 수를 최근 날짜 순으로 반환한다. authored_at이 이미 설정 시간대 기준이라 앞 10자리가 날짜다."""
    counts: dict[str, int] = {}
    for commits in activity.values():
        for commit in commits:
            day = commit.authored_at[:10]
            counts[day] = counts.get(day, 0) + 1
    return [{"date": d, "count": c} for d, c in sorted(counts.items(), reverse=True)]


def _search(gh: Github, query: str, tz: ZoneInfo) -> Iterator[tuple[str, CommitInfo]]:
    for item in gh.search_commits(query=query):
        authored = item.commit.author.date
        if authored.tzinfo is None:
            authored = authored.replace(tzinfo=timezone.utc)
        yield item.repository.full_name, CommitInfo(
            sha=item.sha,
            message=item.commit.message,
            authored_at=authored.astimezone(tz).isoformat(),
        )


def _search_activity(github_token: str, login: str, start: date, tz: ZoneInfo, end: date | None = None) -> Activity:
    # 검색 API는 분당 30회 제한이 있어 한 범위를 한 번의 쿼리(페이지당 100건)로 가져온다.
    gh = Github(github_token, per_page=100)
    login = login or gh.get_user().login
    return group_by_repo(_search(gh, build_search_query(login, start, tz, end), tz))


def collect_daily_commits(github_token: str, day: date, tz: ZoneInfo, login: str = "") -> Activity:
    """그날(tz 기준) 사용자가 작성한 커밋을 모든 레포에서 모아 레포별로 묶는다.
    검색 API 특성상 기본 브랜치의 커밋만 수집된다."""
    return _search_activity(github_token, login, day, tz)


def recent_commit_days(github_token: str, tz: ZoneInfo, days: int = 14, login: str = "") -> list[dict]:
    """최근 N일(오늘 포함) 중 커밋이 있었던 날짜와 커밋 수를 최근 순으로 반환한다."""
    end = today(tz)
    return count_by_day(_search_activity(github_token, login, end - timedelta(days=days - 1), tz, end))
