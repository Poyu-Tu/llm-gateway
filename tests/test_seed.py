"""Tests for the seed script that creates demo users."""

import json

import pytest

from app.auth import find_user_id, hash_api_key
from app.quota import read_limit
from scripts.create_tables import create_tables
from scripts.seed import generate_api_key, seed_user
from tests.test_chat_quota import make_quota_test_client

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration


# Key 的長相：gw_ 開頭，後面 64 個十六進位字元，總長 67
def test_generate_api_key_has_prefix_and_length():
    key = generate_api_key()

    assert key.startswith("gw_")
    assert len(key) == 67


# 每次產生的都不一樣：寫死成固定值的話，所有人會拿到同一把 Key
def test_generate_api_key_is_different_every_time():
    assert generate_api_key() != generate_api_key()


# 交回來的 Key 要真的能用：算成雜湊後查得到這個人
def test_seed_user_returns_a_key_that_identifies_the_user(dynamodb):
    create_tables(dynamodb)

    key = seed_user(dynamodb, "alice", 1000)

    assert find_user_id(dynamodb, hash_api_key(key)) == "alice"


# 資料庫裡找不到 Key 本身，只有雜湊：整張表被搬走也拿不到能用的 Key
def test_seed_user_stores_only_the_hash(dynamodb):
    create_tables(dynamodb)

    key = seed_user(dynamodb, "alice", 1000)

    items = dynamodb.scan(TableName="api_keys")["Items"]
    assert len(items) == 1
    assert key not in str(items)
    assert items[0]["key_hash"]["S"] == hash_api_key(key)


# 額度要寫進使用者層級的那一筆，額度檢查才讀得到
def test_seed_user_sets_the_monthly_limit(dynamodb):
    create_tables(dynamodb)

    seed_user(dynamodb, "alice", 1000)

    assert read_limit(dynamodb, "alice") == 1000


# 兩個人各拿各的 Key、各有各的額度，互不影響
def test_seed_user_keeps_users_separate(dynamodb):
    create_tables(dynamodb)

    alice_key = seed_user(dynamodb, "alice", 1000)
    bob_key = seed_user(dynamodb, "bob", 1_000_000)

    assert find_user_id(dynamodb, hash_api_key(alice_key)) == "alice"
    assert find_user_id(dynamodb, hash_api_key(bob_key)) == "bob"
    assert read_limit(dynamodb, "alice") == 1000
    assert read_limit(dynamodb, "bob") == 1_000_000


# 從頭走到尾：種子腳本建出來的人，拿他的 Key 真的打得通對話入口，稽核記的也是他
def test_seeded_user_can_call_chat(tmp_path, dynamodb):
    client, _, audit_path = make_quota_test_client(tmp_path, dynamodb)
    key = seed_user(dynamodb, "bob", 1000)

    response = client.post(
        "/v1/chat",
        json={"message": "Say hi"},
        headers={"Authorization": "Bearer " + key},
    )

    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert response.status_code == 200
    assert record["user_id"] == "bob"
