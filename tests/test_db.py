import pytest

from app.db import make_dynamodb_client


# 沒設定要連哪裡就不連：boto3 的預設是連真的 AWS
def test_make_dynamodb_client_requires_endpoint(monkeypatch):
    monkeypatch.delenv("DYNAMODB_ENDPOINT_URL", raising=False)

    with pytest.raises(KeyError):
        make_dynamodb_client()


# 連線指向環境變數給的網址；埠故意用 9999，函式把網址寫死就會被抓到
def test_make_dynamodb_client_uses_endpoint_from_env(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", "http://127.0.0.1:9999")

    client = make_dynamodb_client()

    assert client.meta.endpoint_url == "http://127.0.0.1:9999"