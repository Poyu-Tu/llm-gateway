"""Tests for writing one paid request into usage, quotas and audit together."""

import pytest
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

from app.ledger import is_duplicate, record_charge, usage_sort_key
from scripts.create_tables import create_tables

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


# 測試道具：把 DynamoDB 格式轉回 Python 的值
def to_python(item):
    deserializer = TypeDeserializer()
    result = {}
    for name, value in item.items():
        result[name] = deserializer.deserialize(value)
    return result


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


# 測試道具：做一個交易被取消的錯誤；codes 是每一件事被取消的原因
def make_cancelled_error(codes):
    response = {
        "Error": {"Code": "TransactionCanceledException", "Message": "cancelled"},
        "CancellationReasons": [{"Code": code} for code in codes],
    }
    return ClientError(response, "TransactWriteItems")


# ---- 排序鍵與「是不是重複」的判斷：不用連資料庫 ----


# 排序鍵是「時間#單號」：時間在前才能照時間排、用時間範圍查
def test_usage_sort_key_puts_timestamp_first():
    result = usage_sort_key("2026-10-20T08:00:00+00:00", "r1")

    assert result == "2026-10-20T08:00:00+00:00#r1"


# 每一件被取消的原因都是「已經存在」：重複
def test_is_duplicate_when_all_reasons_are_already_exists():
    error = make_cancelled_error(["ConditionalCheckFailed", "None", "ConditionalCheckFailed"])

    assert is_duplicate(error) is True


# 只有一件是「已經存在」、其他沒問題：也是重複（usage 還在、audit 被手動補過之類的情況）
def test_is_duplicate_when_one_reason_is_already_exists():
    error = make_cancelled_error(["None", "None", "ConditionalCheckFailed"])

    assert is_duplicate(error) is True


# 混了別的原因（同時有人在改同一筆額度）：不是重複，是真的沒寫進去，要讓呼叫的人重試
def test_is_not_duplicate_when_a_reason_is_conflict():
    error = make_cancelled_error(["ConditionalCheckFailed", "TransactionConflict", "None"])

    assert is_duplicate(error) is False


# 取消了卻沒有任何原因：不能猜成重複
def test_is_not_duplicate_without_reasons():
    error = make_cancelled_error(["None", "None", "None"])

    assert is_duplicate(error) is False


# 不是交易被取消（例如表不存在）：不是重複
def test_is_not_duplicate_for_other_errors():
    response = {"Error": {"Code": "ResourceNotFoundException", "Message": "no table"}}
    error = ClientError(response, "TransactWriteItems")

    assert is_duplicate(error) is False


# ---- 真的寫進 DynamoDB Local（考場，8002） ----


# 第一次寫：回 True，三本帳都有
@pytest.mark.integration
def test_record_charge_writes_all_three(dynamodb):
    create_tables(dynamodb)

    result = record_charge(dynamodb, make_record(), PERIOD)

    assert result is True
    assert count_items(dynamodb, USAGE) == 1
    assert read_used_or_none(dynamodb) == 7
    assert count_items(dynamodb, AUDIT) == 1


# usage 那一筆：主鍵是 user_id ＋「時間#單號」，只有記帳要的欄位
@pytest.mark.integration
def test_record_charge_usage_row_has_only_billing_fields(dynamodb):
    create_tables(dynamodb)

    record_charge(dynamodb, make_record(), PERIOD)

    items = dynamodb.scan(TableName=USAGE)["Items"]
    assert to_python(items[0]) == {
        "user_id": "alice",
        "ts_request": "2026-10-20T08:00:00+00:00#r1",
        "period": "2026-10",
        "request_id": "r1",
        "model": "gpt-6-luna",
        "input_tokens": 13,
        "output_tokens": 11,
        "reasoning_tokens": None,
        "cost_micro_usd": 7,
    }


# audit 那一筆：完整稽核加上 charged=True；呼叫的人手上那一份不被改到
@pytest.mark.integration
def test_record_charge_marks_audit_as_charged(dynamodb):
    create_tables(dynamodb)
    record = make_record()

    record_charge(dynamodb, record, PERIOD)

    key = {"request_id": {"S": "r1"}}
    item = to_python(dynamodb.get_item(TableName=AUDIT, Key=key)["Item"])
    assert item["charged"] is True
    assert item["summary"] == "Send the bill to [EMAIL]"
    assert "charged" not in record


# 已經用過一些：用「加上去」，不是蓋掉
@pytest.mark.integration
def test_record_charge_adds_to_existing_usage(dynamodb):
    create_tables(dynamodb)
    record_charge(dynamodb, make_record("r1"), PERIOD)

    record_charge(dynamodb, make_record("r2", cost_micro_usd=100), PERIOD)

    assert read_used_or_none(dynamodb) == 107
    assert count_items(dynamodb, USAGE) == 2


# 同一筆送兩次（SQS 至少送到一次）：第二次回 False，錢只扣一次
@pytest.mark.integration
def test_record_charge_same_request_twice_charges_once(dynamodb):
    create_tables(dynamodb)
    record_charge(dynamodb, make_record(), PERIOD)

    result = record_charge(dynamodb, make_record(), PERIOD)

    assert result is False
    assert read_used_or_none(dynamodb) == 7
    assert count_items(dynamodb, USAGE) == 1
    assert count_items(dynamodb, AUDIT) == 1


# 只有 usage 那一筆已經在（audit 沒有）：靠 usage 的「不存在才寫」擋下，回 False、錢不重扣
@pytest.mark.integration
def test_record_charge_stops_when_usage_row_already_exists(dynamodb):
    create_tables(dynamodb)
    usage_key_only = {
        "user_id": {"S": "alice"},
        "ts_request": {"S": "2026-10-20T08:00:00+00:00#r1"},
    }
    dynamodb.put_item(TableName=USAGE, Item=usage_key_only)

    result = record_charge(dynamodb, make_record(), PERIOD)

    assert result is False
    assert read_used_or_none(dynamodb) is None
    assert count_items(dynamodb, AUDIT) == 0


# 只有 audit 那一筆已經在（usage 沒有）：靠 audit 的「不存在才寫」擋下，回 False、錢不重扣
@pytest.mark.integration
def test_record_charge_stops_when_audit_row_already_exists(dynamodb):
    create_tables(dynamodb)
    dynamodb.put_item(TableName=AUDIT, Item={"request_id": {"S": "r1"}})

    result = record_charge(dynamodb, make_record(), PERIOD)

    assert result is False
    assert read_used_or_none(dynamodb) is None
    assert count_items(dynamodb, USAGE) == 0


# 寫到一半有一本帳不能寫（這裡是 usage 表不存在）：錯誤往外丟，而且另外兩本也沒寫——要嘛全寫，要嘛全不寫
@pytest.mark.integration
def test_record_charge_writes_nothing_when_one_part_fails(dynamodb):
    create_tables(dynamodb)
    dynamodb.delete_table(TableName=USAGE)

    with pytest.raises(ClientError):
        record_charge(dynamodb, make_record(), PERIOD)

    assert read_used_or_none(dynamodb) is None
    assert count_items(dynamodb, AUDIT) == 0
