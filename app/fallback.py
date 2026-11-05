"""Call the model, and fall back to the cheap model when the strong one is rate limited."""

from dataclasses import dataclass

from openai import OpenAIError, RateLimitError

from app.config import GatewayConfig, ModelConfig
from app.pricing import find_model_config
from app.providers.openai_client import ChatResult, chat


# 呼叫模型的結果：成功或失敗都用這個交回去，稽核才知道最後用的是哪一顆、有沒有降級過
@dataclass(frozen=True)
class CallOutcome:
    """What happened when we called the model."""
    result: ChatResult | None
    error: OpenAIError | None
    model: str
    settings: ModelConfig
    fallback: bool
    fallback_reason: str | None


# 呼叫一次模型：成功就帶著回答交回去，OpenAI 出錯就帶著那個錯誤交回去（不往外丟）
def call_once(client, messages: list[dict], model: str, settings: ModelConfig, fallback: bool, fallback_reason: str | None) -> CallOutcome:
    """Call the model once and return the answer or the error."""
    try:
        result = chat(client, model, messages, settings.reasoning_effort, settings.max_completion_tokens)
    except OpenAIError as exc:
        return CallOutcome(
            result=None,
            error=exc,
            model=model,
            settings=settings,
            fallback=fallback,
            fallback_reason=fallback_reason,
        )
    return CallOutcome(
        result=result,
        error=None,
        model=model,
        settings=settings,
        fallback=fallback,
        fallback_reason=fallback_reason,
    )


# 供應商「預算用完」的代碼：換成便宜模型刷的還是同一張卡，降級沒用，而且要有人去處理
BUDGET_ERROR_CODES = [
    "insufficient_quota",
    "credit_balance_exhausted",
    "project_spend_limit_exceeded",
    "organization_spend_limit_exceeded",
    "organization_usage_limit_exceeded",
]


# 這個 429 是不是「預算用完」：看代碼，也看類型；兩邊都對不上的，一律當成限流（排除法）
def is_budget_exhausted(error: RateLimitError) -> bool:
    """Return True when the 429 means the provider's budget or credit has run out."""
    if error.code in BUDGET_ERROR_CODES:    # 先比對清單裡的代碼
        return True
    if error.type == "insufficient_quota":  # 再看錯誤類型是不是 insufficient_quota
        return True
    return False


# 強模型被限流就改用便宜模型一次；便宜模型後面沒有備胎，照平常的方式呼叫
def chat_with_fallback(client, messages: list[dict], model: str, settings: ModelConfig, config: GatewayConfig) -> CallOutcome:
    """Call the routed model; when the strong model is rate limited, try the cheap model once."""
    cheap_model = config.routing.cheap_model    # 從設定檔讀「備胎是哪一顆」，沒有寫死在程式裡。

    # 路由選的就是便宜模型：沒有備胎，照連線本身的重試設定（main.py 的 OPENAI_MAX_RETRIES）
    if model == cheap_model:
        return call_once(client, messages, model, settings, False, None)

    # 強模型後面有備胎：這一次不讓 SDK 重試，被限流就直接換人
    no_retry_client = client.with_options(max_retries=0)
    # 強模型這次不讓 SDK 自己重試。原因：有備胎的話，被限流就該馬上換人；讓 SDK 對同一顆強模型重試好幾次，只是白等。
    # 保證的是「強模型一定不重試」，就算以後有人把全域改回 3，降級的行為也不會跟著變。 >> 這是不依賴別處設定的保險
    first = call_once(no_retry_client, messages, model, settings, False, None)  # 用這條不重試的連線呼叫強模型一次。

    # 成功，或是限流以外的錯誤（不是 RateLimitError，例如 500、逾時）：都不降級，直接交回去
    if not isinstance(first.error, RateLimitError):
        return first
    # 供應商的預算用完：降級也一樣會被拒，不降級，直接交回去 >> 429
    if is_budget_exhausted(first.error):
        return first

    # 強模型被限流：查到便宜模型自己的設定，用它再呼叫一次
    cheap_settings = find_model_config(config.models, cheap_model)  # 查便宜模型自己的設定（推理強度、輸出上限），不沿用強模型的。
    reason = type(first.error).__name__ # 記的是 "RateLimitError" 這個類別名稱。
    return call_once(client, messages, cheap_model, cheap_settings, True, reason)   # 用原本的 client（照全域重試設定）呼叫便宜模型一次，fallback=True。


# 兩顆都被限流時，告訴使用者大約多久後再試：沒有標頭或看不懂時用這個
DEFAULT_RETRY_AFTER_SECONDS = 30    # 沒資料時給一個合理的等待時間
# 供應商說要等再久，最多也只轉告這麼久（和 SDK 自己願意等的上限相同）
MAX_RETRY_AFTER_SECONDS = 120


# 照抄供應商說的等待秒數，但不照單全收：只收整數秒，太大就壓到上限，沒有或看不懂就用預設值
def retry_after_seconds(error: RateLimitError) -> int:
    """Return how many seconds the caller should wait, based on the provider's Retry-After header."""
    value = error.response.headers.get("retry-after")   # 從供應商的回應標頭拿等待秒數，用小寫也拿得到，因為 HTTP 標頭不分大小寫
    if value is None:   # 沒有這個標頭 → 預設
        return DEFAULT_RETRY_AFTER_SECONDS

    try:
        seconds = int(value)    # 看不懂 → 預設；"soon"、"1.5"、日期格式都會讓 int() 失敗
    except ValueError:
        return DEFAULT_RETRY_AFTER_SECONDS

    if seconds < 1: # 0 或負數 → 預設
        return DEFAULT_RETRY_AFTER_SECONDS
    if seconds > MAX_RETRY_AFTER_SECONDS:   # 太大 → 壓到上限
        return MAX_RETRY_AFTER_SECONDS
    return seconds
