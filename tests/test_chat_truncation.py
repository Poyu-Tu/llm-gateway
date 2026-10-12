"""Tests for truncated answers on POST /v1/chat: the audit log must show why the answer ended."""

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from app.main import app as gateway
from app.main import get_audit_path, get_client, get_config, get_dynamodb, get_hmac_key, get_quota, get_user_id
from tests.fakes import FakeDynamoDB, make_fake_client
from tests.test_chat_routing import TEST_CONFIG, read_audit

# 含關鍵字 debug、又不到 18 個字：路由一定選強模型 big
STRONG_MESSAGE = "Please debug it"


# 每個測試跑完都把換掉的領用窗口還原，避免影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    gateway.dependency_overrides.clear()


# 和 test_chat_fallback.py 的做法一樣，只是可以指定假模型的回答內容、結束原因與錯誤
def make_truncation_test_client(tmp_path, content="Hi there", finish_reason="stop", error=None):
    """Swap the real dependencies for fakes and return what tests need."""
    fake_client, completions = make_fake_client(content=content, error=error, finish_reason=finish_reason)
    audit_path = tmp_path / "audit.jsonl"
    database = FakeDynamoDB()
    gateway.dependency_overrides[get_client] = lambda: fake_client
    gateway.dependency_overrides[get_hmac_key] = lambda: b"test-key"
    gateway.dependency_overrides[get_audit_path] = lambda: audit_path
    gateway.dependency_overrides[get_user_id] = lambda: "alice"
    gateway.dependency_overrides[get_quota] = lambda: (1_000_000, 0)
    gateway.dependency_overrides[get_dynamodb] = lambda: database
    gateway.dependency_overrides[get_config] = lambda: TEST_CONFIG
    return TestClient(gateway), completions, audit_path, database


# 依序列出資料庫收到的每一筆加總金額（第一筆是呼叫模型前的「加 0」）
def charged_amounts(database):
    """Return the amount of every update the database received, in order."""
    amounts = []
    for update in database.updates:
        amounts.append(update["ExpressionAttributeValues"][":amount"]["N"])
    return amounts


# 正常說完的回答：稽核記 stop
def test_chat_audits_the_finish_reason_of_a_normal_answer(tmp_path):
    client, _, audit_path, _ = make_truncation_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    assert read_audit(audit_path)["finish_reason"] == "stop"


# 被輸出上限截斷、回答是空的（10/12 強模型實測的樣子）：使用者照樣拿到 200，稽核看得出是截斷
def test_chat_audits_a_truncated_answer(tmp_path):
    client, _, audit_path, _ = make_truncation_test_client(tmp_path, content="", finish_reason="length")

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    assert response.json()["reply"] == ""
    assert read_audit(audit_path)["finish_reason"] == "length"


# 截斷的回答照樣計費（10/12 定案：先只記錄，不改行為）；強模型 13 / 11 個 token 是 136
def test_chat_still_charges_a_truncated_answer(tmp_path):
    client, _, audit_path, database = make_truncation_test_client(tmp_path, content="", finish_reason="length")

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    assert read_audit(audit_path)["cost_micro_usd"] == 136
    assert charged_amounts(database) == ["0", "136"]


# 沒拿到回答的失敗紀錄沒有結束原因這一欄
def test_chat_audits_no_finish_reason_when_the_model_fails(tmp_path):
    client, _, audit_path, _ = make_truncation_test_client(tmp_path, error=OpenAIError("boom"))

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 502
    assert "finish_reason" not in read_audit(audit_path)
