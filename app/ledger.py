"""Ledger: write one paid request into the usage, quotas and audit tables together."""

from boto3.dynamodb.types import TypeSerializer
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.db import AUDIT_TABLE, QUOTAS_TABLE, USAGE_TABLE

# usage 一筆只記帳需要的欄位；路由理由、降級、個資類別留在 audit，不存兩份（M5 第 2 題）
USAGE_FIELDS = (
    "request_id",
    "model",
    "input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "cost_micro_usd",
)

# 交易被取消時，DynamoDB 對「不存在才寫」條件不成立的那一件事給的代碼
ALREADY_EXISTS_CODE = "ConditionalCheckFailed"


# usage 的排序鍵：時間在前、單號在後；照字串排就是照時間排，同一個時間的兩筆也不會撞
def usage_sort_key(timestamp: str, request_id: str) -> str:
    """Return the usage sort key: the timestamp, then the request id."""
    result = f"{timestamp}#{request_id}"
    return result


# Python 的值轉成 DynamoDB 的格式（字串變 S、整數變 N、None 變 NULL）
def to_dynamodb_item(values: dict) -> dict:
    """Return the values in DynamoDB's attribute-value format."""
    serializer = TypeSerializer()
    item = {}
    for name, value in values.items():
        item[name] = serializer.serialize(value)
    return item


# 交易被取消時判斷「是不是已經入過帳」：有事被擋、而且被擋的每一件都是「已經存在」才算重複
# 混了別的原因（例如 TransactionConflict）代表這次真的沒寫進去，要往外丟讓 SQS 重送
def is_duplicate(exc: ClientError) -> bool:
    """Return True only if the transaction was cancelled because the charge already exists."""
    if exc.response["Error"]["Code"] != "TransactionCanceledException":
        return False
    reasons = exc.response.get("CancellationReasons", [])
    codes = []
    for reason in reasons:
        code = reason.get("Code")
        if code != "None":
            codes.append(code)
    if not codes:
        return False
    for code in codes:
        if code != ALREADY_EXISTS_CODE:
            return False
    return True


# 一筆有花錢的請求，三本帳一起寫：usage 新增明細、quotas 加上成本、audit 寫稽核；要嘛全寫，要嘛全不寫
# Worker 與 Gateway 的備援共用這一支；用 request_id 去重，同一筆送兩次也只扣一次
def record_charge(client: BaseClient, record: dict, period: str) -> bool:
    """Write usage, quotas and audit in one transaction. Return False if already recorded."""
    # 準備三本要寫的資料
    audit_record = dict(record)
    audit_record["charged"] = True
    usage = {
        "user_id": record["user_id"],
        "ts_request": usage_sort_key(record["timestamp"], record["request_id"]),
        "period": period,
    }
    for name in USAGE_FIELDS:
        usage[name] = record[name]
    quota_key = {
        "user_id": {"S": record["user_id"]},
        "period": {"S": period},
    }
    # 一個交易三件事
    try:
        client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": USAGE_TABLE,
                        "Item": to_dynamodb_item(usage),
                        "ConditionExpression": "attribute_not_exists(user_id)",
                    }
                },
                {
                    "Update": {
                        "TableName": QUOTAS_TABLE,
                        "Key": quota_key,
                        "UpdateExpression": "ADD used_micro_usd :amount",
                        "ExpressionAttributeValues": {
                            ":amount": {"N": str(record["cost_micro_usd"])}
                        },
                    }
                },
                {
                    "Put": {
                        "TableName": AUDIT_TABLE,
                        "Item": to_dynamodb_item(audit_record),
                        "ConditionExpression": "attribute_not_exists(request_id)",
                    }
                },
            ]
        )
    except ClientError as exc:
        if is_duplicate(exc):
            return False
        raise
    return True