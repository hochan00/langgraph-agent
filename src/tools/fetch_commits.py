from github import Github
from langchain_core.tools import tool

from src.core.config import settings


@tool
def fetch_commits(repo: str) -> list[str]:
    """사용자가 특정 레포를 선택해 회고 작성을 요청했을 때, 그 레포의 오늘 커밋 메시지 목록을 가져온다."""

    gh = Github(settings.GITHUB_TOKEN)
    repository = gh.get_repo(repo)
    commits = repository.get_commits()
    return [commit.commit.message for commit in commits]
