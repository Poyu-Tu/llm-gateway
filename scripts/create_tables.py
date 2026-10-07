from app.db import API_KEYS_TABLE, QUOTAS_TABLE, AUDIT_TABLE


def create_tables(client):
    existing = client.list_tables()["TableNames"]

    if API_KEYS_TABLE not in existing:
        client.create_table(
            TableName=API_KEYS_TABLE,
            AttributeDefinitions=[
                {"AttributeName": "key_hash", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "key_hash", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

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