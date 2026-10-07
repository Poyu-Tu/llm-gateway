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