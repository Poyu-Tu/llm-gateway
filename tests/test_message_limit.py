"""Tests that pin the length limit of one message on POST /v1/chat (4,000 characters)."""

from fastapi import HTTPException

from app.main import app, get_user_id
from tests.test_chat import make_test_client

# 上限在這裡再寫一次是故意的：主程式的數字被改掉時，要有另一個地方對得出來
MAX_MESSAGE_CHARS = 4000


# 剛好 4,000 個字：放行
def test_message_at_the_limit_is_accepted(tmp_path):
    client, _, _ = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "a" * MAX_MESSAGE_CHARS})

    assert response.status_code == 200


# 多一個字：被擋、回 422
def test_message_one_over_the_limit_is_rejected(tmp_path):
    client, _, _ = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "a" * (MAX_MESSAGE_CHARS + 1)})

    assert response.status_code == 422


# 被擋的請求碰不到模型，也不留稽核（先確認狀態碼是 422，才檢查「沒發生」的事）
def test_rejected_message_never_reaches_the_model(tmp_path):
    client, completions, audit_path = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "a" * (MAX_MESSAGE_CHARS + 1)})

    assert response.status_code == 422
    assert completions.requests == []
    assert not audit_path.exists()


# 算的是「字」不是「位元組」：4,000 個中文字（約 12,000 位元組）照樣放行
def test_limit_counts_characters_not_bytes(tmp_path):
    client, _, _ = make_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "字" * MAX_MESSAGE_CHARS})

    assert response.status_code == 200


# Key 是錯的又超長：先回 401，不讓沒通過驗證的人從 422 知道長度規則
def test_bad_key_gets_401_even_when_the_message_is_too_long(tmp_path):
    client, _, _ = make_test_client(tmp_path)

    def deny():
        raise HTTPException(status_code=401, detail="Authentication failed")

    app.dependency_overrides[get_user_id] = deny

    response = client.post("/v1/chat", json={"message": "a" * (MAX_MESSAGE_CHARS + 1)})

    assert response.status_code == 401
