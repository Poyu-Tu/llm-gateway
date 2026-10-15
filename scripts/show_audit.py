"""Show one audit record from the audit table. For local checks only."""

import sys

from boto3.dynamodb.types import TypeDeserializer
from botocore.client import BaseClient

from app.db import AUDIT_TABLE, make_dynamodb_client


# 用回應裡的 request_id 查那一筆稽核；強一致讀取，剛寫完一定讀得到；查不到回 None
def read_audit(client: BaseClient, request_id: str) -> dict | None:
    """Return the audit record as plain Python values, or None if there is none."""
    response = client.get_item(
        TableName=AUDIT_TABLE,
        Key={"request_id": {"S": request_id}},
        ConsistentRead=True,
    )
    item = response.get("Item")
    if item is None:
        return None
    # 和 write_audit() 相反：把 DynamoDB 的格式翻回 Python 的值
    deserializer = TypeDeserializer()
    record = {}
    for name, value in item.items():
        record[name] = deserializer.deserialize(value)
    return record


# 一行一欄、照欄位名稱排序印出；查不到就說查不到，結束碼 1
def main() -> None:
    request_id = sys.argv[1]
    record = read_audit(make_dynamodb_client(), request_id)
    if record is None:
        print(f"No audit record for {request_id}")
        sys.exit(1)
    for name in sorted(record):
        print(f"{name}: {record[name]}")


# 直接執行這個檔時才查；被測試 import 時不會自己跑
if __name__ == "__main__":
    main()
