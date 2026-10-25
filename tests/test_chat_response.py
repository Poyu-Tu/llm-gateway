"""Tests for what POST /v1/chat returns to the Demo Console: route, usage, cost and quota."""

import pytest

from app.main import app as gateway
from app.main import get_quota
from tests.fakes import make_rate_limit_error
from tests.test_chat_fallback import STRONG_MESSAGE, make_fallback_test_client


# 每個測試跑完都把換掉的領用窗口還原，避免影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    gateway.dependency_overrides.clear()


# 不到門檻、沒有關鍵字：路由選便宜模型 small；假的模型回報輸入 13、輸出 11，照 small 的單價是 7 micro-USD
SIMPLE_MESSAGE = "Say hi"
CHEAP_COST = 7
STRONG_COST = 136


# 測試道具：額度上限 1000、這個月已經用了 100
def make_client_with_quota(tmp_path, errors=None):
    """Return a test client whose quota is limit 1000, used 100."""
    client, _, _, _, _ = make_fallback_test_client(tmp_path, errors=errors)
    gateway.dependency_overrides[get_quota] = lambda: (1000, 100)
    return client


# M6 Console 要的欄位一次到齊：原本的三個不變，另外加路由、用量、成本、額度
def test_chat_response_shows_route_usage_cost_and_quota(tmp_path):
    client = make_client_with_quota(tmp_path)

    response = client.post("/v1/chat", json={"message": SIMPLE_MESSAGE})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"request_id", "reply", "model", "route", "usage", "cost_micro_usd", "quota"}
    assert body["reply"] == "Hi there"
    assert body["model"] == "small"
    assert body["route"] == {"reason": "default", "fallback": False}
    assert body["usage"] == {"input_tokens": 13, "output_tokens": 11, "reasoning_tokens": 0}
    assert body["cost_micro_usd"] == CHEAP_COST


# 額度回的是「這次之後」的已用：呼叫前讀到的 100 加上這次的 7；不回頭讀資料庫（Worker 可能還沒入帳）
def test_chat_response_quota_includes_this_request(tmp_path):
    client = make_client_with_quota(tmp_path)

    response = client.post("/v1/chat", json={"message": SIMPLE_MESSAGE})

    assert response.json()["quota"] == {"limit_micro_usd": 1000, "used_micro_usd": 100 + CHEAP_COST}


# 含關鍵字：路由理由是 keyword，強模型的成本 136
def test_chat_response_shows_keyword_route_and_strong_cost(tmp_path):
    client = make_client_with_quota(tmp_path)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    body = response.json()
    assert body["model"] == "big"
    assert body["route"] == {"reason": "keyword", "fallback": False}
    assert body["cost_micro_usd"] == STRONG_COST


# 強模型被限流、降級到便宜模型：理由仍是 keyword（路由原本的判斷），fallback 是 True，照便宜的單價算
def test_chat_response_shows_fallback(tmp_path):
    client = make_client_with_quota(tmp_path, errors={"big": make_rate_limit_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    body = response.json()
    assert body["model"] == "small"
    assert body["route"] == {"reason": "keyword", "fallback": True}
    assert body["cost_micro_usd"] == CHEAP_COST
    assert body["quota"]["used_micro_usd"] == 100 + CHEAP_COST
