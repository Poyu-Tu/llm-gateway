"""Tests for chat_with_fallback(), retry_after_seconds() and is_budget_exhausted()."""

from openai import OpenAIError

from app.config import GatewayConfig, ModelConfig, RoutingConfig
from app.fallback import chat_with_fallback, is_budget_exhausted, retry_after_seconds
from tests.fakes import make_fake_client, make_rate_limit_error

# 測試用的設定：兩顆模型的思考量和輸出上限都不同，降級後拿錯設定才看得出來
CONFIG = GatewayConfig(
    routing=RoutingConfig(cheap_model="small", strong_model="big", min_chars=18, keywords=["debug"]),
    models={
        "small": ModelConfig(reasoning_effort="none", max_completion_tokens=100, input_price=100_000, output_price=500_000),
        "big": ModelConfig(reasoning_effort="low", max_completion_tokens=200, input_price=2_000_000, output_price=10_000_000),
    },
)

MESSAGES = [{"role": "user", "content": "hello"}]


# 照路由的結果呼叫：model 是路由選的那一顆，設定也是那一顆自己的
def call(client, model):
    """Call chat_with_fallback the way the chat endpoint will."""
    return chat_with_fallback(client, MESSAGES, model, CONFIG.models[model], CONFIG)


# 路由選便宜模型、一切正常：只呼叫一次，沒有降級
def test_cheap_route_calls_the_cheap_model_once():
    client, completions = make_fake_client()

    outcome = call(client, "small")

    assert outcome.result.text == "Hi there"
    assert outcome.error is None
    assert outcome.model == "small"
    assert outcome.settings == CONFIG.models["small"]
    assert outcome.fallback is False
    assert outcome.fallback_reason is None
    assert completions.models_called() == ["small"]


# 便宜模型那一次不另外改重試設定，照連線本身的設定（main.py 的 OPENAI_MAX_RETRIES，目前是 0）
def test_cheap_route_uses_the_client_retry_setting():
    client, completions = make_fake_client()

    call(client, "small")

    assert completions.retry_settings == [None]


# 路由選強模型、一切正常：只呼叫強模型一次，沒有降級
def test_strong_route_answers_without_fallback():
    client, completions = make_fake_client()

    outcome = call(client, "big")

    assert outcome.result.text == "Hi there"
    assert outcome.error is None
    assert outcome.model == "big"
    assert outcome.settings == CONFIG.models["big"]
    assert outcome.fallback is False
    assert outcome.fallback_reason is None
    assert completions.models_called() == ["big"]


# 強模型後面有備胎：這一次不讓 SDK 重試
def test_strong_route_turns_off_the_sdk_retry():
    client, completions = make_fake_client()

    call(client, "big")

    assert completions.retry_settings == [0]


# S07 的核心：強模型被限流，改由便宜模型回答，並記下降級過與原因
def test_rate_limited_strong_model_falls_back_to_the_cheap_model():
    client, completions = make_fake_client(errors={"big": make_rate_limit_error()})

    outcome = call(client, "big")

    assert outcome.result.text == "Hi there"
    assert outcome.error is None
    assert outcome.model == "small"
    assert outcome.fallback is True
    assert outcome.fallback_reason == "RateLimitError"


# 降級時兩顆各呼叫一次，先強後便宜；不會重複呼叫
def test_fallback_calls_each_model_exactly_once():
    client, completions = make_fake_client(errors={"big": make_rate_limit_error()})

    call(client, "big")

    assert completions.models_called() == ["big", "small"]


# 降級後用的是便宜模型自己的設定：思考量、輸出上限，以及交回去給算成本用的那一份
def test_fallback_uses_the_settings_of_the_cheap_model():
    client, completions = make_fake_client(errors={"big": make_rate_limit_error()})

    outcome = call(client, "big")

    assert completions.requests[0]["reasoning_effort"] == "low"
    assert completions.requests[0]["max_completion_tokens"] == 200
    assert completions.requests[1]["reasoning_effort"] == "none"
    assert completions.requests[1]["max_completion_tokens"] == 100
    assert outcome.settings == CONFIG.models["small"]


# 降級後送給便宜模型的內容和原本的一樣
def test_fallback_sends_the_same_messages():
    client, completions = make_fake_client(errors={"big": make_rate_limit_error()})

    call(client, "big")

    assert completions.requests[0]["messages"] == MESSAGES
    assert completions.requests[1]["messages"] == MESSAGES


# 強模型那一次明確設成不重試；降級後的便宜模型照連線本身的設定
def test_fallback_call_uses_the_client_retry_setting():
    client, completions = make_fake_client(errors={"big": make_rate_limit_error()})

    call(client, "big")

    assert completions.retry_settings == [0, None]


# 限流以外的錯誤不降級：把那個錯誤交回去，便宜模型沒有被呼叫
def test_other_error_on_the_strong_model_does_not_fall_back():
    boom = OpenAIError("boom")
    client, completions = make_fake_client(errors={"big": boom})

    outcome = call(client, "big")

    assert outcome.error is boom
    assert outcome.result is None
    assert outcome.model == "big"
    assert outcome.fallback is False
    assert outcome.fallback_reason is None
    assert completions.models_called() == ["big"]


# 兩顆都被限流：交回便宜模型的那個錯誤，並記下降級過；總共只呼叫兩次
def test_both_models_rate_limited_returns_the_error_of_the_cheap_model():
    strong_error = make_rate_limit_error()
    cheap_error = make_rate_limit_error(retry_after=7)
    client, completions = make_fake_client(errors={"big": strong_error, "small": cheap_error})

    outcome = call(client, "big")

    assert outcome.error is cheap_error
    assert outcome.result is None
    assert outcome.model == "small"
    assert outcome.fallback is True
    assert outcome.fallback_reason == "RateLimitError"
    assert completions.models_called() == ["big", "small"]


# 降級後便宜模型出了別的錯：一樣交回那個錯誤，降級過這件事不能不見
def test_other_error_after_fallback_is_returned():
    boom = OpenAIError("boom")
    client, completions = make_fake_client(errors={"big": make_rate_limit_error(), "small": boom})

    outcome = call(client, "big")

    assert outcome.error is boom
    assert outcome.result is None
    assert outcome.model == "small"
    assert outcome.fallback is True
    assert completions.models_called() == ["big", "small"]


# 路由一開始就選便宜模型、它被限流：沒有備胎可換，交回錯誤，只呼叫一次
def test_rate_limited_cheap_route_does_not_fall_back():
    cheap_error = make_rate_limit_error()
    client, completions = make_fake_client(errors={"small": cheap_error})

    outcome = call(client, "small")

    assert outcome.error is cheap_error
    assert outcome.result is None
    assert outcome.model == "small"
    assert outcome.fallback is False
    assert outcome.fallback_reason is None
    assert completions.models_called() == ["small"]


# ---------- retry_after_seconds()：兩顆都被限流時，告訴使用者多久後再試 ----------


# 供應商說 7 秒，就轉告 7 秒
def test_retry_after_copies_the_providers_seconds():
    assert retry_after_seconds(make_rate_limit_error(retry_after=7)) == 7


# 下限：1 秒照抄
def test_retry_after_accepts_one_second():
    assert retry_after_seconds(make_rate_limit_error(retry_after=1)) == 1


# 上限：120 秒照抄
def test_retry_after_accepts_the_maximum():
    assert retry_after_seconds(make_rate_limit_error(retry_after=120)) == 120


# 超過上限就壓到上限，不照單全收
def test_retry_after_caps_long_waits():
    assert retry_after_seconds(make_rate_limit_error(retry_after=121)) == 120
    assert retry_after_seconds(make_rate_limit_error(retry_after=86400)) == 120


# 供應商沒給標頭：用預設的 30 秒
def test_retry_after_uses_the_default_without_a_header():
    assert retry_after_seconds(make_rate_limit_error()) == 30


# 0 或負數：叫對方立刻重試沒有意義，用預設值
def test_retry_after_uses_the_default_for_zero_or_negative():
    assert retry_after_seconds(make_rate_limit_error(retry_after=0)) == 30
    assert retry_after_seconds(make_rate_limit_error(retry_after=-5)) == 30


# 看不懂的寫法（文字、小數、日期）：不猜，用預設值
def test_retry_after_uses_the_default_for_values_it_cannot_read():
    assert retry_after_seconds(make_rate_limit_error(retry_after="soon")) == 30
    assert retry_after_seconds(make_rate_limit_error(retry_after="1.5")) == 30
    assert retry_after_seconds(make_rate_limit_error(retry_after="Wed, 21 Oct 2026 07:28:00 GMT")) == 30


# ---------- is_budget_exhausted()：這個 429 是限流，還是供應商的預算用完 ----------


# 官方文件列的預算類代碼：每一個都要認得（少打一個字母，這個測試就會紅）
def test_budget_codes_are_recognized():
    codes = [
        "insufficient_quota",
        "credit_balance_exhausted",
        "project_spend_limit_exceeded",
        "organization_spend_limit_exceeded",
        "organization_usage_limit_exceeded",
    ]
    for code in codes:
        assert is_budget_exhausted(make_rate_limit_error(code=code, error_type="invalid_request_error")) is True, code


# 代碼沒見過、但類型是 insufficient_quota：一樣算預算用完
def test_budget_type_is_recognized_with_an_unknown_code():
    error = make_rate_limit_error(code="some_new_billing_code", error_type="insufficient_quota")

    assert is_budget_exhausted(error) is True


# 一般的限流不是預算用完
def test_rate_limit_is_not_a_budget_problem():
    assert is_budget_exhausted(make_rate_limit_error()) is False


# 官方文件的另一種限流（請求增加得太快）也不是預算用完
def test_slow_down_is_not_a_budget_problem():
    error = make_rate_limit_error(code="slow_down", error_type="rate_limit_error")

    assert is_budget_exhausted(error) is False


# 沒有代碼也沒有類型（供應商的回應不是 JSON）：當成限流，不當成預算用完（排除法）
def test_unknown_429_is_treated_as_a_rate_limit():
    assert is_budget_exhausted(make_rate_limit_error(code=None, error_type=None)) is False


# 強模型遇到預算用完：不降級，把那個錯誤交回去，便宜模型沒有被呼叫
def test_budget_exhausted_on_the_strong_model_does_not_fall_back():
    budget_error = make_rate_limit_error(code="project_spend_limit_exceeded", error_type="insufficient_quota")
    client, completions = make_fake_client(errors={"big": budget_error})

    outcome = call(client, "big")

    assert outcome.error is budget_error
    assert outcome.result is None
    assert outcome.model == "big"
    assert outcome.fallback is False
    assert outcome.fallback_reason is None
    assert completions.models_called() == ["big"]
