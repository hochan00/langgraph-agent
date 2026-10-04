from datetime import date

from src.core.config import settings
from src.graph.graph import graph

# 커밋이 많은 날 agent ⇄ tools 왕복이 길어질 수 있어 기본값(25)보다 넉넉하게 둔다.
RECURSION_LIMIT = 60


def run_devlog(day: date) -> dict:
    """하루치 작업 정리 그래프를 요청 단위로 실행한다. 체크포인터 없이 매번 새로 시작한다."""
    if not settings.GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN이 설정되지 않았습니다.")
    return graph.invoke(
        {"messages": [], "date": day.isoformat()},
        config={
            "recursion_limit": RECURSION_LIMIT,
            "run_name": f"devlog {day.isoformat()}",
            "tags": ["devlog"],
        },
        context={
            "github_token": settings.GITHUB_TOKEN,
            "github_login": settings.GITHUB_LOGIN,
        },
    )
