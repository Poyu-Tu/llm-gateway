"""Tests for GET /v1/me: the Console's login check (who am I, how much quota is left)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_client, get_dynamodb, get_quota, get_user_id
from tests.fakes import make_fake_client


# 每個測試跑完都把換掉的領用窗口還原，避免影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    app.dependency_overrides.clear()


# 測試道具：查不到任何 Key 的資料庫（每一把 Key 都不認得）
class EmptyKeyTable:
    """Stands in for a DynamoDB client whose api_keys table has no matching key."""

    def get_item(self, **kwargs):
        return {}


# 登入成功：回名稱和這個月的額度（上限、已用），Console 拿來問好、畫額度條
def test_me_returns_the_user_and_quota():
    app.dependency_overrides[get_user_id] = lambda: "alice"
    app.dependency_overrides[get_quota] = lambda: (1000, 250)
    client = TestClient(app)

    response = client.get("/v1/me")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "alice",
        "quota": {"limit_micro_usd": 1000, "used_micro_usd": 250},
    }


# 登入是免費的：只驗 Key、讀額度，不呼叫模型（假的模型一次都沒被叫到）
def test_me_never_calls_the_model():
    fake_client, completions = make_fake_client()
    app.dependency_overrides[get_client] = lambda: fake_client
    app.dependency_overrides[get_user_id] = lambda: "alice"
    app.dependency_overrides[get_quota] = lambda: (1000, 0)
    client = TestClient(app)

    client.get("/v1/me")

    assert completions.requests == []


# 沒帶 Key、或 Key 不認得：跟 /v1/chat 一樣回 401，Console 停在登入頁
def test_me_rejects_missing_or_unknown_key():
    app.dependency_overrides[get_dynamodb] = lambda: EmptyKeyTable()
    client = TestClient(app)

    missing = client.get("/v1/me")
    unknown = client.get("/v1/me", headers={"Authorization": "Bearer gw_" + "0" * 64})

    assert missing.status_code == 401
    assert unknown.status_code == 401
    assert "user_id" not in unknown.json()
