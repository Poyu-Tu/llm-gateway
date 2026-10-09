"""Tests for the monthly quota check on POST /v1/chat."""

import json
from datetime import datetime, timezone

import pytest

from app.db import QUOTAS_TABLE
from app.main import app, get_now, get_quota
from tests.test_chat_auth import TEST_KEY, make_auth_test_client

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration

# 固定的「現在」：UTC 10/31 15:59 = 台北 10/31 23:59，屬於 2026-10，離下個月剛好 60 秒
FIXED_NOW = datetime(2026, 10, 31, 15, 59, tzinfo=timezone.utc)

# 每個請求都帶 alice 的有效 Key
HEADERS = {"Authorization": "Bearer " + TEST_KEY}


# 測試道具：設定 alice 的每月額度（使用者層級的那一筆）
def put_limit(dynamodb, limit):
    item = {
        "user_id": {"S": "alice"},
        "period": {"S": "limit"},
        "limit_micro_usd": {"N": str(limit)},
    }
    dynamodb.put_item(TableName=QUOTAS_TABLE, Item=item)


# 測試道具：設定 alice 在某個月的已用量
def put_used(dynamodb, period, used):
    item = {
        "user_id": {"S": "alice"},
        "period": {"S": period},
        "used_micro_usd": {"N": str(used)},
    }
    dynamodb.put_item(TableName=QUOTAS_TABLE, Item=item)


# 測試道具：驗證與額度都走真的；只把「現在」固定住
def make_quota_test_client(tmp_path, dynamodb):
    """Like the auth test client, but with the real quota check and a fixed clock."""
    client, completions, audit_path = make_auth_test_client(tmp_path, dynamodb)
    app.dependency_overrides.pop(get_quota)
    app.dependency_overrides[get_now] = lambda: FIXED_NOW
    return client, completions, audit_path


# 還沒用完就放行：已用 999、額度 1000
def test_chat_allows_request_under_quota(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, "2026-10", 999)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200


# M2 驗收條件（S02）：額度用完回 429，告訴對方何時恢復，而且不碰模型
def test_chat_blocks_request_at_quota(tmp_path, dynamodb):
    client, completions, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, "2026-10", 1000)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 429
    assert response.json() == {"detail": "Monthly quota exceeded"}
    assert response.headers["Retry-After"] == "60"
    assert completions.last_request is None


# 被額度擋下的請求照樣寫稽核：查得到誰在額度用完後還一直送；個資類別照記、內容不留
def test_chat_audits_request_blocked_by_quota(tmp_path, dynamodb):
    client, _, audit_path = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, "2026-10", 1000)

    response = client.post("/v1/chat", json={"message": "My ID is A123456780 thanks"}, headers=HEADERS)

    text = audit_path.read_text(encoding="utf-8")
    record = json.loads(text)
    assert response.status_code == 429
    assert record["status"] == "quota_exceeded"
    assert record["pii_types"] == ["TW_ID"]
    assert "model" not in record
    assert "A123456780" not in text


# 沒有額度那一筆就是額度 0：沒設定好的帳號一次都不能用
def test_chat_blocks_user_without_limit(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 429


# 額度明確設成 0 也是一次都不能用，不是沒有上限
def test_chat_treats_zero_limit_as_strict(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 0)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 429


# 這個月還沒有已用量的紀錄就是已用 0：換月之後不用任何人動手就能用
def test_chat_allows_user_without_usage_this_month(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200


# 上個月用爆了不影響這個月：已用量照台北時間的月份分開算
def test_chat_ignores_usage_from_another_month(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, "2026-09", 5000)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200


# M2 驗收條件（S03）：額度讀不到時不放行，回 503；不碰模型、不寫稽核
def test_chat_returns_503_when_quota_cannot_be_read(tmp_path, dynamodb):
    client, completions, audit_path = make_quota_test_client(tmp_path, dynamodb)
    dynamodb.delete_table(TableName=QUOTAS_TABLE)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}
    assert completions.last_request is None
    assert not audit_path.exists()


# 被額度擋下的請求也要記是誰：用完之後還一直送的人，要查得到
def test_chat_blocked_request_audit_records_user_id(tmp_path, dynamodb):
    client, _, audit_path = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, "2026-10", 1000)

    client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert record["status"] == "quota_exceeded"
    assert record["user_id"] == "alice"