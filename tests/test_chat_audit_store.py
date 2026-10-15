"""Tests for POST /v1/chat with the real audit writer (DynamoDB, then the log line)."""

import json

import pytest
from botocore.exceptions import ClientError

from app.db import AUDIT_TABLE
from app.main import app, get_audit_writer, get_dynamodb
from tests.test_audit_store import read_raw_item, to_python
from tests.test_chat_quota import HEADERS, make_quota_test_client, put_limit, put_used

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration

# 假的模型回報輸入 13、輸出 11 個 token；照 gpt-6-luna 的單價進位成 7 micro-USD
COST = 7

# 測試裡的「現在」固定在台北 2026-10（見 test_chat_quota.py 的 FIXED_NOW）
PERIOD = "2026-10"


# 測試道具：讀、扣額度照常，只有寫稽核（put_item）被拒絕
class AuditWriteFailsDynamoDB:
    """Wraps a real client: everything passes through except put_item."""

    def __init__(self, real):
        self.real = real

    def get_item(self, **kwargs):
        return self.real.get_item(**kwargs)

    def update_item(self, **kwargs):
        return self.real.update_item(**kwargs)

    def put_item(self, **kwargs):
        error = {"Error": {"Code": "InternalServerError", "Message": "boom"}}
        raise ClientError(error, "PutItem")


# 測試道具：模型回答那幾秒資料庫出問題，扣額度和寫稽核都失敗（最典型的情況）
# 第一次寫入（花錢前的「加 0」）成功，之後的寫入都失敗
class FailsAfterFirstWriteDynamoDB(AuditWriteFailsDynamoDB):
    """Like AuditWriteFailsDynamoDB, but only the first update_item passes through."""

    def __init__(self, real):
        super().__init__(real)
        self.updates = 0

    def update_item(self, **kwargs):
        self.updates = self.updates + 1
        if self.updates > 1:
            error = {"Error": {"Code": "InternalServerError", "Message": "boom"}}
            raise ClientError(error, "UpdateItem")
        return self.real.update_item(**kwargs)


# 測試道具：驗證、額度、稽核都走真的；只有模型是假的
def make_real_audit_test_client(tmp_path, dynamodb):
    """Like the quota test client, but audit records go to the real audit table."""
    client, completions, _ = make_quota_test_client(tmp_path, dynamodb)
    app.dependency_overrides.pop(get_audit_writer)
    put_limit(dynamodb, 1000)
    put_used(dynamodb, PERIOD, 0)
    return client, completions


# 成功的請求：稽核寫進 audit 表，用回應裡的 request_id 查得到
def test_chat_writes_the_audit_record_to_the_audit_table(tmp_path, dynamodb):
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Mail amy@example.com"}, headers=HEADERS)

    assert response.status_code == 200
    record = to_python(read_raw_item(dynamodb, response.json()["request_id"]))
    assert record["user_id"] == "alice"
    assert record["status"] == "ok"
    assert record["cost_micro_usd"] == COST
    assert record["charged"] is True
    assert record["pii_types"] == ["EMAIL"]
    # 讀回來的數字是 Decimal，json.dumps 轉不了，所以用 str() 檢查
    assert "amy@example.com" not in str(record)


# 被額度擋下的請求：稽核同樣寫進 audit 表
def test_chat_writes_the_blocked_request_to_the_audit_table(tmp_path, dynamodb):
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)
    put_used(dynamodb, PERIOD, 1000)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 429
    items = dynamodb.scan(TableName=AUDIT_TABLE)["Items"]
    assert len(items) == 1
    assert to_python(items[0])["status"] == "quota_exceeded"


# 稽核寫不進去：回答照給（錢已經付了），只多印一行日誌，單號和回應對得上
def test_chat_still_answers_when_the_audit_write_fails(tmp_path, dynamodb, capsys):
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)
    app.dependency_overrides[get_dynamodb] = lambda: AuditWriteFailsDynamoDB(dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["reply"] == "Hi there"
    entry = json.loads(capsys.readouterr().err)
    assert entry["event"] == "audit_write_failed"
    assert entry["request_id"] == response.json()["request_id"]
    assert entry["charged"] is True


# 稽核寫不進去：429 照樣是 429、照樣附 Retry-After，日誌記下是被擋的請求
def test_chat_still_returns_429_when_the_audit_write_fails(tmp_path, dynamodb, capsys):
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)
    put_used(dynamodb, PERIOD, 1000)
    app.dependency_overrides[get_dynamodb] = lambda: AuditWriteFailsDynamoDB(dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    entry = json.loads(capsys.readouterr().err)
    assert entry["status"] == "quota_exceeded"


# 最典型的情況：扣額度和寫稽核一起失敗。回答照給，日誌記下「花了多少、沒扣到」，事後才補得回來
def test_chat_logs_the_uncharged_cost_when_charging_and_audit_both_fail(tmp_path, dynamodb, capsys):
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)
    app.dependency_overrides[get_dynamodb] = lambda: FailsAfterFirstWriteDynamoDB(dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    entry = json.loads(capsys.readouterr().err)
    assert entry["cost_micro_usd"] == COST
    assert entry["charged"] is False
