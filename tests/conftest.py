"""Shared fixtures for tests."""

import pytest

from app.db import make_dynamodb_client

# 考場的網址寫死在這裡：這個道具會刪掉所有資料表，絕不能被指到別的地方
TEST_ENDPOINT_URL = "http://127.0.0.1:8002"


# 每個測試拿到的都是空的考場：先把上一個測試留下的表全部刪掉
@pytest.fixture
def dynamodb(monkeypatch):
    """Return a client for the test-only DynamoDB Local, with all tables removed."""
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", TEST_ENDPOINT_URL)
    client = make_dynamodb_client()
    for name in client.list_tables()["TableNames"]:
        client.delete_table(TableName=name)
    return client