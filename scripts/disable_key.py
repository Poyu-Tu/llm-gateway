"""Disable API keys: one leaked key, or every key a user has.

Run from the repo root; DYNAMODB_TARGET says which database (a URL for DynamoDB Local, or aws):
    uv run python -m scripts.disable_key --key          (asks for the key, does not echo it)
    uv run python -m scripts.disable_key --user alice
"""

import argparse
import getpass

from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.auth import hash_api_key
from app.db import API_KEYS_TABLE, make_dynamodb_client

# 停用之後寫進 status 的值：驗票口只認 active，其他值一律擋下
DISABLED_STATUS = "disabled"
# 掃表時一頁看幾筆；測試會把它調小，確認翻頁之後的 Key 也有被停用
DEFAULT_PAGE_SIZE = 100


# 找不到要停用的 Key：一定要報錯，不能讓人以為已經停用了
class KeyNotFoundError(Exception):
    """The key to disable is not in the database."""


# 把一筆 Key 改成停用；這一筆不存在就報錯（DynamoDB 的更新預設會自己新建一筆）
def disable_key_hash(client: BaseClient, key_hash: str) -> None:
    """Set the key with this hash to disabled, or raise KeyNotFoundError when there is no such key."""
    try:
        client.update_item(
            TableName=API_KEYS_TABLE,
            Key={"key_hash": {"S": key_hash}},
            # status 是 DynamoDB 的保留字，要用 #status 代稱
            UpdateExpression="SET #status = :disabled",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":disabled": {"S": DISABLED_STATUS}},
            # 這一筆必須已經存在：打錯字時報錯，而不是新建一筆假的
            ConditionExpression="attribute_exists(key_hash)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise KeyNotFoundError("No such API key")
        # 不是「找不到」的錯誤（例如連不上）：原封不動往外丟，不能被說成找不到
        raise


# 停用一把外流的 Key：手上有的是 Key 本身，資料庫裡存的是它的雜湊
def disable_key(client: BaseClient, key: str) -> None:
    """Disable one API key, or raise KeyNotFoundError when it is not in the database."""
    disable_key_hash(client, hash_api_key(key))


# 停用一個人的所有 Key：表是用雜湊當主鍵，只能整張表掃過去、挑出這個人的
def disable_user_keys(client: BaseClient, user_id: str, page_size: int = DEFAULT_PAGE_SIZE) -> int:
    """Disable every key that belongs to the user and return how many were disabled."""
    paginator = client.get_paginator("scan")
    pages = paginator.paginate(
        TableName=API_KEYS_TABLE,
        FilterExpression="user_id = :user_id",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
        PaginationConfig={"PageSize": page_size},
    )

    count = 0
    for page in pages:
        for item in page["Items"]:
            disable_key_hash(client, item["key_hash"]["S"])
            count = count + 1
    return count


# 指令列：--key 停一把（用 getpass 輸入，不會出現在畫面和指令紀錄裡），--user 停一個人的全部
def main() -> None:
    """Disable a key or a user's keys, as asked on the command line."""
    parser = argparse.ArgumentParser(description="Disable API keys.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--key", action="store_true", help="disable one key (you will be asked for it)")
    group.add_argument("--user", help="disable every key of this user")
    args = parser.parse_args()

    client = make_dynamodb_client()
    if args.key:
        key = getpass.getpass("API key to disable: ")
        disable_key(client, key)
        print("Disabled 1 key.")
    else:
        count = disable_user_keys(client, args.user)
        print(f"Disabled {count} key(s) of {args.user}.")


if __name__ == "__main__":
    main()
