"""LLM Gateway API service."""

import json
import os
import sys
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import APIError, OpenAI, RateLimitError
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from app.audit import save_audit, hash_prompt, make_summary, mask, detect_pii_types, report_audit_failure
from app.auth import extract_bearer_token, find_user_id, hash_api_key
from app.config import CONFIG_PATH, GatewayConfig, load_config
from app.db import make_dynamodb_client
from app.events import make_sqs_client, read_queue_url, send_event
from app.fallback import chat_with_fallback, is_budget_exhausted, retry_after_seconds
from app.ledger import record_charge
from app.metrics import REGISTRY, observe_request
from app.openai_auth import make_openai_client, read_openai_auth
from app.pricing import ModelNotConfiguredError, cost_micro_usd, find_model_config
from app.quota import add_usage, is_over_quota, period_of, read_limit, read_used, seconds_until_next_period
from app.router import choose_model

# 啟動時就把設定讀進來並檢查：設定有問題，Gateway 直接起不來
CONFIG = load_config(CONFIG_PATH)

# OpenAI 連線設定：重試和逾時都調小，避免重複花錢、卡住連線（D10）
# 不讓 SDK 自己重試：被限流時直接回 503 與 Retry-After，不在背後等到負載平衡器先斷線
OPENAI_MAX_RETRIES = 0
# 強模型寫滿輸出上限 2,000 個 tokens 約 32 秒（實測每秒約 62 個），30 秒會逾時
OPENAI_TIMEOUT_SECONDS = 60

# 向 OpenAI 證明身分的方式也在啟動時就確認：沒設或寫錯，Gateway 直接起不來（不等第一個請求才出錯）
OPENAI_AUTH = read_openai_auth()

# 記帳事件送哪個佇列也在啟動時就確認：沒設或寫錯，Gateway 直接起不來；disabled（本機、測試）表示不用 SQS
CHARGE_QUEUE_URL = read_queue_url()


# 啟動時印一行目前的記帳模式；只印 sqs 或 disabled，不印網址（網址裡有 AWS 帳號 ID）
def log_queue_mode(queue_url: str | None) -> None:
    """Print one JSON line saying whether charge events go to SQS."""
    if queue_url is None:
        mode = "disabled"
    else:
        mode = "sqs"
    print(json.dumps({"event": "charge_queue_mode", "mode": mode}), file=sys.stderr, flush=True)


log_queue_mode(CHARGE_QUEUE_URL)

# 說明頁（/docs、/redoc、/openapi.json）一律關閉：使用者用不到，只會把 API 的地圖交給想攻擊的人
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None) # 開店：建立整個 Web 服務。後面所有門牌都貼在 app 上。

# Demo Console 的檔案（HTML、CSS、JS）跟著 Gateway 打包，不另開 S3（決策書 3.1）
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 每個回應都加上的安全標頭（決策書 4.4）
# CSP：只准載入自己網站的程式與樣式、不准內嵌程式、不准被別的網站嵌進 iframe
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    # 瀏覽器每次都要先問伺服器「檔案有沒有換」：改版後不會繼續用舊的 CSS、JS（沒換就回 304，不重傳）
    "Cache-Control": "no-cache",
}


# 中介層：每個請求處理完、回應送出前，把安全標頭貼上去
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers[name] = value
    return response


# 請求格式：只收 message，沒有 model 欄位，使用者不能指定模型（D9）
class ChatRequest(BaseModel):
    """What the caller sends. The caller cannot choose the model."""
    # message 是空的或超過 4000 字，Pydantic 自動回422，格式不對
    message: str = Field(min_length=1, max_length=4000) # 點餐單的格式。只收一個欄位 message，必須是文字，長度 1～4000 字。


# 領用窗口：OpenAI 連線（測試時會換成假的）
# 整個程式共用一個：身分聯盟換來的通行證可用 1 小時，每個請求都新建就要每次重換、多兩趟網路
@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return make_openai_client(OPENAI_AUTH, OPENAI_MAX_RETRIES, OPENAI_TIMEOUT_SECONDS)


# 領用窗口：HMAC 金鑰，從環境變數讀取，不寫在程式裡
def get_hmac_key() -> bytes:
    return os.environ["AUDIT_HMAC_KEY"].encode("utf-8")


# 領用窗口：模型、單價與路由規則（測試時會換成測試用的設定）
def get_config() -> GatewayConfig:
    return CONFIG


# 領用窗口：資料庫連線（測試時會換成考場的）
def get_dynamodb() -> BaseClient:
    return make_dynamodb_client()


# 領用窗口：記帳事件的佇列網址；None 表示不用 SQS（測試時會換成假的網址）
def get_queue_url() -> str | None:
    return CHARGE_QUEUE_URL


# 領用窗口：SQS 連線（測試時會換成假的）；整個程式共用一條，同 get_client()
# disabled 時不建：boto3 一建連線就去找 AWS 憑證，本機沒有憑證或登入方式不同時會出錯、或卡在逾時
@lru_cache(maxsize=1)
def get_sqs() -> BaseClient | None:
    if CHARGE_QUEUE_URL is None:
        return None
    return make_sqs_client()


# 領用窗口：寫稽核的方式。正式環境寫進 audit 表、寫不進去就印一行日誌；測試時換成寫暫存檔
def get_audit_writer(dynamodb: BaseClient = Depends(get_dynamodb)) -> Callable[[dict], None]:
    def write(record: dict) -> None:
        save_audit(dynamodb, record)

    return write


# 驗票口：通過才交出「這個請求是誰」；沒通過在這裡就結束，進不了對話入口
def get_user_id(
    authorization: str | None = Header(default=None),   # 標頭可以不帶，沒帶就是 None
    dynamodb: BaseClient = Depends(get_dynamodb),   # 資料庫連線由領用窗口給（測試時換成考場）
) -> str:
    """Return the caller's user id, or stop the request with 401 or 503."""
    token = extract_bearer_token(authorization)  # extract_bearer_token 從標頭拿出 Key
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}, # HTTP 規範：回 401 要告訴對方「該用哪種方式驗證」
        )
    key_hash = hash_api_key(token)  # 請求進來時，在 get_user_id() 裡算雜湊
    # 資料庫讀不到時不放行，也不說成是 Key 的問題：回 503，請對方稍後再試
    try:
        user_id = find_user_id(dynamodb, key_hash) # find_user_id 拿雜湊去查表
    except (BotoCoreError, ClientError):    # BotoCoreError 是連不上、逾時這類；ClientError 是 AWS 有回、但辦不到，例如表不存在、沒權限
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}, # HTTP 規範：回 401 要告訴對方「該用哪種方式驗證」
        )
    return user_id


# 領用窗口：現在的時間（測試時會換成固定的時間點）
def get_now() -> datetime:
    return datetime.now(timezone.utc)


# 領用窗口：這個人的額度與本月已用量；讀不到就不放行
def get_quota(
    user_id: str = Depends(get_user_id),    # 要先過驗票口，沒過驗票口就不會讀額度，也不會把別人的額度讀出來
    dynamodb: BaseClient = Depends(get_dynamodb),
    now: datetime = Depends(get_now),
) -> tuple[int, int]:
    """Return the caller's limit and usage this month, or stop the request with 503."""
    try:
        limit_micro_usd = read_limit(dynamodb, user_id)
        used_micro_usd = read_used(dynamodb, user_id, period_of(now))
    except (BotoCoreError, ClientError):
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    return limit_micro_usd, used_micro_usd  # 只回數字，不判斷，判斷留給 chat_endpoint：超額要寫一筆稽核再回 429


# 健康檢查：只回狀態，不透露版本等資訊
@app.get("/health")
def health_check():
    """
    Health check for the load balancer.
    
    Return only the status on purpose. Extra details such as the
    version would help attackers look up known vulnerabilities.
    """
    return {"status": "ok"}


# 首頁就是 Demo Console
@app.get("/")
def console() -> FileResponse:
    """Return the Demo Console page."""
    return FileResponse(STATIC_DIR / "index.html")


# 登入用：只驗 Key、回名稱與額度；不呼叫模型、一毛不花（Console 的登入頁與角落的名稱）
@app.get("/v1/me")
def me(
    user_id: str = Depends(get_user_id),
    quota: tuple[int, int] = Depends(get_quota),
):
    """Return who the caller is and their quota this month, without calling the model."""
    limit_micro_usd, used_micro_usd = quota
    return {
        "user_id": user_id,
        "quota": {
            "limit_micro_usd": limit_micro_usd,
            "used_micro_usd": used_micro_usd,
        },
    }


# 監控端點：Prometheus 來抄數字；雲端由 ALB 檢查通行證，沒帶就 403、碰不到容器（4.3）
@app.get("/metrics")
def metrics() -> Response:
    """Return the counters in the Prometheus text format."""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


# SQS 送不進去、改走備援時印一行：帳是對的（Gateway 自己記了），只是要知道佇列出了問題；不印摘要與指紋
def report_queue_failure(record: dict, error: Exception) -> None:
    """Print one JSON line saying the charge event could not be sent."""
    entry = {
        "event": "charge_queue_failed",
        "request_id": record["request_id"],
        "error_type": type(error).__name__,
    }
    print(json.dumps(entry), file=sys.stderr, flush=True)


# 供應商的預算用完時印一行：要有人去加值或調上限，長期層的告警看這一行（D32）；只記單號、模型與代碼，不記錯誤訊息
def report_budget_exhausted(record: dict) -> None:
    """Print one JSON line saying the provider's budget has run out."""
    entry = {
        "event": "provider_budget_exhausted",
        "request_id": record["request_id"],
        "routed_model": record.get("routed_model"),
        "error_code": record.get("error_code"),
    }
    print(json.dumps(entry), file=sys.stderr, flush=True)


# 成功那一筆的記帳：先送 SQS 交給 Worker；送不進去或不用 SQS，就自己一次寫三本帳
# 兩條都失敗時印 charge_record_failed（有自己的告警），回答照給：錢已經付給 OpenAI 了
def save_charge(sqs: BaseClient | None, queue_url: str | None, dynamodb: BaseClient, record: dict, period: str) -> None:
    """Send the charge event to SQS, or record it here if that fails or SQS is disabled."""
    if queue_url is not None:
        try:
            send_event(sqs, queue_url, record, period)
            return
        except (BotoCoreError, ClientError) as exc:
            report_queue_failure(record, exc)
    # 回 False 表示 SQS 其實收到了、Worker 已經記過：帳是對的，不用印日誌
    try:
        record_charge(dynamodb, record, period)
    except (BotoCoreError, ClientError) as exc:
        record["charged"] = False
        report_audit_failure(record, exc, event="charge_record_failed")


# 對話入口：開單號 → 遮罩 → 呼叫模型 → 寫稽核紀錄 → 回傳
@app.post("/v1/chat")
# @：Python 的「裝飾器」，可以想成把一張標籤貼在下一行的函式上。
# post：HTTP 的方法。GET 是「去櫃檯看一眼」，例如 /health 只是問「你活著嗎」；POST 是「遞一張單子進去請店家處理」，要帶內容（message）。
# "/v1/chat"：路徑。v1 是第 1 版，以後要改格式可以開 /v2/chat，舊的程式不會壞。
def chat_endpoint(
    # Depends(...)：店員上工前，先去「領用窗口」領工具。FastAPI 會先執行 get_client()，再把結果交給 client。
    request: ChatRequest,   # 點餐單，FastAPI 已檢查過
    client: OpenAI = Depends(get_client),   # 領用窗口：OpenAI 連線
    hmac_key: bytes = Depends(get_hmac_key),    # 領用窗口：雜湊值用的金鑰
    write_audit_record: Callable[[dict], None] = Depends(get_audit_writer), # 領用窗口：寫進 audit 表
    user_id: str = Depends(get_user_id),    # 領用窗口：驗 Key → 是誰
    quota: tuple[int, int] = Depends(get_quota),    # 領用窗口：額度、已用量
    now: datetime = Depends(get_now),   # 領用窗口：現在時間
    dynamodb: BaseClient = Depends(get_dynamodb),   # 領用窗口：資料庫連線
    sqs: BaseClient | None = Depends(get_sqs),  # 領用窗口：記帳佇列
    queue_url: str | None = Depends(get_queue_url), # 領用窗口：佇列網址
    config: GatewayConfig = Depends(get_config),    # 領用窗口：設定檔
):
    """Send the masked message to the model and write an audit record."""
    # 開始計時：每條路結束前把花了多久記進監控
    started = time.perf_counter()   # 開始計時，給監控記「花了幾秒」
    request_id = str(uuid.uuid4())  # 隨機單號，不會撞號、猜不到下一號
    masked = mask(request.message)  # 送給 OpenAI 的是這個

    # 先準備紀錄的前半段：不管成功或失敗都要記的欄位
    record = {
        "request_id": request_id,   # audit 表的主鍵
        "user_id": user_id, # who
        "timestamp": now.isoformat(),   # 改用 get_now()，測試能固定時間
        "prompt_hash": hash_prompt(request.message, hmac_key),  # 原文的 HMAC 雜湊值，64 個字
        "summary": make_summary(request.message),   # 先遮罩、再取前 50 個字
        "pii_types": detect_pii_types(request.message)  # 偵測到哪幾類個資（只記類別）
    }

    # 額度用完就擋：先記一筆稽核（查得到誰在用完後還一直送），再回 429 並告知何時恢復
    limit_micro_usd, used_micro_usd = quota # 拆開兩個數字（額度、本月已用）
    if is_over_quota(limit_micro_usd, used_micro_usd):
        record["status"] = "quota_exceeded"
        write_audit_record(record)  # 被擋的也記：查得到誰用完了還一直送
        observe_request(record, time.perf_counter() - started)  # Grafana 上「被擋了幾次」
        raise HTTPException(
            status_code=429,
            detail="Monthly quota exceeded",
            headers={"Retry-After": str(seconds_until_next_period(now))},
        )

    # 花錢之前先確認扣得了帳：對當月那一筆加 0，寫不進去就回 503，一毛都還沒花
    period = period_of(now) # 這個月，例如 "2026-11"（台北時間）
    try:
        add_usage(dynamodb, user_id, period, 0) # 加 0 元
    except (BotoCoreError, ClientError):    # 連不上（BotoCoreError）或 AWS 拒絕（ClientError）
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")  # 一毛都還沒花

    # 依遮罩後的內容選模型，理由記進稽核；再查到這顆模型的設定（含單價）：查不到就不呼叫
    decision = choose_model(masked, config.routing)
    record["route_reason"] = decision.reason    # length / keyword / default
    record["routed_model"] = decision.model     # 路由選的那顆
    # 查不到設定是我們自己的設定問題：記一筆失敗、回 500，不呼叫模型、不扣錢
    try:
        settings = find_model_config(config.models, decision.model)
    except ModelNotConfiguredError as exc:
        record["status"] = "error"
        record["error_type"] = type(exc).__name__   # 記下錯誤類別名稱 "ModelNotConfiguredError"
        write_audit_record(record)
        observe_request(record, time.perf_counter() - started)
        raise HTTPException(status_code=500, detail="Internal server error")

    # 呼叫模型：強模型被限流時改用便宜模型一次；不論成功失敗，都交回一個結果（不往外丟錯誤：成功或失敗都包成一個 CallOutcome 交回來）
    outcome = chat_with_fallback(
        client,
        [{"role": "user", "content": masked}],  # 遮罩後的內容
        decision.model, # 路由選的那顆模型
        settings,   # 模型的設定
        config, 
    )

    # 稽核：有沒有降級；降級了才記原因（成功、失敗都記，所以寫在判斷成敗之前）
    record["fallback"] = outcome.fallback   # 記 fallback（成功、失敗都記）
    if outcome.fallback:    # 降級了才記 fallback_reason
        record["fallback_reason"] = outcome.fallback_reason

    # 沒拿到回答：記一筆失敗
    if outcome.error is not None:   # 有錯誤嗎？
        record["status"] = "error"
        record["error_type"] = type(outcome.error).__name__ # 錯誤類別名
        # 供應商有回應的錯誤才有代碼（例如 rate_limit_exceeded、project_spend_limit_exceeded）：
        # 只記這個短代碼、不記錯誤訊息，事後才分得出是哪一種問題
        if isinstance(outcome.error, APIError): # OpenAI 有回應的錯誤（APIError） → 記 error_code（短代碼）不記錯誤訊息全文，因為訊息可能帶到使用者內容，也很長。只記代碼，之後查得到是哪一種問題，又不會把東西洩漏出去。
            record["error_code"] = outcome.error.code
        write_audit_record(record)  # 寫稽核
        observe_request(record, time.perf_counter() - started)  # 記監控數字，失敗也算進請求數和耗時。
        # 供應商回 429（限流或預算用完）：回 503
        if isinstance(outcome.error, RateLimitError):   # 是 429？
            # 供應商的預算用完：多久會恢復無從得知，要有人處理，所以不附 Retry-After
            if is_budget_exhausted(outcome.error):  # 預算用完？
                report_budget_exhausted(record) # 印一行日誌給長期層的告警看
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")  # 503（不附 Retry-After）
            # 限流（降級後的便宜模型，或路由一開始就選便宜模型）：告訴對方大約多久後再試
            raise HTTPException(    # 503 + Retry-After
                status_code=503,
                detail="Service temporarily unavailable",
                headers={"Retry-After": str(retry_after_seconds(outcome.error))},
            )
        raise HTTPException(status_code=502, detail="Upstream model error") # 502 Bad Gateway：上游模型出錯，Gateway 只是轉送，不是自己的問題

    # 成功：補上模型和用量，再寫入
    # model 記實際回答、也拿來計費的那一顆（降級後是便宜模型）；provider_model 記 OpenAI 回報的名稱
    result = outcome.result # 走到這裡代表 error is None，所以 result 一定有值。
    # model 記 outcome.model，不是 decision.model。路由選了誰，已經在 :331 記成 routed_model。
    # 所以一筆降級的紀錄會同時有「路由選 sol」和「實際由 luna 回答」
    record["model"] = outcome.model
    record["provider_model"] = result.model # OpenAI 回報的名稱，把「我們要求的」和「對方實際給的」分開記，萬一 OpenAI 悄悄換了版本，事後查得到。
    record["input_tokens"] = result.input_tokens
    record["output_tokens"] = result.output_tokens  # output_tokens 已經包含 reasoning_tokens（OpenAI 的 completion_tokens 本來就把思考算在裡面）。
    record["reasoning_tokens"] = result.reasoning_tokens    # 輸出裡有多少是在思考
    # 結束原因：被輸出上限截斷（length）時，回答可能只有一半甚至是空的，但照樣計費
    record["finish_reason"] = result.finish_reason  # "stop" 或 "length"
    record["status"] = "ok"

    # 把這次的成本放進紀錄，交給 save_charge()：送 SQS 讓 Worker 記，送不進去就自己記；記帳出問題也照樣把回答交出去
    cost = cost_micro_usd(outcome.settings, result.input_tokens, result.output_tokens)
    record["cost_micro_usd"] = cost
    save_charge(sqs, queue_url, dynamodb, record, period)   # 成功的那筆稽核就是在這裡寫的，不是用 write_audit_record()
    observe_request(record, time.perf_counter() - started)
    # 回應除了回答，也把 Console 要顯示的東西一起帶回去：路由理由、有沒有降級、用量、成本、額度
    # 額度的已用＝呼叫前讀到的已用＋這次成本：帳由 Worker 非同步記，回頭讀資料庫可能還沒入帳
    return {
        "request_id": request_id,
        "reply": result.text,
        "model": outcome.model,
        "route": {
            "reason": decision.reason,  # 路由理由：length / keyword / default
            "fallback": outcome.fallback,   # 有沒有降級
        },
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "reasoning_tokens": result.reasoning_tokens,
        },
        "cost_micro_usd": cost,
        # 只回「有哪幾類個資被遮掉」，不回個資本身（跟稽核紀錄同一份）
        "pii_types": record["pii_types"],   # 只回類別，不回個資本身
        "quota": {
            "limit_micro_usd": limit_micro_usd,
            "used_micro_usd": used_micro_usd + cost,    # 呼叫前讀到的已用＋這次成本：帳由 Worker 非同步記，回頭讀資料庫可能還沒入帳
        },
    }
