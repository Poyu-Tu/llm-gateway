"""Tests for the /metrics endpoint and the counters POST /v1/chat updates (M6)."""

import pytest

from app.main import app as gateway
from app.main import get_quota
from app.metrics import REGISTRY
from tests.fakes import make_rate_limit_error
from tests.test_chat_fallback import STRONG_MESSAGE, make_fallback_test_client


# 每個測試跑完都把換掉的領用窗口還原，避免影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    gateway.dependency_overrides.clear()


# 計數器是整個程式共用的，別的測試也會加；所以一律比「這次前後差多少」
def read(name, **labels):
    """Return the current value of one sample, or 0 when it does not exist yet."""
    value = REGISTRY.get_sample_value(name, labels)
    if value is None:
        return 0
    return value


# /metrics 回 Prometheus 的文字格式，五個指標的名字都在
def test_metrics_lists_the_five_metrics(tmp_path):
    client, _, _, _, _ = make_fallback_test_client(tmp_path)

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    for name in ["llm_requests_total", "llm_tokens_total", "llm_cost_usd_total", "llm_request_duration_seconds", "llm_rate_limit_rejected_total"]:
        assert name in response.text


# 成功的一題：請求數 +1、輸入 13 和輸出 11 個 token、成本 7 micro-USD（換成美元是 0.000007）、延遲記一筆
def test_successful_chat_updates_requests_tokens_cost_and_duration(tmp_path):
    client, _, _, _, _ = make_fallback_test_client(tmp_path)
    before = {
        "requests": read("llm_requests_total", user="alice", model="small", status="ok"),
        "input": read("llm_tokens_total", user="alice", model="small", kind="input"),
        "output": read("llm_tokens_total", user="alice", model="small", kind="output"),
        "cost": read("llm_cost_usd_total", user="alice", model="small"),
        "duration": read("llm_request_duration_seconds_count", status="ok"),
    }

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert read("llm_requests_total", user="alice", model="small", status="ok") == before["requests"] + 1
    assert read("llm_tokens_total", user="alice", model="small", kind="input") == before["input"] + 13
    assert read("llm_tokens_total", user="alice", model="small", kind="output") == before["output"] + 11
    assert read("llm_cost_usd_total", user="alice", model="small") == pytest.approx(before["cost"] + 0.000007)
    assert read("llm_request_duration_seconds_count", status="ok") == before["duration"] + 1


# 額度用完被擋：請求數記在 status=quota_exceeded（還沒選模型，model 是 none），被擋次數 reason=quota +1，不記 token 與成本
def test_quota_block_counts_as_rejected(tmp_path):
    client, _, _, _, _ = make_fallback_test_client(tmp_path)
    gateway.dependency_overrides[get_quota] = lambda: (1000, 1000)
    before_requests = read("llm_requests_total", user="alice", model="none", status="quota_exceeded")
    before_rejected = read("llm_rate_limit_rejected_total", reason="quota")
    before_cost = read("llm_cost_usd_total", user="alice", model="none")

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 429
    assert read("llm_requests_total", user="alice", model="none", status="quota_exceeded") == before_requests + 1
    assert read("llm_rate_limit_rejected_total", reason="quota") == before_rejected + 1
    assert read("llm_cost_usd_total", user="alice", model="none") == before_cost


# 兩顆模型都被供應商限流：請求數記在 status=error、model 是路由選的 big；被擋次數 reason=provider +1
def test_provider_rate_limit_counts_as_rejected(tmp_path):
    errors = {"big": make_rate_limit_error(), "small": make_rate_limit_error()}
    client, _, _, _, _ = make_fallback_test_client(tmp_path, errors=errors)
    before_requests = read("llm_requests_total", user="alice", model="big", status="error")
    before_rejected = read("llm_rate_limit_rejected_total", reason="provider")

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 503
    assert read("llm_requests_total", user="alice", model="big", status="error") == before_requests + 1
    assert read("llm_rate_limit_rejected_total", reason="provider") == before_rejected + 1


# /metrics 只有數字和標籤，不能出現使用者問的內容（D7：應用日誌與監控都不記 prompt）
def test_metrics_never_contain_the_message(tmp_path):
    client, _, _, _, _ = make_fallback_test_client(tmp_path)
    client.post("/v1/chat", json={"message": "my secret plan"})

    response = client.get("/metrics")

    assert "my secret plan" not in response.text
