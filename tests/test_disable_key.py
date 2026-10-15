"""Tests for the script that disables API keys."""

import pytest

from app.auth import find_user_id, hash_api_key
from app.db import API_KEYS_TABLE
from scripts.create_tables import create_tables
from scripts.disable_key import KeyNotFoundError, disable_key, disable_user_keys
from scripts.seed import seed_user

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration


# 測試道具：api_keys 表裡現在有幾筆
def count_keys(client):
    return client.scan(TableName=API_KEYS_TABLE, Select="COUNT")["Count"]


# 測試道具：直接讀出這把 Key 那一筆的 status
def status_of(client, key):
    item = client.get_item(TableName=API_KEYS_TABLE, Key={"key_hash": {"S": hash_api_key(key)}})["Item"]
    return item["status"]["S"]


# 停用之後，驗票口就認不得這把 Key
def test_disable_key_stops_the_key_from_working(dynamodb):
    create_tables(dynamodb)
    key = seed_user(dynamodb, "alice", 1000)

    disable_key(dynamodb, key)

    assert find_user_id(dynamodb, hash_api_key(key)) is None
    assert status_of(dynamodb, key) == "disabled"


# 只改 status：這把 Key 是誰的要留著，事後才查得到
def test_disable_key_keeps_the_owner(dynamodb):
    create_tables(dynamodb)
    key = seed_user(dynamodb, "alice", 1000)

    disable_key(dynamodb, key)

    item = dynamodb.get_item(TableName=API_KEYS_TABLE, Key={"key_hash": {"S": hash_api_key(key)}})["Item"]
    assert item["user_id"]["S"] == "alice"


# 打錯字：要報錯，而且不能在表裡多出一筆
def test_disable_key_rejects_an_unknown_key_without_creating_one(dynamodb):
    create_tables(dynamodb)
    seed_user(dynamodb, "alice", 1000)

    with pytest.raises(KeyNotFoundError):
        disable_key(dynamodb, "gw_this-key-does-not-exist")

    assert count_keys(dynamodb) == 1


# 只停那一把：別人的 Key 照常能用
def test_disable_key_leaves_other_keys_working(dynamodb):
    create_tables(dynamodb)
    alice_key = seed_user(dynamodb, "alice", 1000)
    bob_key = seed_user(dynamodb, "bob", 1000)

    disable_key(dynamodb, alice_key)

    assert find_user_id(dynamodb, hash_api_key(bob_key)) == "bob"


# 停一個人：他的每一把都停掉，並回報停了幾把
def test_disable_user_keys_disables_every_key_of_the_user(dynamodb):
    create_tables(dynamodb)
    first = seed_user(dynamodb, "alice", 1000)
    second = seed_user(dynamodb, "alice", 1000)

    count = disable_user_keys(dynamodb, "alice")

    assert count == 2
    assert find_user_id(dynamodb, hash_api_key(first)) is None
    assert find_user_id(dynamodb, hash_api_key(second)) is None


# 停一個人：別人的不能被一起停掉
def test_disable_user_keys_leaves_other_users_working(dynamodb):
    create_tables(dynamodb)
    seed_user(dynamodb, "alice", 1000)
    bob_key = seed_user(dynamodb, "bob", 1000)

    disable_user_keys(dynamodb, "alice")

    assert find_user_id(dynamodb, hash_api_key(bob_key)) == "bob"


# 沒有這個人：停了 0 把，表裡也不能多出東西
def test_disable_user_keys_returns_zero_for_an_unknown_user(dynamodb):
    create_tables(dynamodb)
    seed_user(dynamodb, "alice", 1000)

    count = disable_user_keys(dynamodb, "nobody")

    assert count == 0
    assert count_keys(dynamodb) == 1


# 掃表是一頁一頁回來的：一頁只看 1 筆時，後面幾頁的 Key 也要被停掉
def test_disable_user_keys_reads_every_page(dynamodb):
    create_tables(dynamodb)
    keys = [seed_user(dynamodb, "alice", 1000) for _ in range(3)]
    seed_user(dynamodb, "bob", 1000)

    count = disable_user_keys(dynamodb, "alice", page_size=1)

    assert count == 3
    for key in keys:
        assert find_user_id(dynamodb, hash_api_key(key)) is None
