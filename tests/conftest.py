"""Shared fixtures for tests."""

import os

import pytest

from app.db import make_dynamodb_client

# app/main.py 一載入就要讀 OPENAI_AUTH（沒設就起不來）。測試一律用金鑰模式：
# 用 = 不用 setdefault，這個視窗裡就算留著雲端的設定，也不會把測試帶去向 AWS 要證明
os.environ["OPENAI_AUTH"] = "api_key"

# app/main.py 一載入也要讀 CHARGE_QUEUE_URL（沒設就起不來）。測試一律先設 disabled：
# 同樣用 =，視窗裡就算留著雲端的佇列網址，也不會把測試帶去連真的 SQS；要測 SQS 那條路的測試自己換上 FakeSqs
os.environ["CHARGE_QUEUE_URL"] = "disabled"

# 考場的網址寫死在這裡：這個道具會刪掉所有資料表，絕不能被指到別的地方
TEST_ENDPOINT_URL = "http://127.0.0.1:8002"


# 每個測試拿到的都是空的考場：先把上一個測試留下的表全部刪掉
@pytest.fixture
def dynamodb(monkeypatch):
    """Return a client for the test-only DynamoDB Local, with all tables removed."""
    monkeypatch.setenv("DYNAMODB_TARGET", TEST_ENDPOINT_URL)
    client = make_dynamodb_client()
    for name in client.list_tables()["TableNames"]:
        client.delete_table(TableName=name)
    return client