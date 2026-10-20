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
