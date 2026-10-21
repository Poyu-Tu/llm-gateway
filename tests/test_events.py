"""Tests for the charge event: the envelope the Gateway sends and the Worker reads."""

import json

import boto3
import pytest
from botocore.exceptions import ClientError

from app.events import (
    EVENT_VERSION,
    QUEUE_DISABLED,
    InvalidEventError,
    build_event,
    make_sqs_client,
    parse_event,
    read_queue_url,
    send_event,
)
from tests.fakes import FakeSqs

PERIOD = "2026-10"
# 假的佇列網址：帳號 ID 用 12 個 0，不寫真的
QUEUE_URL = "https://sqs.ap-northeast-1.amazonaws.com/000000000000/charge-events"


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


# ---- 佇列網址的設定（Gateway 啟動時讀） ----


# 寫 disabled：不用 SQS（本機、測試），回 None
def test_read_queue_url_returns_none_when_disabled(monkeypatch):
    monkeypatch.setenv("CHARGE_QUEUE_URL", QUEUE_DISABLED)

    assert read_queue_url() is None


# 寫 https 網址：照原樣回傳
def test_read_queue_url_returns_the_https_url(monkeypatch):
    monkeypatch.setenv("CHARGE_QUEUE_URL", QUEUE_URL)

    assert read_queue_url() == QUEUE_URL


# 沒寫：直接報錯（Gateway 起不來），不讓它安靜地變回同步記帳
def test_read_queue_url_requires_the_setting(monkeypatch):
    monkeypatch.delenv("CHARGE_QUEUE_URL", raising=False)

    with pytest.raises(KeyError):
        read_queue_url()


# 寫錯（空白、大寫、http、少了 https://）：直接報錯
@pytest.mark.parametrize(
    "value",
    ["", "DISABLED", "http://sqs.ap-northeast-1.amazonaws.com/000000000000/q", "sqs.ap-northeast-1.amazonaws.com/q"],
)
def test_read_queue_url_rejects_unknown_values(monkeypatch, value):
    monkeypatch.setenv("CHARGE_QUEUE_URL", value)

    with pytest.raises(ValueError):
        read_queue_url()


# ---- SQS 連線（只看設定，不真的連線） ----


# 身分用假的，免得讀到這台電腦上真的 AWS 身分（同 test_db.py）
@pytest.fixture
def fake_aws_identity(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIA-FROM-THE-ROLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret-from-the-role")
    monkeypatch.setattr(boto3, "DEFAULT_SESSION", None)


# 連東京的 SQS
def test_make_sqs_client_uses_tokyo(fake_aws_identity):
    client = make_sqs_client()

    assert client.meta.service_model.service_name == "sqs"
    assert client.meta.region_name == "ap-northeast-1"


# 逾時與重試比照 DynamoDB：DNS 被擋時要很快失敗，才會走備援
def test_make_sqs_client_gives_up_quickly(fake_aws_identity):
    client = make_sqs_client()

    assert client.meta.config.connect_timeout == 2
    assert client.meta.config.read_timeout == 5
    assert client.meta.config.retries == {"total_max_attempts": 2, "mode": "standard"}


# ---- 送出（Gateway 用，SQS 用替身） ----


# 送到指定的佇列，內容就是 build_event() 組好的信封
def test_send_event_sends_the_envelope_to_the_queue():
    sqs = FakeSqs()
    record = make_record()

    send_event(sqs, QUEUE_URL, record, PERIOD)

    assert sqs.sent == [{"QueueUrl": QUEUE_URL, "MessageBody": build_event(record, PERIOD)}]


# 送不進去：錯誤往外丟，由 Gateway 決定改走備援（這裡不接）
def test_send_event_lets_the_error_out():
    response = {"Error": {"Code": "AccessDenied", "Message": "no"}}
    sqs = FakeSqs(error=ClientError(response, "SendMessage"))

    with pytest.raises(ClientError):
        send_event(sqs, QUEUE_URL, make_record(), PERIOD)
