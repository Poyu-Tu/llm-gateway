from datetime import datetime, timezone, timedelta

# 台北時間固定比 UTC 快 8 小時（台灣沒有日光節約時間）；用固定偏移就不必另外安裝時區資料
TAIPEI_TZ = timezone(timedelta(hours=8))


# 額度按台北時間的月初切；系統內的時間是 UTC，直接取月份會把每月 1 號凌晨算上個月
def period_of(moment: datetime) -> str:
    """Return the quota period (YYYY-MM, Taipei time) that the moment belongs to."""
    if moment.tzinfo is None:
        raise ValueError("Moment must include a timezone")
    taipei_moment = moment.astimezone(TAIPEI_TZ)
    result = taipei_moment.strftime("%Y-%m")
    return result


# 額度剛好用完就擋；額度 0 代表一次都不能用，不是沒有上限
def is_over_quota(limit_micro_usd: int, used_micro_usd: int) -> bool:
    """Return True when the user has used up the monthly quota."""
    if used_micro_usd >= limit_micro_usd:
        return True
    return False


# Retry-After 的值：告訴被擋下的客戶端，額度什麼時候恢復
def seconds_until_next_period(moment: datetime) -> int:
    """Return whole seconds from the moment until the next quota period starts."""
    raise NotImplementedError("seconds_until_next_period is not written yet")