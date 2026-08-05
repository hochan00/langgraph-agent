from github import Github
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime

from src.graph.context import RetroContext


@tool
def fetch_commits(repo: str, runtime: ToolRuntime[RetroContext]) -> list[dict]:
    """사용자가 특정 레포를 선택해 회고 작성을 요청했을 때, 그 레포의 오늘 커밋 메시지 목록을 가져온다."""

    gh = Github(runtime.context["github_token"])
    repository = gh.get_repo(repo)
    commits = repository.get_commits()
    return [{"sha": commit.sha, "message": commit.commit.message} for commit in commits]
