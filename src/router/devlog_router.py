from fastapi import APIRouter, HTTPException, Query

from src.core.config import settings
from src.core.dates import get_tz
from src.schemas.api_schema import CommitDay
from src.services.github_activity import recent_commit_days

router = APIRouter(tags=["DevLog"])


def _github_token() -> str:
    if not settings.GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN이 설정되지 않았습니다.")
    return settings.GITHUB_TOKEN


@router.get("/days", response_model=list[CommitDay])
def get_commit_days(days: int = Query(14, ge=1, le=60)):
    """최근 N일 중 커밋이 있었던 날짜와 커밋 수를 최근 순으로 반환한다 (에이전트를 거치지 않음)."""
    return recent_commit_days(_github_token(), get_tz(), days, settings.GITHUB_LOGIN)
