"""Tests for the fallback when SQS fails on POST /v1/chat: the Gateway records the charge itself."""

import json

import pytest
from botocore.exceptions import ClientError

from app.db import AUDIT_TABLE, USAGE_TABLE
from app.main import app, get_dynamodb, get_queue_url, get_sqs
from app.quota import read_used
from tests.fakes import FAKE_QUEUE_URL, FakeSqs
from tests.test_audit_store import read_raw_item, to_python
from tests.test_chat_audit_store import make_real_audit_test_client
from tests.test_chat_charge import TransactionFailsDynamoDB
from tests.test_chat_quota import HEADERS

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration

# 假的模型回報輸入 13、輸出 11 個 token；照 gpt-6-luna 的單價進位成 7 micro-USD
COST = 7

# 測試裡的「現在」固定在台北 2026-10（見 test_chat_quota.py 的 FIXED_NOW）
PERIOD = "2026-10"


# 測試道具：SQS 送不進去時丟的錯誤（例如 DNS 防火牆擋掉、權限不夠）
def make_sqs_error():
    """Return the error boto3 raises when SendMessage is refused."""
    error = {"Error": {"Code": "AccessDenied", "Message": "denied"}}
    return ClientError(error, "SendMessage")


# 測試道具：交易被取消，而且每一件被擋的原因都是「已經存在」：等於 SQS 其實收到了、Worker 已經記過
class AlreadyRecordedDynamoDB:
    """Wraps a real client: every transaction is cancelled as a duplicate."""

    def __init__(self, real):
        self.real = real

    def get_item(self, **kwargs):
        return self.real.get_item(**kwargs)

    def update_item(self, **kwargs):
        return self.real.update_item(**kwargs)

    def transact_write_items(self, **kwargs):
        error = {
            "Error": {"Code": "TransactionCanceledException", "Message": "cancelled"},
            "CancellationReasons": [
                {"Code": "ConditionalCheckFailed"},
                {"Code": "None"},
                {"Code": "ConditionalCheckFailed"},
            ],
        }
        raise ClientError(error, "TransactWriteItems")


# 驗證、額度、稽核都走真的；佇列網址換成假的（等於雲端有設定佇列），SQS 換成送出就失敗的替身
def make_fallback_charge_test_client(tmp_path, dynamodb):
    """Return a client whose SQS always fails, so the Gateway has to record the charge itself."""
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)
    sqs = FakeSqs(error=make_sqs_error())
    app.dependency_overrides[get_sqs] = lambda: sqs
    app.dependency_overrides[get_queue_url] = lambda: FAKE_QUEUE_URL
    return client


# 讀出 stderr 的每一行 JSON 日誌
def read_log_lines(capsys):
    """Return every JSON line printed to stderr."""
    lines = []
    for line in capsys.readouterr().err.splitlines():
        lines.append(json.loads(line))
    return lines


# SQS 送不進去：Gateway 自己用交易記好三本帳，回答照給；日誌只多一行 charge_queue_failed，不帶摘要與指紋
def test_chat_records_the_charge_itself_when_sqs_fails(tmp_path, dynamodb, capsys):
    client = make_fallback_charge_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    request_id = response.json()["request_id"]
    assert read_used(dynamodb, "alice", PERIOD) == COST
    record = to_python(read_raw_item(dynamodb, request_id))
    assert record["status"] == "ok"
    assert record["charged"] is True
    assert len(dynamodb.scan(TableName=USAGE_TABLE)["Items"]) == 1
    assert read_log_lines(capsys) == [
        {"event": "charge_queue_failed", "request_id": request_id, "error_type": "ClientError"},
    ]


# SQS 送不進去、交易又說「已經記過」：其實佇列收到了、只是回應逾時，Worker 已經記了；帳是對的，回答照給、不印 audit_write_failed
def test_chat_answers_when_the_fallback_finds_the_charge_already_recorded(tmp_path, dynamodb, capsys):
    client = make_fallback_charge_test_client(tmp_path, dynamodb)
    app.dependency_overrides[get_dynamodb] = lambda: AlreadyRecordedDynamoDB(dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    events = [line["event"] for line in read_log_lines(capsys)]
    assert events == ["charge_queue_failed"]


# 兩條都失敗：回答照給（錢已經付了），三本帳都沒寫；日誌先一行 charge_queue_failed，再一行 charge_record_failed（M6 拆出來的事件名，有告警）帶成本與 charged=false
def test_chat_logs_the_uncharged_cost_when_sqs_and_the_fallback_both_fail(tmp_path, dynamodb, capsys):
    client = make_fallback_charge_test_client(tmp_path, dynamodb)
    app.dependency_overrides[get_dynamodb] = lambda: TransactionFailsDynamoDB(dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["reply"] == "Hi there"
    lines = read_log_lines(capsys)
    assert [line["event"] for line in lines] == ["charge_queue_failed", "charge_record_failed"]
    assert lines[1]["request_id"] == response.json()["request_id"]
    assert lines[1]["cost_micro_usd"] == COST
    assert lines[1]["charged"] is False
    assert read_used(dynamodb, "alice", PERIOD) == 0
    assert dynamodb.scan(TableName=AUDIT_TABLE)["Items"] == []


# disabled（本機、測試）：不碰 SQS，直接自己記三本帳，也不印任何一行
def test_chat_records_the_charge_without_touching_sqs_when_disabled(tmp_path, dynamodb, capsys):
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)
    sqs = FakeSqs(error=make_sqs_error())
    app.dependency_overrides[get_sqs] = lambda: sqs
    app.dependency_overrides[get_queue_url] = lambda: None

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    assert sqs.sent == []
    assert read_used(dynamodb, "alice", PERIOD) == COST
    assert to_python(read_raw_item(dynamodb, response.json()["request_id"]))["charged"] is True
    assert capsys.readouterr().err == ""
