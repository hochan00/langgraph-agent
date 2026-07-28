from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()


from github import Github

from src.core.config import settings

gh = Github(settings.GITHUB_TOKEN)

username = gh.get_user().login
one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
commits = gh.search_commits(query=f"author:{username} author-date:>{one_month_ago}")

repo_names = set()
for commit in commits:
    repo_names.add(commit.repository.full_name)

print(repo_names)

# repos = gh.get_user().get_repos(type="owner")
# for repo in repos:
#    print(repo.full_name)

repository = gh.get_repo("hochan00/langgraph-agent")
commits = repository.get_commits()
for commit in commits:
    print(commit.commit.message)
