"""Tests for charging usage to the monthly quota on POST /v1/chat."""

import json

import pytest
from botocore.exceptions import ClientError

from app.main import app, get_dynamodb
from app.quota import read_used
from tests.test_chat_quota import HEADERS, make_quota_test_client, put_limit, put_used

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration

# 假的模型每次都回報輸入 13、輸出 11 個 token；照 gpt-6-luna 的單價是 6.8，進位成 7 micro-USD
COST = 7

# 測試裡的「現在」固定在台北 2026-10（見 test_chat_quota.py 的 FIXED_NOW）
PERIOD = "2026-10"


# 測試道具：讀得到、但寫入一律被拒絕的資料庫（例如權限只給了讀）
class ReadOnlyDynamoDB:
    """Wraps a real client: reads pass through, every write is denied."""

    def __init__(self, real):
        self.real = real

    def get_item(self, **kwargs):
        return self.real.get_item(**kwargs)

    def update_item(self, **kwargs):
        error = {"Error": {"Code": "AccessDeniedException", "Message": "denied"}}
        raise ClientError(error, "UpdateItem")


# 測試道具：第一次寫入成功、之後的寫入都失敗（模型回答的那幾秒資料庫剛好出問題）
class FailsAfterFirstWriteDynamoDB:
    """Wraps a real client: the first write passes through, later writes fail."""

    def __init__(self, real):
        self.real = real
        self.writes = 0

    def get_item(self, **kwargs):
        return self.real.get_item(**kwargs)

    def update_item(self, **kwargs):
        self.writes = self.writes + 1
        if self.writes > 1:
            error = {"Error": {"Code": "InternalServerError", "Message": "boom"}}
            raise ClientError(error, "UpdateItem")
        return self.real.update_item(**kwargs)


# 成功的請求要把這次的成本加到當月已用量上
def test_chat_adds_cost_to_monthly_usage(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, PERIOD, 100)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    assert read_used(dynamodb, "alice", PERIOD) == 100 + COST


# 這個月的第一次請求：原本沒有紀錄，扣完之後要有，而且金額正確
def test_chat_creates_usage_record_on_first_request(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)

    client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert read_used(dynamodb, "alice", PERIOD) == COST


# M2 驗收條件（S02）：連續呼叫，用量一路累加，用完之後被擋下
def test_chat_blocks_after_usage_reaches_limit(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 2 * COST)

    first = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)
    second = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)
    third = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert read_used(dynamodb, "alice", PERIOD) == 2 * COST


# 被額度擋下的請求沒有呼叫模型，不能扣錢
def test_chat_does_not_charge_blocked_request(tmp_path, dynamodb):
    client, _, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, PERIOD, 1000)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 429
    assert read_used(dynamodb, "alice", PERIOD) == 1000


# 成功的請求在稽核留下成本，並註明有扣到
def test_chat_audit_records_cost_and_charge(tmp_path, dynamodb):
    client, _, audit_path = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)

    client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert record["status"] == "ok"
    assert record["cost_micro_usd"] == COST
    assert record["charged"] is True


# 寫不進去就不花錢：呼叫模型之前先確認寫得進去，否則回 503，模型沒有被呼叫
def test_chat_returns_503_before_spending_when_usage_cannot_be_written(tmp_path, dynamodb):
    client, completions, _ = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    app.dependency_overrides[get_dynamodb] = lambda: ReadOnlyDynamoDB(dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}
    assert completions.last_request is None


# 模型已經回答、扣款才失敗：回答照給，稽核記下這筆沒扣到的金額，之後可以補收
def test_chat_still_answers_when_charge_fails_after_the_model_replied(tmp_path, dynamodb):
    client, _, audit_path = make_quota_test_client(tmp_path, dynamodb)
    put_limit(dynamodb, 1000)
    flaky = FailsAfterFirstWriteDynamoDB(dynamodb)
    app.dependency_overrides[get_dynamodb] = lambda: flaky

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert response.status_code == 200
    assert response.json()["reply"] == "Hi there"
    assert record["cost_micro_usd"] == COST
    assert record["charged"] is False
    assert read_used(dynamodb, "alice", PERIOD) == 0
