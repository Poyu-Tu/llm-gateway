import pytest

from scripts.create_tables import create_tables

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration


# 建完之後三張表都在；表名直接寫字串，常數打錯才抓得到
def test_create_tables_creates_three_tables(dynamodb):
    create_tables(dynamodb)

    names = dynamodb.list_tables()["TableNames"]
    assert sorted(names) == ["api_keys", "audit", "quotas"]


# quotas 的主鍵是 user_id 加 period：少了 period，換月會蓋掉上個月的紀錄
def test_create_tables_gives_quotas_a_two_part_key(dynamodb):
    create_tables(dynamodb)

    schema = dynamodb.describe_table(TableName="quotas")["Table"]["KeySchema"]
    assert schema == [
        {"AttributeName": "user_id", "KeyType": "HASH"},
        {"AttributeName": "period", "KeyType": "RANGE"},
    ]


# api_keys 用雜湊值當主鍵：拿到 Key 的雜湊就能直接查
def test_create_tables_keys_api_keys_by_key_hash(dynamodb):
    create_tables(dynamodb)

    schema = dynamodb.describe_table(TableName="api_keys")["Table"]["KeySchema"]
    assert schema == [{"AttributeName": "key_hash", "KeyType": "HASH"}]


# audit 用 request_id 當主鍵：使用者拿回應裡的編號就能對回紀錄
def test_create_tables_keys_audit_by_request_id(dynamodb):
    create_tables(dynamodb)

    schema = dynamodb.describe_table(TableName="audit")["Table"]["KeySchema"]
    assert schema == [{"AttributeName": "request_id", "KeyType": "HASH"}]


# 重複執行不能出錯，也不能把已有的資料清掉
def test_create_tables_can_run_twice_and_keeps_data(dynamodb):
    create_tables(dynamodb)
    key = {"user_id": {"S": "alice"}, "period": {"S": "2026-10"}}
    dynamodb.put_item(TableName="quotas", Item=key)

    create_tables(dynamodb)

    assert "Item" in dynamodb.get_item(TableName="quotas", Key=key)