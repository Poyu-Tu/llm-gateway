"""Worker: read charge events from SQS and write them into the ledger."""

import json
from functools import lru_cache

from botocore.client import BaseClient

from app.db import make_dynamodb_client
from app.events import parse_event
from app.ledger import record_charge


# 領用窗口：DynamoDB 連線。同一個 Lambda 執行環境只建一次，下一則訊息沿用（測試時換成考場的）
@lru_cache(maxsize=1)
def get_client() -> BaseClient:
    return make_dynamodb_client()


# 每則一行 JSON 日誌：只放單號和金額，不放摘要、指紋、使用者
def log_charge(event_name: str, record: dict) -> None:
    entry = {
        "event": event_name,
        "request_id": record["request_id"],
        "cost_micro_usd": record["cost_micro_usd"],
    }
    print(json.dumps(entry), flush=True) # 馬上送出，不等緩衝


# 處理一則訊息：拆信封 → 三本帳一起寫；看不懂或寫不進去就往外丟，讓 SQS 重送、三次後進 DLQ
def process_message(client: BaseClient, body: str) -> bool:
    """Write one charge event into the ledger. Return False if it was already recorded."""
    record, period = parse_event(body)
    recorded = record_charge(client, record, period)
    if recorded:
        log_charge("charge_recorded", record)
    else:
        log_charge("charge_already_recorded", record)
    return recorded


# Lambda 的入口：SQS 送來的事件裡，訊息放在 event["Records"]，每一則的內容在 "body"
def handler(event: dict, context) -> None:
    """Lambda entry point for the SQS trigger."""
    client = get_client()
    for message in event["Records"]:
        process_message(client, message["body"])