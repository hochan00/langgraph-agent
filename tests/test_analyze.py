from src.graph.nodes.analyze import align_with_activity
from src.schemas.activity_schema import CommitInfo, DailyActivity, RepoActivity


def _activity(*repos: str) -> dict:
    commit = CommitInfo(sha="abcdef1234", message="feat: x", authored_at="2026-10-20T10:00:00+09:00")
    return {repo: [commit] for repo in repos}


def _repo(name: str, summary: str = "요약") -> RepoActivity:
    return RepoActivity(repo=name, summary=summary, key_changes=["변경"])


def test_drops_repo_not_collected():
    daily = DailyActivity(repos=[_repo("a/repo"), _repo("ghost/repo")])
    aligned = align_with_activity(daily, _activity("a/repo"))
    assert [r.repo for r in aligned.repos] == ["a/repo"]


def test_fills_missing_repo_with_empty_analysis():
    aligned = align_with_activity(DailyActivity(repos=[_repo("b/repo")]), _activity("a/repo", "b/repo"))
    assert [r.repo for r in aligned.repos] == ["a/repo", "b/repo"]
    assert aligned.repos[0].summary == ""
    assert aligned.repos[0].key_changes == []
    assert aligned.repos[1].summary == "요약"


def test_keeps_first_when_repo_duplicated():
    daily = DailyActivity(repos=[_repo("a/repo", "첫 번째"), _repo("a/repo", "두 번째")])
    assert align_with_activity(daily, _activity("a/repo")).repos[0].summary == "첫 번째"
