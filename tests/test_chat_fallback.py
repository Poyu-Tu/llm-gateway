"""Tests for fallback on POST /v1/chat: what the caller gets, what is charged, and what the audit log says."""

import httpx2
import pytest
from fastapi.testclient import TestClient
from openai import NotFoundError, OpenAIError

from app.main import app as gateway
from app.main import get_audit_path, get_client, get_config, get_dynamodb, get_hmac_key, get_quota, get_user_id
from tests.fakes import FakeDynamoDB, make_fake_client, make_rate_limit_error
from tests.test_chat_routing import BROKEN_CONFIG, TEST_CONFIG, read_audit

# 含關鍵字 debug、又不到 18 個字：路由一定選強模型 big
STRONG_MESSAGE = "Please debug it"


# 每個測試跑完都把換掉的領用窗口還原，避免影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    gateway.dependency_overrides.clear()


# 和 test_chat_routing.py 的 make_routing_test_client 一樣，只是多了 errors：指定哪一顆模型丟哪個錯誤
def make_fallback_test_client(tmp_path, errors=None):
    """Swap the real dependencies for fakes and return what tests need."""
    fake_client, completions = make_fake_client(errors=errors)
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


# 對話入口真的經過 chat_with_fallback：強模型那一次不讓 SDK 重試
def test_chat_turns_off_the_sdk_retry_for_the_strong_model(tmp_path):
    client, completions, _, _ = make_fallback_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    assert completions.retry_settings == [0]


# 便宜模型那一次不另外改重試設定，照連線本身的設定（main.py 的 OPENAI_MAX_RETRIES，目前是 0）
def test_chat_uses_the_client_retry_setting_for_the_cheap_model(tmp_path):
    client, completions, _, _ = make_fallback_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert completions.retry_settings == [None]


# S07：強模型被限流，使用者照樣拿到回答，回應的 model 是實際回答的便宜模型
def test_chat_answers_from_the_cheap_model_when_the_strong_one_is_rate_limited(tmp_path):
    client, completions, _, _ = make_fallback_test_client(tmp_path, errors={"big": make_rate_limit_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    assert response.json()["reply"] == "Hi there"
    assert response.json()["model"] == "small"
    assert completions.models_called() == ["big", "small"]


# 降級後照便宜模型的單價收錢：13 / 11 個 token 是 7，不是強模型的 136
def test_chat_charges_the_cheap_price_after_fallback(tmp_path):
    client, _, audit_path, database = make_fallback_test_client(tmp_path, errors={"big": make_rate_limit_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    assert read_audit(audit_path)["cost_micro_usd"] == 7
    assert charged_amounts(database) == ["0", "7"]


# 稽核：model 是實際回答、也拿來計費的便宜模型；routed_model 仍是路由原本選的強模型
def test_chat_audits_both_the_routed_and_the_answering_model_after_fallback(tmp_path):
    client, _, audit_path, _ = make_fallback_test_client(tmp_path, errors={"big": make_rate_limit_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    record = read_audit(audit_path)
    assert record["status"] == "ok"
    assert record["routed_model"] == "big"
    assert record["model"] == "small"
    assert record["provider_model"] == "small"


# 降級後便宜模型出了別的錯：回 502、留下稽核、不扣錢（資料庫只收到事前的「加 0」）
def test_chat_returns_502_when_the_cheap_model_fails_after_fallback(tmp_path):
    errors = {"big": make_rate_limit_error(), "small": OpenAIError("boom")}
    client, completions, audit_path, database = make_fallback_test_client(tmp_path, errors=errors)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    # 先確認兩顆都真的被呼叫過、請求是在第二顆失敗的，下面的「沒扣錢」才有意義
    assert response.status_code == 502
    assert response.json() == {"detail": "Upstream model error"}
    assert completions.models_called() == ["big", "small"]
    record = read_audit(audit_path)
    assert record["status"] == "error"
    assert record["error_type"] == "OpenAIError"
    assert charged_amounts(database) == ["0"]


# 兩顆都被限流：回 503，Retry-After 照便宜模型（最後一次）的標頭，不是強模型的
def test_chat_returns_503_with_retry_after_when_both_models_are_rate_limited(tmp_path):
    errors = {"big": make_rate_limit_error(retry_after=50), "small": make_rate_limit_error(retry_after=7)}
    client, completions, _, _ = make_fallback_test_client(tmp_path, errors=errors)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}
    assert response.headers["retry-after"] == "7"
    assert completions.models_called() == ["big", "small"]


# 便宜模型的錯誤沒有帶標頭：Retry-After 用預設的 30 秒
def test_chat_uses_the_default_retry_after_without_a_provider_header(tmp_path):
    errors = {"big": make_rate_limit_error(), "small": make_rate_limit_error()}
    client, _, _, _ = make_fallback_test_client(tmp_path, errors=errors)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 503
    assert response.headers["retry-after"] == "30"


# 路由一開始就選便宜模型、它被限流：一樣回 503 與 Retry-After，只呼叫一次
def test_chat_returns_503_when_the_cheap_route_is_rate_limited(tmp_path):
    client, completions, _, _ = make_fallback_test_client(tmp_path, errors={"small": make_rate_limit_error(retry_after=9)})

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 503
    assert response.headers["retry-after"] == "9"
    assert completions.models_called() == ["small"]


# 兩顆都被限流：留下一筆失敗的稽核，不扣錢（資料庫只收到事前的「加 0」）
def test_chat_audits_and_spends_nothing_when_both_models_are_rate_limited(tmp_path):
    errors = {"big": make_rate_limit_error(), "small": make_rate_limit_error()}
    client, _, audit_path, database = make_fallback_test_client(tmp_path, errors=errors)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    # 先確認請求真的是在這條路結束的，下面的「沒扣錢」才有意義
    assert response.status_code == 503
    record = read_audit(audit_path)
    assert record["status"] == "error"
    assert record["error_type"] == "RateLimitError"
    assert record["routed_model"] == "big"
    assert charged_amounts(database) == ["0"]


# 預算用完的錯誤：代碼與類型照官方文件的寫法
def make_budget_error():
    """Return the 429 the provider sends when the project's spend limit is reached."""
    return make_rate_limit_error(code="project_spend_limit_exceeded", error_type="insufficient_quota")


# 強模型遇到預算用完：不降級，回 503，不附 Retry-After（多久恢復無從得知）
def test_chat_does_not_fall_back_when_the_provider_budget_is_exhausted(tmp_path):
    client, completions, _, _ = make_fallback_test_client(tmp_path, errors={"big": make_budget_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}
    assert "retry-after" not in response.headers
    assert completions.models_called() == ["big"]


# 路由一開始就選便宜模型、遇到預算用完：一樣回 503、不附 Retry-After
def test_chat_returns_503_without_retry_after_when_the_cheap_route_hits_the_budget(tmp_path):
    client, completions, _, _ = make_fallback_test_client(tmp_path, errors={"small": make_budget_error()})

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 503
    assert "retry-after" not in response.headers
    assert completions.models_called() == ["small"]


# 強模型被限流、降級後的便宜模型剛好遇到預算用完：看的是最後那一次的錯誤，不附 Retry-After
def test_chat_returns_503_without_retry_after_when_the_budget_runs_out_after_fallback(tmp_path):
    errors = {"big": make_rate_limit_error(retry_after=7), "small": make_budget_error()}
    client, completions, _, _ = make_fallback_test_client(tmp_path, errors=errors)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 503
    assert "retry-after" not in response.headers
    assert completions.models_called() == ["big", "small"]


# 預算用完：留下一筆失敗的稽核，不扣錢
def test_chat_audits_and_spends_nothing_when_the_provider_budget_is_exhausted(tmp_path):
    client, _, audit_path, database = make_fallback_test_client(tmp_path, errors={"big": make_budget_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    # 先確認請求真的是在這條路結束的，下面的「沒扣錢」才有意義
    assert response.status_code == 503
    record = read_audit(audit_path)
    assert record["status"] == "error"
    assert record["error_type"] == "RateLimitError"
    assert charged_amounts(database) == ["0"]


# ---------- 稽核欄位：fallback、fallback_reason、error_code ----------


# 供應商說「沒有這顆模型」（404，代碼 model_not_found）：E22 看過的那種設定錯誤
def make_model_not_found_error():
    """Return the error the OpenAI SDK raises when the model does not exist."""
    request = httpx2.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx2.Response(404, request=request)
    return NotFoundError("fake 404", response=response, body={"code": "model_not_found", "type": "invalid_request_error"})


# 沒降級的成功紀錄：fallback 是 false，沒有 fallback_reason 這一欄
def test_chat_audits_no_fallback_on_a_normal_answer(tmp_path):
    client, _, audit_path, _ = make_fallback_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    record = read_audit(audit_path)
    assert record["fallback"] is False
    assert "fallback_reason" not in record


# 降級後成功的紀錄：fallback 是 true，原因是錯誤的類別名稱
def test_chat_audits_the_fallback_and_its_reason(tmp_path):
    client, _, audit_path, _ = make_fallback_test_client(tmp_path, errors={"big": make_rate_limit_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 200
    record = read_audit(audit_path)
    assert record["fallback"] is True
    assert record["fallback_reason"] == "RateLimitError"


# 兩顆都被限流：失敗的紀錄也要看得出降級過，並記下供應商的代碼
def test_chat_audits_fallback_and_code_when_both_models_are_rate_limited(tmp_path):
    errors = {"big": make_rate_limit_error(), "small": make_rate_limit_error()}
    client, _, audit_path, _ = make_fallback_test_client(tmp_path, errors=errors)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 503
    record = read_audit(audit_path)
    assert record["fallback"] is True
    assert record["fallback_reason"] == "RateLimitError"
    assert record["error_code"] == "rate_limit_exceeded"


# 預算用完：沒降級，代碼記下來，事後分得出這不是限流
def test_chat_audits_the_budget_code_without_fallback(tmp_path):
    client, _, audit_path, _ = make_fallback_test_client(tmp_path, errors={"big": make_budget_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 503
    record = read_audit(audit_path)
    assert record["fallback"] is False
    assert "fallback_reason" not in record
    assert record["error_code"] == "project_spend_limit_exceeded"


# 不是 429 的供應商錯誤也記代碼：模型名稱打錯時，從稽核就看得出是 model_not_found
def test_chat_audits_the_code_of_other_provider_errors(tmp_path):
    client, _, audit_path, _ = make_fallback_test_client(tmp_path, errors={"big": make_model_not_found_error()})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 502
    record = read_audit(audit_path)
    assert record["error_type"] == "NotFoundError"
    assert record["error_code"] == "model_not_found"
    assert record["fallback"] is False


# 沒有代碼的錯誤（不是供應商回應的錯誤）：不留 error_code 這一欄
def test_chat_audits_no_code_when_the_error_has_none(tmp_path):
    client, _, audit_path, _ = make_fallback_test_client(tmp_path, errors={"big": OpenAIError("boom")})

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 502
    assert "error_code" not in read_audit(audit_path)


# 被額度擋下的請求沒有走到呼叫模型，紀錄裡沒有 fallback
def test_chat_audits_no_fallback_when_the_quota_is_used_up(tmp_path):
    client, completions, audit_path, _ = make_fallback_test_client(tmp_path)
    gateway.dependency_overrides[get_quota] = lambda: (100, 100)

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    # 先確認請求真的是被額度擋下的
    assert response.status_code == 429
    assert completions.models_called() == []
    assert "fallback" not in read_audit(audit_path)


# 路由選到的模型查不到設定（500）：同樣沒有走到呼叫模型，紀錄裡沒有 fallback
def test_chat_audits_no_fallback_when_the_routed_model_has_no_settings(tmp_path):
    client, completions, audit_path, _ = make_fallback_test_client(tmp_path)
    gateway.dependency_overrides[get_config] = lambda: BROKEN_CONFIG

    response = client.post("/v1/chat", json={"message": STRONG_MESSAGE})

    assert response.status_code == 500
    assert completions.models_called() == []
    assert "fallback" not in read_audit(audit_path)
