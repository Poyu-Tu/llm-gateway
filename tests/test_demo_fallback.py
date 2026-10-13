"""Tests for scripts/demo_fallback.py: only the strong model is rate limited, and the Gateway falls back."""

import json

import pytest
from fastapi.testclient import TestClient
from openai import RateLimitError

from app.config import CONFIG_PATH, load_config
from app.main import app as gateway
from app.main import get_audit_path, get_client, get_dynamodb, get_hmac_key, get_quota, get_user_id
from scripts.demo_fallback import SimulatedLimitClient
from tests.fakes import FakeDynamoDB, make_fake_client

ROUTING = load_config(CONFIG_PATH).routing
# 含關鍵字 debug、又不到 300 字：正式規則一定選強模型
STRONG_MESSAGE = "Please debug it"


# 每個測試跑完都把換掉的領用窗口還原，避免影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    gateway.dependency_overrides.clear()


# 問強模型：丟 429，而且沒有真的送出去
def test_strong_model_gets_a_fake_429_and_never_reaches_the_real_client():
    real_client, completions = make_fake_client()
    client = SimulatedLimitClient(real_client)

    with pytest.raises(RateLimitError):
        client.chat.completions.create(model=ROUTING.strong_model, messages=[])

    assert completions.requests == []


# 問便宜模型：原封不動交給真的連線
def test_cheap_model_is_passed_to_the_real_client():
    real_client, completions = make_fake_client()
    client = SimulatedLimitClient(real_client)

    client.chat.completions.create(model=ROUTING.cheap_model, messages=[])

    assert completions.models_called() == [ROUTING.cheap_model]


# 換過重試設定的連線（降級時強模型那一次用的）也一樣被限流
def test_connection_with_other_retry_setting_is_also_rate_limited():
    real_client, _ = make_fake_client()
    client = SimulatedLimitClient(real_client).with_options(max_retries=0)

    with pytest.raises(RateLimitError):
        client.chat.completions.create(model=ROUTING.strong_model, messages=[])


# 整條路：難題路由到強模型 → 假 429 → 降級到便宜模型 → 使用者拿到 200，稽核記下降級
def test_gateway_falls_back_to_the_cheap_model(tmp_path):
    real_client, completions = make_fake_client()
    audit_path = tmp_path / "audit.jsonl"
    gateway.dependency_overrides[get_client] = lambda: SimulatedLimitClient(real_client)
    gateway.dependency_overrides[get_hmac_key] = lambda: b"test-key"
    gateway.dependency_overrides[get_audit_path] = lambda: audit_path
    gateway.dependency_overrides[get_user_id] = lambda: "bob"
    gateway.dependency_overrides[get_quota] = lambda: (1_000_000, 0)
    gateway.dependency_overrides[get_dynamodb] = lambda: FakeDynamoDB()

    response = TestClient(gateway).post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    assert response.json()["model"] == ROUTING.cheap_model
    assert completions.models_called() == [ROUTING.cheap_model]
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert record["routed_model"] == ROUTING.strong_model
    assert record["fallback"] is True
    assert record["fallback_reason"] == "RateLimitError"
