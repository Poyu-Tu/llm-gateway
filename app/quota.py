import math
from datetime import datetime, timezone, timedelta

from botocore.client import BaseClient

from app.db import QUOTAS_TABLE

# 台北時間固定比 UTC 快 8 小時（台灣沒有日光節約時間）；用固定偏移就不必另外安裝時區資料
TAIPEI_TZ = timezone(timedelta(hours=8))

# 額度那一筆用固定的排序鍵，和每個月的已用量放在同一個人底下
LIMIT_SORT_KEY = "limit"


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
    if moment.tzinfo is None:
        raise ValueError("Moment must include a timezone")
    taipei_moment = moment.astimezone(TAIPEI_TZ)
    if taipei_moment.month == 12:
        next_year = taipei_moment.year + 1
        next_month = 1
    else:
        next_year = taipei_moment.year
        next_month = taipei_moment.month + 1
    next_start = datetime(next_year, next_month, 1, tzinfo=TAIPEI_TZ)
    diff = next_start - taipei_moment
    result = math.ceil(diff.total_seconds())
    return result


# 額度放在使用者層級的那一筆；查不到就當成 0：沒設定好的帳號不能變成沒有上限
def read_limit(client: BaseClient, user_id: str) -> int:
    """Return the user's monthly limit in micro-USD, or 0 when none is set."""
    key = {
        "user_id": {"S": user_id},
        "period": {"S": LIMIT_SORT_KEY},
    }
    response = client.get_item(TableName=QUOTAS_TABLE, Key=key)
    if "Item" not in response:
        return 0
    item = response["Item"]
    if "limit_micro_usd" not in item:
        return 0
    return int(item["limit_micro_usd"]["N"])


# 已用量一個月一筆；這個月還沒有紀錄就是 0，換月不用任何人動手
def read_used(client: BaseClient, user_id: str, period: str) -> int:
    """Return what the user has spent in the given period, or 0 when there is no record."""
    key = {
        "user_id": {"S": user_id},
        "period": {"S": period},
    }
    response = client.get_item(TableName=QUOTAS_TABLE, Key=key)
    if "Item" not in response:
        return 0
    item = response["Item"]
    if "used_micro_usd" not in item:
        return 0
    return int(item["used_micro_usd"]["N"])