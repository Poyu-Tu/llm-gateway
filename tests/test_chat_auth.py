"""Tests for API key authentication on POST /v1/chat."""

import pytest
from fastapi.testclient import TestClient

from app.auth import hash_api_key
from app.db import API_KEYS_TABLE
from app.main import app, get_audit_path, get_client, get_dynamodb, get_hmac_key
from scripts.create_tables import create_tables
from tests.fakes import make_fake_client

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
# pytestmark = pytest.mark.integration
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skip(reason="authentication is not wired into main.py yet"),
]

# 測試用的假 Key：格式和真的一樣（gw_ 加 64 個字元），但一看就知道是假的
TEST_KEY = "gw_" + "a" * 64


# 測試道具：把 alice 的 Key 放進 api_keys；再呼叫一次會蓋掉同一筆，用來改狀態
def put_test_key(dynamodb, status):
    item = {
        "key_hash": {"S": hash_api_key(TEST_KEY)},
        "user_id": {"S": "alice"},
        "status": {"S": status},
    }
    dynamodb.put_item(TableName=API_KEYS_TABLE, Item=item)


# 測試道具：模型、金鑰、稽核檔換成假的；資料庫換成考場；驗證走真的
def make_auth_test_client(tmp_path, dynamodb):
    """Swap everything except authentication, and seed one active key."""
    fake_client, completions = make_fake_client()
    audit_path = tmp_path / "audit.jsonl"
    app.dependency_overrides.clear()
    app.dependency_overrides[get_client] = lambda: fake_client
    app.dependency_overrides[get_hmac_key] = lambda: b"test-key"
    app.dependency_overrides[get_audit_path] = lambda: audit_path
    app.dependency_overrides[get_dynamodb] = lambda: dynamodb
    create_tables(dynamodb)
    put_test_key(dynamodb, "active")
    return TestClient(app), completions, audit_path


def test_chat_accepts_valid_key(tmp_path, dynamodb):
    client, _, _ = make_auth_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers={"Authorization": "Bearer " + TEST_KEY})

    assert response.status_code == 200


def test_chat_rejects_missing_key(tmp_path, dynamodb):
    client, _, _ = make_auth_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication failed"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_chat_rejects_unknown_key(tmp_path, dynamodb):
    client, _, _ = make_auth_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"}, headers={"Authorization": "Bearer gw_wrong_key"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication failed"}


def test_chat_rejects_disabled_key(tmp_path, dynamodb):
    client, _, _ = make_auth_test_client(tmp_path, dynamodb)

    put_test_key(dynamodb, "disabled")
    response = client.post("/v1/chat", json={"message": "Say hi"}, headers={"Authorization": "Bearer " + TEST_KEY})

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication failed"}


def test_chat_rejected_request_reaches_neither_model_nor_audit(tmp_path, dynamodb):
    client, completions, audit_path = make_auth_test_client(tmp_path, dynamodb)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 401
    assert completions.last_request is None
    assert not audit_path.exists()
    
