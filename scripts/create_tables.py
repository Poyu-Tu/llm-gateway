from botocore.client import BaseClient

from app.db import API_KEYS_TABLE, QUOTAS_TABLE, AUDIT_TABLE


# 建表放在 scripts/，不放 app/：Gateway 在雲端不該有建表的權限
def create_tables(client: BaseClient) -> None:
    """Create the tables this milestone needs, skipping any that already exist."""
    # 已經存在的表就跳過：重複執行不會報錯，也不會清掉裡面的資料
    existing = client.list_tables()["TableNames"]

    # 主鍵是 key_hash：Gateway 手上只有 Key 的雜湊，要拿它查出是誰
    if API_KEYS_TABLE not in existing:
        client.create_table(
            TableName=API_KEYS_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "key_hash", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "key_hash", "KeyType": "HASH"},
            ],
            # 練習場用隨用隨付；雲端用哪一種留到 M4 決定
            BillingMode="PAY_PER_REQUEST",
        )

    # user_id + period：換月自然是新的一筆，不用寫每月重置的排程
    if QUOTAS_TABLE not in existing:
        client.create_table(
            TableName=QUOTAS_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "period", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "period", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

    # 一筆請求一筆紀錄，事後用 request_id 找
    if AUDIT_TABLE not in existing:
        client.create_table(
            TableName=AUDIT_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "request_id", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "request_id", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )