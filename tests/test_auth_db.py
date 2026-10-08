import pytest

from app.auth import find_user_id
from app.db import API_KEYS_TABLE
from scripts.create_tables import create_tables

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration


# 測試道具：往 api_keys 放一筆；status 給 None 就不寫這個欄位
def put_key(client, key_hash, user_id, status):
    item = {"key_hash": {"S": key_hash}, "user_id": {"S": user_id}}
    if status is not None:
        item["status"] = {"S": status}
    client.put_item(TableName=API_KEYS_TABLE, Item=item)


# 有效的 Key：查得到是誰
def test_find_user_id_returns_user_for_active_key(dynamodb):
    create_tables(dynamodb)
    put_key(dynamodb, "hash-a", "alice", "active")

    result = find_user_id(dynamodb, "hash-a")

    assert result == "alice"


# 表裡有別人的 Key 時，拿一把不存在的去查，不能交出任何人
def test_find_user_id_returns_none_for_unknown_key(dynamodb):
    create_tables(dynamodb)
    put_key(dynamodb, "hash-a", "alice", "active")

    result = find_user_id(dynamodb, "hash-b")

    assert result is None


# 被停用的 Key 不能用；紀錄留著是為了查得到它曾經是誰的
def test_find_user_id_rejects_disabled_key(dynamodb):
    create_tables(dynamodb)
    put_key(dynamodb, "hash-a", "alice", "disabled")

    result = find_user_id(dynamodb, "hash-a")

    assert result is None


# 狀態欄不存在時不能當成有效：不知道就拒絕
def test_find_user_id_rejects_key_without_status(dynamodb):
    create_tables(dynamodb)
    put_key(dynamodb, "hash-a", "alice", None)

    result = find_user_id(dynamodb, "hash-a")

    assert result is None