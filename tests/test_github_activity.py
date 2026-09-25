from datetime import date
from zoneinfo import ZoneInfo

from src.schemas.activity_schema import CommitInfo
from src.services.github_activity import build_search_query, count_by_day, group_by_repo

KST = ZoneInfo("Asia/Seoul")


def _commit(sha: str, at: str, message: str = "feat: 기능") -> CommitInfo:
    return CommitInfo(sha=sha, message=message, authored_at=at)


def test_build_search_query_uses_kst_range():
    assert build_search_query("octocat", date(2026, 10, 20), KST) == (
        "author:octocat author-date:2026-10-20T00:00:00+09:00..2026-10-20T23:59:59+09:00"
    )


def test_group_by_repo_removes_duplicate_sha_and_sorts():
    items = [
        ("b/repo", _commit("bbb2", "2026-10-20T15:00:00+09:00")),
        ("a/repo", _commit("aaa2", "2026-10-20T13:00:00+09:00")),
        ("a/repo", _commit("aaa1", "2026-10-20T09:00:00+09:00")),
        # 포크 등으로 같은 커밋이 다른 레포에서 다시 검색되는 경우
        ("c/fork", _commit("aaa1", "2026-10-20T09:00:00+09:00")),
    ]
    grouped = group_by_repo(items)

    assert list(grouped) == ["a/repo", "b/repo"]
    assert [c.sha for c in grouped["a/repo"]] == ["aaa1", "aaa2"]


def test_group_by_repo_empty():
    assert group_by_repo([]) == {}


def test_count_by_day_recent_first():
    activity = {
        "a/repo": [
            _commit("1", "2026-10-19T23:59:00+09:00"),
            _commit("2", "2026-10-20T00:01:00+09:00"),
        ],
        "b/repo": [_commit("3", "2026-10-20T10:00:00+09:00")],
    }
    assert count_by_day(activity) == [
        {"date": "2026-10-20", "count": 2},
        {"date": "2026-10-19", "count": 1},
    ]


def test_commit_title_is_first_line():
    commit = _commit("abcdef1234", "2026-10-20T10:00:00+09:00", "fix: 버그 수정\n\n자세한 설명")
    assert commit.short_sha == "abcdef1"
    assert commit.title == "fix: 버그 수정"
    assert _commit("x", "2026-10-20T10:00:00+09:00", "  ").title == "(메시지 없음)"
