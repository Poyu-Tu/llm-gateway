"""LLM Gateway API service."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, Header, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

from app.audit import append_audit, hash_prompt, make_summary, mask, detect_pii_types
from app.auth import extract_bearer_token, find_user_id, hash_api_key
from app.db import make_dynamodb_client
from app.providers.openai_client import chat

# M1 固定用便宜模型、不思考；M3 才會依內容選模型
MODEL = "gpt-6-luna"
REASONING_EFFORT = "none"

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
):
    """Send the masked message to the model and write an audit record."""
    request_id = str(uuid.uuid4())
    masked = mask(request.message)

    # 先準備紀錄的前半段：不管成功或失敗都要記的欄位
    record = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_hash": hash_prompt(request.message, hmac_key),
        "summary": make_summary(request.message),
        "pii_types": detect_pii_types(request.message)
    }

    # 試著呼叫模型；OpenAI 出錯就記一筆失敗，回 502
    try:
        result = chat(client, MODEL, [{"role": "user", "content": masked}], REASONING_EFFORT)
    except OpenAIError as exc:
        record["status"] = "error"
        record["error_type"] = type(exc).__name__
        append_audit(record, audit_path)
        raise HTTPException(status_code=502, detail="Upstream model error")

    # 成功：補上模型和用量，再寫入
    record["model"] = result.model
    record["input_tokens"] = result.input_tokens
    record["output_tokens"] = result.output_tokens
    record["reasoning_tokens"] = result.reasoning_tokens
    record["status"] = "ok"
    append_audit(record, audit_path)
    return {
        "request_id": request_id,
        "reply": result.text,
        "model": result.model,
    }