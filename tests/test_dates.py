from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from src.core.dates import day_range, search_date_range, today, yesterday

KST = ZoneInfo("Asia/Seoul")


def test_day_range_uses_kst_midnight():
    start, end = day_range(date(2026, 10, 20), KST)
    assert start.isoformat() == "2026-10-20T00:00:00+09:00"
    assert end.isoformat() == "2026-10-21T00:00:00+09:00"
    assert start.astimezone(timezone.utc).isoformat() == "2026-10-19T15:00:00+00:00"


def test_today_follows_kst_not_utc():
    # UTC로는 10/19 16시지만 KST로는 이미 10/20 01시
    now = datetime(2026, 10, 19, 16, 0, tzinfo=timezone.utc)
    assert today(KST, now) == date(2026, 10, 20)
    assert yesterday(KST, now) == date(2026, 10, 19)


def test_yesterday_just_after_midnight():
    now = datetime(2026, 10, 20, 0, 30, tzinfo=KST)
    assert yesterday(KST, now) == date(2026, 10, 19)


def test_search_date_range_single_day():
    assert (
        search_date_range(date(2026, 10, 20), KST)
        == "2026-10-20T00:00:00+09:00..2026-10-20T23:59:59+09:00"
    )


def test_search_date_range_multiple_days():
    assert (
        search_date_range(date(2026, 10, 7), KST, date(2026, 10, 20))
        == "2026-10-07T00:00:00+09:00..2026-10-20T23:59:59+09:00"
    )
