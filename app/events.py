"""Charge events: the message the Gateway sends to SQS and the Worker reads."""

import json

# 信封格式的版本：改格式時加一；Worker 看到不認得的版本就往外丟，三次後進 DLQ（M5 第 1、4 題）
EVENT_VERSION = 1


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