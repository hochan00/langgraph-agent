from typing import Annotated

from github import Github
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.core.config import settings


@tool
def fetch_diff(
    repo: Annotated[str, InjectedState("repo")], commit_sha: str
) -> list[str]:
    """커밋 메시지만으로 판단하기 어려운 경우, 해당 커밋의 실제 코드 변경 내용(diff)을 가져온다."""

    gh = Github(settings.GITHUB_TOKEN)
    repository = gh.get_repo(repo)
    commit = repository.get_commit(commit_sha)

    diffs = []
    for file in commit.files:
        diffs.append(f"file_name: {file.filename}\n {file.patch}")
    return diffs
