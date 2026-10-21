"""Tests for the SQS path on POST /v1/chat: the paid request goes out as a charge event, not as an audit write."""

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

import app.main
from app.events import parse_event
from app.main import app as gateway
from app.main import get_audit_writer, get_client, get_dynamodb, get_hmac_key, get_now, get_queue_url, get_quota, get_sqs, get_user_id, log_queue_mode
from tests.fakes import FAKE_QUEUE_URL, FakeDynamoDB, FakeSqs, make_fake_client, make_file_audit_writer

# 台北 2026-10-31 23:59（UTC 15:59）：還是 10 月
END_OF_OCTOBER = datetime(2026, 10, 31, 15, 59, tzinfo=timezone.utc)
# 台北 2026-11-01 00:00（UTC 10/31 16:00）：UTC 還是 10 月，台北已經是 11 月
START_OF_NOVEMBER = datetime(2026, 10, 31, 16, 0, tzinfo=timezone.utc)


# 每個測試跑完都把換掉的領用窗口還原，避免影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    gateway.dependency_overrides.clear()


# 不用 Docker：模型、資料庫、SQS 都是假的；佇列網址換成假的，等於雲端上「有設定佇列」的情況
def make_sqs_test_client(tmp_path, now=END_OF_OCTOBER, error=None):
    """Swap every dependency for a fake and return what tests need."""
    fake_client, _ = make_fake_client(error=error)
    audit_path = tmp_path / "audit.jsonl"
    database = FakeDynamoDB()
    sqs = FakeSqs()
    gateway.dependency_overrides[get_client] = lambda: fake_client
    gateway.dependency_overrides[get_hmac_key] = lambda: b"test-key"
    gateway.dependency_overrides[get_audit_writer] = lambda: make_file_audit_writer(audit_path)
    gateway.dependency_overrides[get_user_id] = lambda: "alice"
    gateway.dependency_overrides[get_quota] = lambda: (1_000_000, 0)
    gateway.dependency_overrides[get_now] = lambda: now
    gateway.dependency_overrides[get_dynamodb] = lambda: database
    gateway.dependency_overrides[get_sqs] = lambda: sqs
    gateway.dependency_overrides[get_queue_url] = lambda: FAKE_QUEUE_URL
    return TestClient(gateway), audit_path, database, sqs


# 成功的請求送出剛好一封信封：送到設定的佇列；裡面的紀錄就是這次請求、帶著成本；charged 由寫帳的人加，Gateway 不加
def test_chat_sends_one_charge_event_for_a_paid_request(tmp_path):
    client, _, _, sqs = make_sqs_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert len(sqs.sent) == 1
    assert sqs.sent[0]["QueueUrl"] == FAKE_QUEUE_URL
    record, period = parse_event(sqs.sent[0]["MessageBody"])
    assert record["request_id"] == response.json()["request_id"]
    assert record["status"] == "ok"
    assert record["cost_micro_usd"] == 7
    assert "charged" not in record
    assert period == "2026-10"


# 信封上的月份照台北時間：UTC 還是 10/31，台北已經是 11/1，就算 11 月（Worker 照著記，不重算）
def test_chat_puts_the_taipei_month_on_the_event(tmp_path):
    client, _, _, sqs = make_sqs_test_client(tmp_path, now=START_OF_NOVEMBER)

    client.post("/v1/chat", json={"message": "Say hi"})

    _, period = parse_event(sqs.sent[0]["MessageBody"])
    assert period == "2026-11"


# 送進 SQS 之後，Gateway 自己不寫稽核、不扣錢：資料庫只收到花錢前那一次「加 0」
def test_chat_leaves_audit_and_charge_to_the_worker_when_the_event_is_sent(tmp_path):
    client, audit_path, database, _ = make_sqs_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert not audit_path.exists()
    amounts = [update["ExpressionAttributeValues"][":amount"]["N"] for update in database.updates]
    assert amounts == ["0"]


# 沒花錢的請求不送 SQS：模型失敗回 502，Gateway 照樣自己寫稽核
def test_chat_does_not_send_an_event_when_the_model_fails(tmp_path):
    client, audit_path, _, sqs = make_sqs_test_client(tmp_path, error=OpenAIError("boom"))

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 502
    assert sqs.sent == []
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert record["status"] == "error"


# 啟動時那一行只說模式，不印佇列網址（網址裡有 AWS 帳號 ID）
def test_log_queue_mode_names_the_mode_without_the_url(capsys):
    log_queue_mode(None)
    log_queue_mode(FAKE_QUEUE_URL)

    lines = capsys.readouterr().err.splitlines()
    assert json.loads(lines[0]) == {"event": "charge_queue_mode", "mode": "disabled"}
    assert json.loads(lines[1]) == {"event": "charge_queue_mode", "mode": "sqs"}
    assert FAKE_QUEUE_URL not in lines[1]


# disabled 時不建 SQS 連線：boto3 一建連線就去找 AWS 憑證，本機登入方式不同時會直接報錯（10/22 全部測試時踩到）
def test_get_sqs_builds_no_client_when_disabled():
    assert app.main.CHARGE_QUEUE_URL is None
    app.main.get_sqs.cache_clear()

    assert app.main.get_sqs() is None
