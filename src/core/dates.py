from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.core.config import settings


def get_tz(name: str | None = None) -> ZoneInfo:
    """날짜 경계 기준 시간대. 서버 로컬 시간 대신 설정값(TIMEZONE)을 쓴다."""
    return ZoneInfo(name or settings.TIMEZONE)


def today(tz: ZoneInfo, now: datetime | None = None) -> date:
    return (now or datetime.now(tz)).astimezone(tz).date()


def yesterday(tz: ZoneInfo, now: datetime | None = None) -> date:
    return today(tz, now) - timedelta(days=1)


def day_range(day: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """그 날짜의 시작(포함)과 다음 날 시작(미포함)을 tz 기준 aware datetime으로 반환한다."""
    start = datetime.combine(day, time.min, tzinfo=tz)
    return start, datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)


def search_date_range(start: date, tz: ZoneInfo, end: date | None = None) -> str:
    """GitHub 검색 쿼리용 날짜 범위(start ~ end, 양 끝 포함).
    예: 2026-10-20T00:00:00+09:00..2026-10-20T23:59:59+09:00"""
    range_start, _ = day_range(start, tz)
    _, range_end = day_range(end or start, tz)
    return f"{range_start.isoformat()}..{(range_end - timedelta(seconds=1)).isoformat()}"
