"""Tests for POST /v1/chat, using a fake OpenAI client."""

import json

import pytest
from openai import OpenAIError
from fastapi.testclient import TestClient

from app.main import app, get_audit_writer, get_client, get_dynamodb, get_hmac_key, get_queue_url, get_quota, get_sqs, get_user_id
from tests.fakes import FAKE_QUEUE_URL, FakeDynamoDB, FakeSqs, make_fake_client, make_file_audit_writer, read_sent_record


# 每個測試跑完都把換掉的領用窗口還原：這個檔把記帳換成假的 SQS，不還原的話別的測試檔會跟著送進假佇列
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    app.dependency_overrides.clear()


# 把領用窗口換成假的，回傳：測試用戶端、筆記本、稽核檔位置、假的 SQS
# 成功那一筆裝進信封送假的 SQS（讀信封檢查）；沒花錢的失敗紀錄照樣寫進稽核檔
def make_test_client(tmp_path, error=None):
    """Swap the real dependencies for fakes and return what tests need."""
    fake_client, completions = make_fake_client(error=error)
    audit_path = tmp_path / "audit.jsonl"
    app.dependency_overrides[get_client] = lambda: fake_client
    app.dependency_overrides[get_hmac_key] = lambda: b"test-key"
    app.dependency_overrides[get_audit_writer] = lambda: make_file_audit_writer(audit_path)
    # 驗票口換成直接放行：這個檔測的是遮罩與稽核，驗證另外在 test_chat_auth.py 測
    app.dependency_overrides[get_user_id] = lambda: "alice"
    app.dependency_overrides[get_quota] = lambda: (1_000_000, 0)
    app.dependency_overrides[get_dynamodb] = lambda: FakeDynamoDB()
    sqs = FakeSqs()
    app.dependency_overrides[get_sqs] = lambda: sqs
    app.dependency_overrides[get_queue_url] = lambda: FAKE_QUEUE_URL
    return TestClient(app), completions, audit_path, sqs


# 送出訊息要拿到回答和模型名稱
def test_chat_returns_reply(tmp_path):
    client, _, _, _ = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert response.json()["reply"] == "Hi there"
    assert response.json()["model"] == "gpt-6-luna"


# M1 驗收條件：稽核紀錄有指紋和摘要，但找不到原文和回答
def test_chat_audit_has_hash_and_summary_but_not_the_prompt(tmp_path):
    """The audit log must never contain the prompt or the reply."""
    client, _, _, sqs = make_test_client(tmp_path)
    message = "Please compare these two database options for our team and explain why"

    client.post("/v1/chat", json={"message": message})

    text = sqs.sent[-1]["MessageBody"]
    record = read_sent_record(sqs)
    assert len(record["prompt_hash"]) == 64
    assert record["summary"] == message[:50]
    assert message not in text
    assert "Hi there" not in text


# 空白訊息要被擋掉
def test_chat_rejects_empty_message(tmp_path):
    client, _, _, _ = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": ""})

    assert response.status_code == 422


# OpenAI 出錯時：回 502、稽核記一筆失敗，而且不洩漏錯誤細節
def test_chat_returns_502_and_audits_when_model_fails(tmp_path):
    client, _, audit_path, _ = make_test_client(tmp_path, error=OpenAIError("boom"))

    response = client.post("/v1/chat", json={"message": "Say hi"})

    text = audit_path.read_text(encoding="utf-8")
    record = json.loads(text)
    assert response.status_code == 502
    assert record["status"] == "error"
    assert record["error_type"] == "OpenAIError"
    assert "boom" not in text
    assert "boom" not in response.text


# M2 驗收條件：送給模型的內容已遮罩，找不到原本的個資
def test_chat_sends_masked_message_to_model(tmp_path):
    client, completions, _, _ = make_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "My ID is A123456780 thanks"})

    sent = completions.last_request["messages"][0]["content"]
    assert sent == "My ID is [TW_ID] thanks"


# M2 驗收條件：稽核紀錄裡也找不到個資，摘要是遮罩後的
def test_chat_audit_does_not_contain_personal_data(tmp_path):
    client, _, _, sqs = make_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "My ID is A123456780 thanks"})

    text = sqs.sent[-1]["MessageBody"]
    record = read_sent_record(sqs)
    assert "A123456780" not in text
    assert record["summary"] == "My ID is [TW_ID] thanks"


# M2 驗收條件（S04）：稽核記「偵測到哪幾類個資」，而且紀錄裡找不到個資本身
def test_chat_audit_records_pii_types(tmp_path):
    client, _, _, sqs = make_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "My ID is A123456780 call 0912345678"})

    text = sqs.sent[-1]["MessageBody"]
    record = read_sent_record(sqs)
    assert record["pii_types"] == ["PHONE", "TW_ID"]
    assert "A123456780" not in text
    assert "0912345678" not in text


# 沒有個資時欄位仍然存在、值是空清單：「檢查過沒找到」和「沒檢查」要分得出來
def test_chat_audit_records_empty_pii_types_without_personal_data(tmp_path):
    client, _, _, sqs = make_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "Say hi"})

    record = read_sent_record(sqs)
    assert record["pii_types"] == []


# 呼叫模型失敗時，個資一樣進來過，稽核仍要記類別，而且不能留下個資本身
def test_chat_error_audit_still_records_pii_types(tmp_path):
    client, _, audit_path, _ = make_test_client(tmp_path, error=OpenAIError("boom"))

    client.post("/v1/chat", json={"message": "My ID is A123456780 thanks"})

    text = audit_path.read_text(encoding="utf-8")
    record = json.loads(text)
    assert record["status"] == "error"
    assert record["pii_types"] == ["TW_ID"]
    assert "A123456780" not in text


# 稽核要記「是誰送的」：沒有這一欄，就查不出每個人各用了多少
def test_chat_audit_records_user_id(tmp_path):
    client, _, _, sqs = make_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "Say hi"})

    record = read_sent_record(sqs)
    assert record["user_id"] == "alice"
