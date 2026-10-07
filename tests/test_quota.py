from datetime import datetime, timezone

import pytest

from app.quota import period_of


# 月中的時間離換月很遠，UTC 和台北是同一個月；先確認回傳的格式是 YYYY-MM
def test_period_of_returns_year_and_month():
    moment = datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc)

    result = period_of(moment)

    assert result == "2026-10"


# 台北 9/30 23:59 還沒換月：換算不能多推，把上個月的最後一分鐘算進新的月
def test_period_of_keeps_last_minute_of_month():
    moment = datetime(2026, 9, 30, 15, 59, tzinfo=timezone.utc)

    result = period_of(moment)

    assert result == "2026-09"


# 台北 10/1 00:00 剛換月，UTC 還在 9/30：要算 10 月
def test_period_of_moves_first_minute_to_new_month():
    moment = datetime(2026, 9, 30, 16, 0, tzinfo=timezone.utc)

    result = period_of(moment)

    assert result == "2026-10"


# 決策書 3.2 的例子：台北 10/1 00:30 = UTC 9/30 16:30，歸入 10 月
def test_period_of_matches_decision_book_example():
    moment = datetime(2026, 9, 30, 16, 30, tzinfo=timezone.utc)

    result = period_of(moment)

    assert result == "2026-10"


# 跨年：台北已經是 2027/1/1，年份也要跟著進位，月份要補 0
def test_period_of_moves_new_year_to_next_year():
    moment = datetime(2026, 12, 31, 16, 0, tzinfo=timezone.utc)

    result = period_of(moment)

    assert result == "2027-01"


# 沒帶時區的時間不知道是哪裡的幾點：不猜，直接拒絕
def test_period_of_rejects_time_without_timezone():
    moment = datetime(2026, 10, 15, 3, 0)

    with pytest.raises(ValueError):
        period_of(moment)