"""End-to-end test: the event the Gateway sends is what the Worker records."""

import pytest

from app.db import AUDIT_TABLE
from app.main import app, get_queue_url, get_sqs
from app.quota import read_used
from tests.fakes import FAKE_QUEUE_URL, FakeSqs
from tests.test_audit_store import read_raw_item, to_python
from tests.test_chat_audit_store import make_real_audit_test_client
from tests.test_chat_quota import HEADERS
from worker.handler import process_message

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration

# 假的模型回報輸入 13、輸出 11 個 token；照 gpt-6-luna 的單價進位成 7 micro-USD
COST = 7

# 測試裡的「現在」固定在台北 2026-10（見 test_chat_quota.py 的 FIXED_NOW）
PERIOD = "2026-10"


# 驗證、額度、資料庫都走真的；SQS 是會收信的替身，佇列網址換成假的（等於雲端有設定佇列）
def make_e2e_test_client(tmp_path, dynamodb):
    """Return a client that sends charge events to a fake SQS, plus that fake SQS."""
    client, _ = make_real_audit_test_client(tmp_path, dynamodb)
    sqs = FakeSqs()
    app.dependency_overrides[get_sqs] = lambda: sqs
    app.dependency_overrides[get_queue_url] = lambda: FAKE_QUEUE_URL
    return client, sqs


# 整條路：Gateway 送出信封時還沒扣錢、還沒有稽核；把同一封交給 Worker，三本帳才寫好
def test_worker_records_the_event_the_gateway_sent(tmp_path, dynamodb):
    client, sqs = make_e2e_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    assert response.status_code == 200
    assert read_used(dynamodb, "alice", PERIOD) == 0
    assert dynamodb.scan(TableName=AUDIT_TABLE)["Items"] == []

    assert process_message(dynamodb, sqs.sent[0]["MessageBody"]) is True

    assert read_used(dynamodb, "alice", PERIOD) == COST
    record = to_python(read_raw_item(dynamodb, response.json()["request_id"]))
    assert record["status"] == "ok"
    assert record["charged"] is True


# 兩條路寫出來的 audit 長得一樣：Worker 那條（送 SQS）和 Gateway 備援那條（disabled）欄位完全相同
def test_worker_and_fallback_write_the_same_audit_fields(tmp_path, dynamodb):
    client, sqs = make_e2e_test_client(tmp_path, dynamodb)
    via_worker = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)
    process_message(dynamodb, sqs.sent[0]["MessageBody"])
    app.dependency_overrides[get_queue_url] = lambda: None
    via_fallback = client.post("/v1/chat", json={"message": "Say hi"}, headers=HEADERS)

    worker_record = to_python(read_raw_item(dynamodb, via_worker.json()["request_id"]))
    fallback_record = to_python(read_raw_item(dynamodb, via_fallback.json()["request_id"]))
    assert len(sqs.sent) == 1
    assert sorted(worker_record) == sorted(fallback_record)
