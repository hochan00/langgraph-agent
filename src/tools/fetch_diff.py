from fnmatch import fnmatch
from typing import Annotated

from github import Github
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState, ToolRuntime

from src.graph.context import DevlogContext
from src.schemas.activity_schema import Activity

MAX_FILE_PATCH_CHARS = 4000
MAX_COMMIT_DIFF_CHARS = 15000

# 자동 생성 파일은 diff가 길기만 하고 작업 내용을 알려주지 않아 파일명만 남긴다.
GENERATED_PATTERNS = (
    "*.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "*.min.js",
    "*.min.css",
    "*.map",
    "dist/*",
    "*/dist/*",
    "build/*",
    "*/build/*",
)


def is_generated_file(filename: str) -> bool:
    name = filename.rsplit("/", 1)[-1]
    return any(fnmatch(name, p) or fnmatch(filename, p) for p in GENERATED_PATTERNS)


def format_file_diff(filename: str, patch: str | None, limit: int = MAX_FILE_PATCH_CHARS) -> str:
    if is_generated_file(filename):
        return f"file_name: {filename}\n(lock·빌드 산출물 — 내용 생략)"
    if patch is None:
        return f"file_name: {filename}\n(바이너리 또는 대용량 파일)"
    if len(patch) > limit:
        patch = f"{patch[:limit]}\n... (이하 {len(patch) - limit}자 생략)"
    return f"file_name: {filename}\n{patch}"


def format_commit_diff(files: list[tuple[str, str | None]], limit: int = MAX_COMMIT_DIFF_CHARS) -> str:
    """커밋의 파일별 diff를 합친다. 커밋 전체 길이 상한을 넘으면 남은 파일은 이름만 나열한다."""
    parts: list[str] = []
    used = 0
    for i, (filename, patch) in enumerate(files):
        part = format_file_diff(filename, patch)
        if used + len(part) > limit:
            rest = "\n".join(f"file_name: {name}" for name, _ in files[i:])
            parts.append(f"(커밋 diff 길이 상한으로 이후 파일은 이름만 표시)\n{rest}")
            break
        parts.append(part)
        used += len(part)
    return "\n\n".join(parts) or "(변경된 파일 없음)"


def resolve_commit(activity: Activity, repo: str, commit_sha: str) -> str:
    """수집된 레포·커밋이면 전체 SHA를 반환하고, 아니면 거부 사유를 담아 ValueError를 낸다."""
    commits = activity.get(repo)
    if commits is None:
        raise ValueError(f"{repo}는 이 날짜에 수집된 레포가 아닙니다. 수집된 레포: {', '.join(activity)}")
    sha = commit_sha.strip().lower()
    if len(sha) < 7:
        raise ValueError("SHA는 7자 이상이어야 합니다.")
    matches = [c.sha for c in commits if c.sha.startswith(sha)]
    if not matches:
        raise ValueError(f"{sha}는 {repo}에서 이 날짜에 수집된 커밋이 아닙니다.")
    if len(matches) > 1:
        raise ValueError(f"{sha}에 해당하는 커밋이 여러 개입니다. 더 긴 SHA를 넘기세요.")
    return matches[0]


@tool
def fetch_diff(
    repo: str,
    commit_sha: str,
    activity: Annotated[Activity, InjectedState("activity")],
    runtime: ToolRuntime[DevlogContext],
) -> str:
    """커밋 메시지만으로는 무엇을 바꿨는지 알기 어려울 때, 그 커밋의 실제 코드 변경 내용(diff)을 가져온다.
    repo에는 커밋 목록에 적힌 레포 이름(owner/repo)을, commit_sha에는 목록에 적힌 SHA(7자 이상)를 그대로 넘긴다."""
    try:
        full_sha = resolve_commit(activity, repo, commit_sha)
    except ValueError as e:
        return f"거부: {e}"

    commit = Github(runtime.context["github_token"]).get_repo(repo).get_commit(full_sha)
    diff = format_commit_diff([(f.filename, f.patch) for f in commit.files])
    return f"[{repo}@{full_sha[:7]}]\n{diff}"
