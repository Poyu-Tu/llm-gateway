"""Tests for the Worker: read one charge event and write it into the ledger."""

import json

import pytest
from botocore.exceptions import ClientError

from app.events import InvalidEventError, build_event
from scripts.create_tables import create_tables
from worker.handler import handler, process_message

# 表名直接寫字串：常數打錯才抓得到
USAGE = "usage"
QUOTAS = "quotas"
AUDIT = "audit"
PERIOD = "2026-10"


# 測試道具：一筆成功請求的完整紀錄（欄位和 chat_endpoint() 寫的一樣，還沒有 charged）
def make_record(request_id="r1", **changes):
    record = {
        "request_id": request_id,
        "user_id": "alice",
        "timestamp": "2026-10-20T08:00:00+00:00",
        "prompt_hash": "f" * 64,
        "summary": "Send the bill to [EMAIL]",
        "pii_types": ["EMAIL"],
        "route_reason": "default",
        "routed_model": "gpt-6-luna",
        "fallback": False,
        "model": "gpt-6-luna",
        "provider_model": "gpt-6-luna",
        "input_tokens": 13,
        "output_tokens": 11,
        "reasoning_tokens": None,
        "finish_reason": "stop",
        "status": "ok",
        "cost_micro_usd": 7,
    }
    record.update(changes)
    return record


# 測試道具：讀當月已用量；沒有那一筆就回 None（分得出「0」和「根本沒寫」）
def read_used_or_none(client, user_id="alice"):
    key = {"user_id": {"S": user_id}, "period": {"S": PERIOD}}
    response = client.get_item(TableName=QUOTAS, Key=key, ConsistentRead=True)
    if "Item" not in response:
        return None
    return int(response["Item"]["used_micro_usd"]["N"])


# 測試道具：整張表有幾筆
def count_items(client, table):
    return client.scan(TableName=table, Select="COUNT")["Count"]


# 測試道具：把印出來的每一行日誌轉回 dict
def read_log_lines(capsys):
    lines = capsys.readouterr().out.strip().splitlines()
    return [json.loads(line) for line in lines]


# ---- 看不懂的訊息：不用連資料庫（還沒碰到資料庫就丟出去） ----


# 版本不對：往外丟，讓 SQS 重送、三次後進 DLQ（不當作成功、不刪掉訊息）
def test_process_message_raises_on_unknown_version():
    body = json.dumps({"version": 2, "period": PERIOD, "record": make_record()})

    with pytest.raises(InvalidEventError):
        process_message(object(), body)


# 不是 JSON：往外丟
def test_process_message_raises_on_non_json():
    with pytest.raises(InvalidEventError):
        process_message(object(), "not json")


# ---- 真的寫進 DynamoDB Local（考場，8002） ----


# 正常的一則：三本帳寫好、回 True、印一行 charge_recorded
@pytest.mark.integration
def test_process_message_records_the_charge(dynamodb, capsys):
    create_tables(dynamodb)

    result = process_message(dynamodb, build_event(make_record(), PERIOD))

    assert result is True
    assert count_items(dynamodb, USAGE) == 1
    assert read_used_or_none(dynamodb) == 7
    assert count_items(dynamodb, AUDIT) == 1
    assert read_log_lines(capsys) == [
        {"event": "charge_recorded", "request_id": "r1", "cost_micro_usd": 7}
    ]


# 同一則收到兩次（SQS 至少送到一次）：第二次回 False、不丟錯（SQS 會刪掉訊息），錢只扣一次
@pytest.mark.integration
def test_process_message_same_event_twice_charges_once(dynamodb, capsys):
    create_tables(dynamodb)
    body = build_event(make_record(), PERIOD)
    process_message(dynamodb, body)

    result = process_message(dynamodb, body)

    assert result is False
    assert read_used_or_none(dynamodb) == 7
    assert read_log_lines(capsys)[-1] == {
        "event": "charge_already_recorded",
        "request_id": "r1",
        "cost_micro_usd": 7,
    }


# 日誌只放單號和金額：摘要、指紋、使用者都不印
@pytest.mark.integration
def test_process_message_log_has_no_summary_or_hash(dynamodb, capsys):
    create_tables(dynamodb)

    process_message(dynamodb, build_event(make_record(), PERIOD))

    out = capsys.readouterr().out
    assert "Send the bill" not in out
    assert "f" * 64 not in out
    assert "alice" not in out


# 資料庫寫不進去（表不存在）：往外丟讓 SQS 重送，不當作已入帳
@pytest.mark.integration
def test_process_message_raises_when_ledger_write_fails(dynamodb):
    with pytest.raises(ClientError):
        process_message(dynamodb, build_event(make_record(), PERIOD))


# handler：把事件裡的每一則都交給 process_message（批次大小設 1，但不假設只有一則）
@pytest.mark.integration
def test_handler_records_every_message_in_the_event(dynamodb, monkeypatch):
    create_tables(dynamodb)
    monkeypatch.setattr("worker.handler.get_client", lambda: dynamodb)
    event = {
        "Records": [
            {"body": build_event(make_record("r1"), PERIOD)},
            {"body": build_event(make_record("r2", cost_micro_usd=100), PERIOD)},
        ]
    }

    handler(event, None)

    assert read_used_or_none(dynamodb) == 107
    assert count_items(dynamodb, USAGE) == 2


# handler 遇到看不懂的訊息：往外丟（Lambda 回報失敗，SQS 才會重送）
def test_handler_raises_on_a_bad_message(monkeypatch):
    monkeypatch.setattr("worker.handler.get_client", lambda: object())
    event = {"Records": [{"body": "not json"}]}

    with pytest.raises(InvalidEventError):
        handler(event, None)
