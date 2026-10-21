"""Charge events: the message the Gateway sends to SQS and the Worker reads."""

import json
import os

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from app.db import CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS, REGION, TOTAL_MAX_ATTEMPTS

# 信封格式的版本：改格式時加一；Worker 看到不認得的版本就往外丟，三次後進 DLQ（M5 第 1、4 題）
EVENT_VERSION = 1

# 佇列設定寫這個字，就是不用 SQS（本機、測試）：成功那條路直接記三本帳
QUEUE_DISABLED = "disabled"


# 看不懂的訊息：Worker 丟出這個錯誤，讓 SQS 重送、最後進 DLQ
class InvalidEventError(ValueError):
    """The message is not a charge event this Worker can read."""


# 組信封：版本、月份、原封不動的紀錄（月份不塞進紀錄，兩條路寫出來的 audit 才會一樣）
def build_event(record: dict, period: str) -> str:
    """Return the SQS message body for one paid request."""
    event = {
        "version": EVENT_VERSION,
        "period": period,
        "record": record,
    }
    return json.dumps(event)


# 拆信封：檢查格式，回傳紀錄與月份；看不懂就丟 InvalidEventError
def parse_event(body: str) -> tuple[dict, str]:
    """Return the record and period from a message body, or raise InvalidEventError."""
    try:
        event = json.loads(body)
    except json.JSONDecodeError as exc:
        raise InvalidEventError("Message is not JSON") from exc
    if not isinstance(event, dict):
        raise InvalidEventError("Message is not a JSON object")
    if event.get("version") != EVENT_VERSION:
        raise InvalidEventError("Unknown event version")
    record = event.get("record")
    period = event.get("period")
    if not isinstance(record, dict) or not isinstance(period, str):
        raise InvalidEventError("Message is missing the record or the period")
    return record, period


# 佇列網址一定要明講：寫網址就送 SQS、寫 disabled 就不用；沒寫或寫錯就報錯，Gateway 起不來（第二塊第 5 題）
def read_queue_url() -> str | None:
    """Return the charge queue URL, or None when SQS is disabled."""
    value = os.environ["CHARGE_QUEUE_URL"]
    if value == QUEUE_DISABLED:
        return None
    if value.startswith("https://"):
        return value
    raise ValueError(f"CHARGE_QUEUE_URL must be 'disabled' or an https URL, got: {value!r}")


# SQS 連線：逾時與重試比照 DynamoDB；DNS 被擋掉時要很快失敗，才會走備援
def make_sqs_client() -> BaseClient:
    """Return an SQS client in Tokyo that gives up quickly."""
    config = Config(
        connect_timeout=CONNECT_TIMEOUT_SECONDS,
        read_timeout=READ_TIMEOUT_SECONDS,
        retries={"total_max_attempts": TOTAL_MAX_ATTEMPTS, "mode": "standard"},
    )
    return boto3.client("sqs", region_name=REGION, config=config)


# 送出一筆記帳事件；送不進去的錯誤不在這裡接，交給 Gateway 改走備援
def send_event(client: BaseClient, queue_url: str, record: dict, period: str) -> None:
    """Send one charge event to this queue."""
    client.send_message(QueueUrl=queue_url, MessageBody=build_event(record, period))