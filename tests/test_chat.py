"""Tests for POST /v1/chat, using a fake OpenAI client."""

import json

from openai import OpenAIError
from fastapi.testclient import TestClient

from app.main import app, get_audit_path, get_client, get_hmac_key
from tests.fakes import make_fake_client


# 把三個領用窗口換成假的，回傳：測試用戶端、筆記本、稽核檔位置
def make_test_client(tmp_path, error=None):
    """Swap the real dependencies for fakes and return what tests need."""
    fake_client, completions = make_fake_client(error=error)
    audit_path = tmp_path / "audit.jsonl"
    app.dependency_overrides[get_client] = lambda: fake_client
    app.dependency_overrides[get_hmac_key] = lambda: b"test-key"
    app.dependency_overrides[get_audit_path] = lambda: audit_path
    return TestClient(app), completions, audit_path


# 送出訊息要拿到回答和模型名稱
def test_chat_returns_reply(tmp_path):
    client, _, _ = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert response.json()["reply"] == "Hi there"
    assert response.json()["model"] == "gpt-6-luna"


# M1 驗收條件：稽核紀錄有指紋和摘要，但找不到原文和回答
def test_chat_audit_has_hash_and_summary_but_not_the_prompt(tmp_path):
    """The audit log must never contain the prompt or the reply."""
    client, _, audit_path = make_test_client(tmp_path)
    message = "Please compare these two database options for our team and explain why"

    client.post("/v1/chat", json={"message": message})

    text = audit_path.read_text(encoding="utf-8")
    record = json.loads(text)
    assert len(record["prompt_hash"]) == 64
    assert record["summary"] == message[:50]
    assert message not in text
    assert "Hi there" not in text


# 空白訊息要被擋掉
def test_chat_rejects_empty_message(tmp_path):
    client, _, _ = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": ""})

    assert response.status_code == 422


# OpenAI 出錯時：回 502、稽核記一筆失敗，而且不洩漏錯誤細節
def test_chat_returns_502_and_audits_when_model_fails(tmp_path):
    client, _, audit_path = make_test_client(tmp_path, error=OpenAIError("boom"))

    response = client.post("/v1/chat", json={"message": "Say hi"})

    text = audit_path.read_text(encoding="utf-8")
    record = json.loads(text)
    assert response.status_code == 502
    assert record["status"] == "error"
    assert record["error_type"] == "OpenAIError"
    assert "boom" not in text
    assert "boom" not in response.text