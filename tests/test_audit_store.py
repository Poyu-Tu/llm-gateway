"""Tests for writing audit records to the audit table, and for the fallback log line."""

import json

import pytest
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError, EndpointConnectionError

from app.audit import report_audit_failure, save_audit, write_audit
from app.db import AUDIT_TABLE
from scripts.create_tables import create_tables

# 日誌那一行只能有這些欄位：夠事後補收、對帳；摘要與指紋不能出現（D7）
FAILURE_LOG_KEYS = {
    "event",
    "request_id",
    "user_id",
    "timestamp",
    "status",
    "cost_micro_usd",
    "charged",
    "error_type",
}


# 測試道具：一筆成功請求的完整紀錄（欄位和 chat_endpoint() 寫的一樣）
def make_record(request_id="r1", **changes):
    record = {
        "request_id": request_id,
        "user_id": "alice",
        "timestamp": "2026-10-15T08:00:00+00:00",
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
        "charged": True,
    }
    record.update(changes)
    return record


# 測試道具：被額度擋下的那種紀錄，還沒有成本與扣款欄位
def make_blocked_record():
    record = make_record()
    for name in ["route_reason", "routed_model", "fallback", "model", "provider_model",
                 "input_tokens", "output_tokens", "reasoning_tokens", "finish_reason",
                 "cost_micro_usd", "charged"]:
        del record[name]
    record["status"] = "quota_exceeded"
    return record


# 測試道具：資料庫拒絕寫入時 boto3 丟出的錯誤
def make_client_error(code="AccessDeniedException"):
    return ClientError({"Error": {"Code": code, "Message": "denied"}}, "PutItem")


# 測試道具：只記下收到的 put_item，不真的寫
class RecordingDynamoDB:
    def __init__(self):
        self.puts = []

    def put_item(self, **kwargs):
        self.puts.append(kwargs)


# 測試道具：一寫就丟指定的錯誤
class FailingDynamoDB:
    def __init__(self, error):
        self.error = error

    def put_item(self, **kwargs):
        raise self.error


# 測試道具：用 request_id 讀回原始格式的那一筆（強一致讀取，剛寫完一定讀得到）
def read_raw_item(dynamodb, request_id):
    response = dynamodb.get_item(
        TableName=AUDIT_TABLE,
        Key={"request_id": {"S": request_id}},
        ConsistentRead=True,
    )
    return response["Item"]


# 測試道具：把原始格式轉回 Python 的值
def to_python(item):
    deserializer = TypeDeserializer()
    result = {}
    for name, value in item.items():
        result[name] = deserializer.deserialize(value)
    return result


# ---- 日誌那一行（不用資料庫）----


# 寫不進去時印剛好一行，而且整行是 JSON：CloudWatch 的指標篩選才抓得到
def test_report_audit_failure_prints_one_json_line(capsys):
    report_audit_failure(make_record(), make_client_error())

    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "audit_write_failed"
    assert entry["request_id"] == "r1"
    assert entry["user_id"] == "alice"
    assert entry["status"] == "ok"
    assert entry["cost_micro_usd"] == 7
    assert entry["charged"] is True
    assert entry["error_type"] == "ClientError"


# M6：花了錢、記帳兩條路都失敗的那一種，由呼叫的人指定事件名；其他欄位照舊
def test_report_audit_failure_can_use_another_event_name(capsys):
    report_audit_failure(make_record(), make_client_error(), event="charge_record_failed")

    entry = json.loads(capsys.readouterr().err)
    assert entry["event"] == "charge_record_failed"
    assert entry["error_type"] == "ClientError"


# 只印中繼資料：摘要、指紋、個資類別都不能出現在日誌（D7）
def test_report_audit_failure_leaves_out_summary_and_hash(capsys):
    report_audit_failure(make_record(), make_client_error())

    text = capsys.readouterr().err
    assert set(json.loads(text).keys()) == FAILURE_LOG_KEYS
    assert "[EMAIL]" not in text
    assert "f" * 64 not in text


# 被額度擋下的紀錄還沒有成本與扣款：照樣印得出來，那兩欄是 null，不能因為少欄位就出錯
def test_report_audit_failure_works_before_cost_is_known(capsys):
    report_audit_failure(make_blocked_record(), make_client_error())

    entry = json.loads(capsys.readouterr().err)
    assert entry["status"] == "quota_exceeded"
    assert entry["cost_micro_usd"] is None
    assert entry["charged"] is None


# 寫得進去就不印任何東西：日誌只在出事時出現，告警才不會一直響
def test_save_audit_stays_quiet_when_the_write_works(capsys):
    database = RecordingDynamoDB()

    save_audit(database, make_record())

    assert len(database.puts) == 1
    assert capsys.readouterr().err == ""


# 資料庫拒絕寫入：不往外丟錯誤（使用者照樣拿到回應），改印一行日誌
def test_save_audit_reports_when_the_database_refuses(capsys):
    save_audit(FailingDynamoDB(make_client_error()), make_record())

    entry = json.loads(capsys.readouterr().err)
    assert entry["request_id"] == "r1"
    assert entry["error_type"] == "ClientError"


# 連不上資料庫：同樣不往外丟，印一行日誌
def test_save_audit_reports_when_the_database_is_unreachable(capsys):
    error = EndpointConnectionError(endpoint_url="http://127.0.0.1:8002")

    save_audit(FailingDynamoDB(error), make_record())

    entry = json.loads(capsys.readouterr().err)
    assert entry["error_type"] == "EndpointConnectionError"


# 程式自己的錯（例如紀錄裡混進 DynamoDB 收不下的 float）不吞掉：要讓測試抓到，不是默默印一行
def test_save_audit_does_not_hide_programming_errors(capsys):
    with pytest.raises(TypeError):
        save_audit(RecordingDynamoDB(), make_record(cost_micro_usd=6.8))


# ---- 寫進 audit 表（要連 DynamoDB Local）----


# 寫進去的每一欄都讀得回來，值與型別不變
@pytest.mark.integration
def test_write_audit_stores_the_record(dynamodb):
    create_tables(dynamodb)
    record = make_record()

    write_audit(dynamodb, record)

    assert to_python(read_raw_item(dynamodb, "r1")) == record


# 個資類別存成清單（L）：順序照 EMAIL、CARD、PHONE、TW_ID 保留（D43）
@pytest.mark.integration
def test_write_audit_keeps_pii_types_as_an_ordered_list(dynamodb):
    create_tables(dynamodb)

    write_audit(dynamodb, make_record(pii_types=["EMAIL", "CARD", "PHONE", "TW_ID"]))

    item = read_raw_item(dynamodb, "r1")
    assert item["pii_types"] == {"L": [{"S": "EMAIL"}, {"S": "CARD"}, {"S": "PHONE"}, {"S": "TW_ID"}]}


# 空清單也要存得進去：空的代表「檢查過、沒找到」，和「沒檢查」不同（D43）
@pytest.mark.integration
def test_write_audit_keeps_an_empty_pii_types_list(dynamodb):
    create_tables(dynamodb)

    write_audit(dynamodb, make_record(pii_types=[]))

    item = read_raw_item(dynamodb, "r1")
    assert item["pii_types"] == {"L": []}


# 沒有值的欄位（例如沒有推理 token 明細）存成 NULL，不是漏掉那一欄
@pytest.mark.integration
def test_write_audit_stores_missing_values_as_null(dynamodb):
    create_tables(dynamodb)

    write_audit(dynamodb, make_record(reasoning_tokens=None))

    item = read_raw_item(dynamodb, "r1")
    assert item["reasoning_tokens"] == {"NULL": True}


# 同一個 request_id 不能被蓋掉：第二次寫要被拒絕，留下的是第一筆
@pytest.mark.integration
def test_write_audit_never_overwrites_a_record(dynamodb):
    create_tables(dynamodb)
    write_audit(dynamodb, make_record(status="ok"))

    with pytest.raises(ClientError) as raised:
        write_audit(dynamodb, make_record(status="error"))

    assert raised.value.response["Error"]["Code"] == "ConditionalCheckFailedException"
    assert to_python(read_raw_item(dynamodb, "r1"))["status"] == "ok"


# 表不存在（例如 Terraform 漏建）：不往外丟，印一行日誌
# boto3 會把這種錯誤轉成 ClientError 底下的專屬類別，日誌記到的就是那個名字
@pytest.mark.integration
def test_save_audit_reports_when_the_table_is_missing(dynamodb, capsys):
    save_audit(dynamodb, make_record())

    entry = json.loads(capsys.readouterr().err)
    assert entry["request_id"] == "r1"
    assert entry["error_type"] == "ResourceNotFoundException"
