import pytest

from src.schemas.activity_schema import CommitInfo
from src.tools.fetch_diff import (
    format_commit_diff,
    format_file_diff,
    is_generated_file,
    resolve_commit,
)

ACTIVITY = {
    "owner/repo": [
        CommitInfo(sha="a1b2c3d4e5f6", message="feat: a", authored_at="2026-10-20T10:00:00+09:00"),
        CommitInfo(sha="a1b2c3d9e9e9", message="fix: b", authored_at="2026-10-20T11:00:00+09:00"),
    ]
}


@pytest.mark.parametrize(
    "filename",
    ["uv.lock", "frontend/package-lock.json", "static/app.min.js", "dist/index.js", "web/build/main.js"],
)
def test_generated_files(filename):
    assert is_generated_file(filename)


@pytest.mark.parametrize("filename", ["src/main.py", "src/build_tools.py", "README.md"])
def test_source_files(filename):
    assert not is_generated_file(filename)


def test_generated_file_shows_name_only():
    assert format_file_diff("uv.lock", "+" * 100) == "file_name: uv.lock\n(lock·빌드 산출물 — 내용 생략)"


def test_none_patch_is_binary_or_large():
    assert format_file_diff("logo.png", None) == "file_name: logo.png\n(바이너리 또는 대용량 파일)"


def test_long_patch_is_truncated_per_file():
    text = format_file_diff("src/a.py", "x" * 50, limit=10)
    assert text == "file_name: src/a.py\nxxxxxxxxxx\n... (이하 40자 생략)"


def test_commit_diff_lists_remaining_files_by_name_after_limit():
    files = [("src/a.py", "a" * 30), ("src/b.py", "b" * 30), ("src/c.py", None)]
    text = format_commit_diff(files, limit=60)

    assert "a" * 30 in text
    assert "b" * 30 not in text
    assert "(커밋 diff 길이 상한으로 이후 파일은 이름만 표시)\nfile_name: src/b.py\nfile_name: src/c.py" in text


def test_commit_diff_without_files():
    assert format_commit_diff([]) == "(변경된 파일 없음)"


def test_resolve_commit_accepts_collected_short_sha():
    assert resolve_commit(ACTIVITY, "owner/repo", "A1B2C3D4") == "a1b2c3d4e5f6"


def test_resolve_commit_rejects_unknown_repo():
    with pytest.raises(ValueError, match="수집된 레포가 아닙니다"):
        resolve_commit(ACTIVITY, "other/repo", "a1b2c3d4")


def test_resolve_commit_rejects_unknown_sha():
    with pytest.raises(ValueError, match="수집된 커밋이 아닙니다"):
        resolve_commit(ACTIVITY, "owner/repo", "deadbeef")


def test_resolve_commit_rejects_short_or_ambiguous_sha():
    with pytest.raises(ValueError, match="7자 이상"):
        resolve_commit(ACTIVITY, "owner/repo", "a1b2")
    with pytest.raises(ValueError, match="여러 개"):
        resolve_commit(ACTIVITY, "owner/repo", "a1b2c3d")
