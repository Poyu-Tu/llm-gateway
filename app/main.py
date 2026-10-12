"""LLM Gateway API service."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, Header, HTTPException
from openai import APIError, OpenAI, RateLimitError
from pydantic import BaseModel, Field

from app.audit import append_audit, hash_prompt, make_summary, mask, detect_pii_types
from app.auth import extract_bearer_token, find_user_id, hash_api_key
from app.db import make_dynamodb_client
from app.config import CONFIG_PATH, GatewayConfig, load_config
from app.router import choose_model
from app.pricing import ModelNotConfiguredError, cost_micro_usd, find_model_config
from app.fallback import chat_with_fallback, is_budget_exhausted, retry_after_seconds
from app.quota import add_usage, is_over_quota, period_of, read_limit, read_used, seconds_until_next_period

# 啟動時就把設定讀進來並檢查：設定有問題，Gateway 直接起不來
CONFIG = load_config(CONFIG_PATH)

# OpenAI 連線設定：重試和逾時都調小，避免重複花錢、卡住連線（D10）
OPENAI_MAX_RETRIES = 1
OPENAI_TIMEOUT_SECONDS = 30

app = FastAPI()


# 請求格式：只收 message，沒有 model 欄位，使用者不能指定模型（D9）
class ChatRequest(BaseModel):
    """What the caller sends. The caller cannot choose the model."""

    message: str = Field(min_length=1, max_length=4000)


# 領用窗口：OpenAI 連線（測試時會換成假的）
def get_client() -> OpenAI:
    return OpenAI(max_retries=OPENAI_MAX_RETRIES, timeout=OPENAI_TIMEOUT_SECONDS)


# 領用窗口：HMAC 金鑰，從環境變數讀取，不寫在程式裡
def get_hmac_key() -> bytes:
    return os.environ["AUDIT_HMAC_KEY"].encode("utf-8")


# 領用窗口：稽核紀錄檔的位置
def get_audit_path() -> Path:
    return Path("data/audit.jsonl")


# 領用窗口：模型、單價與路由規則（測試時會換成測試用的設定）
def get_config() -> GatewayConfig:
    return CONFIG


# 領用窗口：資料庫連線（測試時會換成考場的）
def get_dynamodb() -> BaseClient:
    return make_dynamodb_client()


# 驗票口：通過才交出「這個請求是誰」；沒通過在這裡就結束，進不了對話入口
def get_user_id(
    authorization: str | None = Header(default=None),
    dynamodb: BaseClient = Depends(get_dynamodb),
) -> str:
    """Return the caller's user id, or stop the request with 401 or 503."""
    token = extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    key_hash = hash_api_key(token)
    # 資料庫讀不到時不放行，也不說成是 Key 的問題：回 503，請對方稍後再試
    try:
        user_id = find_user_id(dynamodb, key_hash)
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


# 領用窗口：現在的時間（測試時會換成固定的時間點）
def get_now() -> datetime:
    return datetime.now(timezone.utc)


# 領用窗口：這個人的額度與本月已用量；讀不到就不放行
def get_quota(
    user_id: str = Depends(get_user_id),
    dynamodb: BaseClient = Depends(get_dynamodb),
    now: datetime = Depends(get_now),
) -> tuple[int, int]:
    """Return the caller's limit and usage this month, or stop the request with 503."""
    try:
        limit_micro_usd = read_limit(dynamodb, user_id)
        used_micro_usd = read_used(dynamodb, user_id, period_of(now))
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    return limit_micro_usd, used_micro_usd


# 健康檢查：只回狀態，不透露版本等資訊
@app.get("/health")
def health_check():
    """
    Health check for the load balancer.
    
    Return only the status on purpose. Extra details such as the
    version would help attackers look up known vulnerabilities.
    """
    return {"status": "ok"}


# 對話入口：開單號 → 遮罩 → 呼叫模型 → 寫稽核紀錄 → 回傳
@app.post("/v1/chat")
def chat_endpoint(
    request: ChatRequest,
    client: OpenAI = Depends(get_client),
    hmac_key: bytes = Depends(get_hmac_key),
    audit_path: Path = Depends(get_audit_path),
    user_id: str = Depends(get_user_id),
    quota: tuple[int, int] = Depends(get_quota),
    now: datetime = Depends(get_now),
    dynamodb: BaseClient = Depends(get_dynamodb),
    config: GatewayConfig = Depends(get_config),
):
    """Send the masked message to the model and write an audit record."""
    request_id = str(uuid.uuid4())
    masked = mask(request.message)

    # 先準備紀錄的前半段：不管成功或失敗都要記的欄位
    record = {
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": now.isoformat(),
        "prompt_hash": hash_prompt(request.message, hmac_key),
        "summary": make_summary(request.message),
        "pii_types": detect_pii_types(request.message)
    }

    # 額度用完就擋：先記一筆稽核（查得到誰在用完後還一直送），再回 429 並告知何時恢復
    limit_micro_usd, used_micro_usd = quota
    if is_over_quota(limit_micro_usd, used_micro_usd):
        record["status"] = "quota_exceeded"
        append_audit(record, audit_path)
        raise HTTPException(
            status_code=429,
            detail="Monthly quota exceeded",
            headers={"Retry-After": str(seconds_until_next_period(now))},
        )

    # 花錢之前先確認扣得了帳：對當月那一筆加 0，寫不進去就回 503，一毛都還沒花
    period = period_of(now)
    try:
        add_usage(dynamodb, user_id, period, 0)
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

    # 依遮罩後的內容選模型，理由記進稽核；再查到這顆模型的設定（含單價）：查不到就不呼叫
    decision = choose_model(masked, config.routing)
    record["route_reason"] = decision.reason
    record["routed_model"] = decision.model
    # 查不到設定是我們自己的設定問題：記一筆失敗、回 500，不呼叫模型、不扣錢
    try:
        settings = find_model_config(config.models, decision.model)
    except ModelNotConfiguredError as exc:
        record["status"] = "error"
        record["error_type"] = type(exc).__name__
        append_audit(record, audit_path)
        raise HTTPException(status_code=500, detail="Internal server error")

    # 呼叫模型：強模型被限流時改用便宜模型一次；不論成功失敗，都交回一個結果（不往外丟錯誤）
    outcome = chat_with_fallback(
        client,
        [{"role": "user", "content": masked}],
        decision.model,
        settings,
        config,
    )

    # 稽核：有沒有降級；降級了才記原因（成功、失敗都記，所以寫在判斷成敗之前）
    record["fallback"] = outcome.fallback
    if outcome.fallback:
        record["fallback_reason"] = outcome.fallback_reason

    # 沒拿到回答：記一筆失敗
    if outcome.error is not None:
        record["status"] = "error"
        record["error_type"] = type(outcome.error).__name__
        # 供應商有回應的錯誤才有代碼（例如 rate_limit_exceeded、project_spend_limit_exceeded）：
        # 只記這個短代碼、不記錯誤訊息，事後才分得出是哪一種問題
        if isinstance(outcome.error, APIError):
            record["error_code"] = outcome.error.code
        append_audit(record, audit_path)
        # 供應商回 429（限流或預算用完）：回 503
        if isinstance(outcome.error, RateLimitError):
            # 供應商的預算用完：多久會恢復無從得知，要有人處理，所以不附 Retry-After
            if is_budget_exhausted(outcome.error):
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
            # 限流（降級後的便宜模型，或路由一開始就選便宜模型）：告訴對方大約多久後再試
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable",
                headers={"Retry-After": str(retry_after_seconds(outcome.error))},
            )
        raise HTTPException(status_code=502, detail="Upstream model error")

    # 成功：補上模型和用量，再寫入
    # model 記實際回答、也拿來計費的那一顆（降級後是便宜模型）；provider_model 記 OpenAI 回報的名稱
    result = outcome.result
    record["model"] = outcome.model
    record["provider_model"] = result.model
    record["input_tokens"] = result.input_tokens
    record["output_tokens"] = result.output_tokens
    record["reasoning_tokens"] = result.reasoning_tokens
    record["status"] = "ok"

    # 把這次的成本加到當月已用量；這時模型已經回答了，扣失敗也照樣把回答交出去，並記下沒扣到
    cost = cost_micro_usd(outcome.settings, result.input_tokens, result.output_tokens)
    record["cost_micro_usd"] = cost
    try:
        add_usage(dynamodb, user_id, period, cost)
        record["charged"] = True
    except (BotoCoreError, ClientError):
        record["charged"] = False
        
    append_audit(record, audit_path)
    return {
        "request_id": request_id,
        "reply": result.text,
        "model": outcome.model,
    }