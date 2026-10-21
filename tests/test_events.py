"""Tests for the charge event: the envelope the Gateway sends and the Worker reads."""

import json

import pytest

from app.events import EVENT_VERSION, InvalidEventError, build_event, parse_event

PERIOD = "2026-10"


# 測試道具：一筆成功請求的紀錄（欄位種類齊全：字串、整數、None、布林、清單）
def make_record(**changes):
    record = {
        "request_id": "r1",
        "user_id": "alice",
        "timestamp": "2026-10-20T08:00:00+00:00",
        "summary": "Send the bill to [EMAIL]",
        "pii_types": ["EMAIL"],
        "fallback": False,
        "model": "gpt-6-luna",
        "input_tokens": 13,
        "output_tokens": 11,
        "reasoning_tokens": None,
        "status": "ok",
        "cost_micro_usd": 7,
    }
    record.update(changes)
    return record


# 測試道具：自己組一個信封（用來做格式壞掉的訊息）
def make_body(**envelope):
    return json.dumps(envelope)


# ---- 組信封（Gateway 用） ----


# 現在的格式是第 1 版
def test_event_version_is_one():
    assert EVENT_VERSION == 1


# 信封三個欄位：版本、月份、原封不動的紀錄
def test_build_event_wraps_record_with_version_and_period():
    body = build_event(make_record(), PERIOD)

    assert json.loads(body) == {"version": 1, "period": "2026-10", "record": make_record()}


# 月份放在信封上，不塞進紀錄：呼叫者手上那份不被改到，audit 也不會多一個欄位
def test_build_event_does_not_put_period_into_record():
    record = make_record()

    body = build_event(record, PERIOD)

    assert "period" not in record
    assert "period" not in json.loads(body)["record"]


# ---- 拆信封（Worker 用） ----


# 組好再拆，拿回同一份紀錄與月份（中文、None、布林、清單都還原）
def test_parse_event_returns_record_and_period():
    record = make_record(summary="把帳單寄給 [EMAIL]")

    result = parse_event(build_event(record, PERIOD))

    assert result == (record, PERIOD)


# 不是 JSON：看不懂
def test_parse_event_rejects_non_json():
    with pytest.raises(InvalidEventError):
        parse_event("not json")


# 是 JSON 但不是一個物件：看不懂
def test_parse_event_rejects_json_that_is_not_an_object():
    with pytest.raises(InvalidEventError):
        parse_event("[1, 2]")


# 不認得的版本（例如 Gateway 先部署了第 2 版）：看不懂，不能照第 1 版硬記
def test_parse_event_rejects_unknown_version():
    body = make_body(version=2, period=PERIOD, record=make_record())

    with pytest.raises(InvalidEventError):
        parse_event(body)


# 沒有版本：看不懂
def test_parse_event_rejects_missing_version():
    body = make_body(period=PERIOD, record=make_record())

    with pytest.raises(InvalidEventError):
        parse_event(body)


# 少了紀錄：看不懂
def test_parse_event_rejects_missing_record():
    body = make_body(version=1, period=PERIOD)

    with pytest.raises(InvalidEventError):
        parse_event(body)


# 少了月份：看不懂（Worker 不自己算月份）
def test_parse_event_rejects_missing_period():
    body = make_body(version=1, record=make_record())

    with pytest.raises(InvalidEventError):
        parse_event(body)


# 紀錄不是物件：看不懂
def test_parse_event_rejects_record_that_is_not_an_object():
    body = make_body(version=1, period=PERIOD, record="r1")

    with pytest.raises(InvalidEventError):
        parse_event(body)
