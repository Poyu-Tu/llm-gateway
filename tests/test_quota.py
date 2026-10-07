from datetime import datetime, timezone

import pytest

from app.quota import is_over_quota, period_of, seconds_until_next_period


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


# 還沒用完就放行；額度和已用量故意差 1，兩個參數拿反時答案會不同
def test_is_over_quota_allows_usage_below_limit():
    assert is_over_quota(1000, 999) is False


# 剛好用完就要擋：用「大於等於」，不是「大於」
def test_is_over_quota_blocks_usage_equal_to_limit():
    assert is_over_quota(1000, 1000) is True


# 已經超過當然要擋
def test_is_over_quota_blocks_usage_above_limit():
    assert is_over_quota(1000, 1001) is True


# 額度 0 是嚴格上限，不是「沒有上限」（E17 的邊界值）
def test_is_over_quota_treats_zero_limit_as_strict():
    assert is_over_quota(0, 0) is True


# 月底最後一分鐘：剩 60 秒。
def test_seconds_until_next_period_counts_last_minute():
    moment = datetime(2026, 10, 31, 15, 59, tzinfo=timezone.utc)

    result = seconds_until_next_period(moment)

    assert result == 60


# # 剛換月的那一刻：要等一整個月（十月 31 天），不能回 0；沒換算成台北時間會在這裡算錯
def test_seconds_until_next_period_covers_whole_month_at_start():
    moment = datetime(2026, 9, 30, 16, 0, tzinfo=timezone.utc)

    result = seconds_until_next_period(moment)

    assert result == 2_678_400


# 十二月的下個月是明年一月：月份不能變成 13
def test_seconds_until_next_period_crosses_year():
    moment = datetime(2026, 12, 31, 15, 0, tzinfo=timezone.utc)

    result = seconds_until_next_period(moment)

    assert result == 3600


# 不足一秒要進位：叫客戶端早半秒回來，還是會被擋
def test_seconds_until_next_period_rounds_up_partial_second():
    moment = datetime(2026, 10, 31, 15, 59, 59, 500000, tzinfo=timezone.utc)

    result = seconds_until_next_period(moment)

    assert result == 1


# 沒帶時區的時間不知道是哪裡的幾點：不猜，直接拒絕
def test_seconds_until_next_period_rejects_time_without_timezone():
    moment = datetime(2026, 10, 15, 3, 0)

    with pytest.raises(ValueError):
        seconds_until_next_period(moment)