"""Tests for reading quota records from DynamoDB."""

import pytest

from app.db import QUOTAS_TABLE
from app.quota import read_limit, read_used
from scripts.create_tables import create_tables

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration


# 測試道具：往 quotas 放一筆；field 是欄位名，value 是整數
def put_quota_row(client, user_id, period, field, value):
    item = {
        "user_id": {"S": user_id},
        "period": {"S": period},
        field: {"N": str(value)},
    }
    client.put_item(TableName=QUOTAS_TABLE, Item=item)


# 額度那一筆的排序鍵直接寫字串 "limit"：常數的值打錯才抓得到；回傳要是整數，不是帶引號的字串
def test_read_limit_returns_stored_limit_as_int(dynamodb):
    create_tables(dynamodb)
    put_quota_row(dynamodb, "alice", "limit", "limit_micro_usd", 1000)

    result = read_limit(dynamodb, "alice")

    assert result == 1000


# 沒有額度那一筆就當成額度 0：沒設定好的帳號不能變成沒有上限
def test_read_limit_returns_zero_without_limit_row(dynamodb):
    create_tables(dynamodb)
    put_quota_row(dynamodb, "bob", "limit", "limit_micro_usd", 1000)

    result = read_limit(dynamodb, "alice")

    assert result == 0


# 只有當月已用量、沒有額度那一筆時也是 0：不能把別筆紀錄誤當成額度
def test_read_limit_ignores_monthly_rows(dynamodb):
    create_tables(dynamodb)
    put_quota_row(dynamodb, "alice", "2026-10", "used_micro_usd", 500)

    result = read_limit(dynamodb, "alice")

    assert result == 0


# 讀得到當月的已用量，而且是整數
def test_read_used_returns_stored_usage_as_int(dynamodb):
    create_tables(dynamodb)
    put_quota_row(dynamodb, "alice", "2026-10", "used_micro_usd", 250)

    result = read_used(dynamodb, "alice", "2026-10")

    assert result == 250


# 這個月還沒有紀錄就是已用 0：換月不用任何人動手
def test_read_used_returns_zero_without_row(dynamodb):
    create_tables(dynamodb)

    result = read_used(dynamodb, "alice", "2026-10")

    assert result == 0


# 上個月的用量不能算進這個月
def test_read_used_reads_only_the_given_period(dynamodb):
    create_tables(dynamodb)
    put_quota_row(dynamodb, "alice", "2026-09", "used_micro_usd", 5000)

    result = read_used(dynamodb, "alice", "2026-10")

    assert result == 0