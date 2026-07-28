from datetime import datetime, timedelta

from github import Github
from langchain_core.tools import tool

from src.core.config import settings


@tool
def list_repos() -> list[str]:
    """사용자가 개발 회고를 작성하고 싶어 하지만 어느 레포인지 특정하지 않았을 때 사용한다.
    최근 한 달간 사용자가 실제로 커밋한 레포 목록을 조회해 후보로 보여준다."""
    gh = Github(settings.GITHUB_TOKEN)

    username = gh.get_user().login
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    commits = gh.search_commits(query=f"author:{username} author-date:>{one_month_ago}")

    repo_names = set()
    for commit in commits:
        repo_names.add(commit.repository.full_name)

    return list(repo_names)
