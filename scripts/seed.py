"""Seed the practice database with demo users. For local use only."""

import secrets

from botocore.client import BaseClient

from app.auth import hash_api_key
from app.db import API_KEYS_TABLE, QUOTAS_TABLE, make_dynamodb_client
from app.quota import LIMIT_SORT_KEY
from scripts.create_tables import create_tables

# Key 的固定開頭：一眼看得出是這個 Gateway 的 Key，外流時也方便用掃描工具找
API_KEY_PREFIX = "gw_"

# 示範用的兩個人與每月額度（micro-USD）：alice 很快就會用完，bob 用不完
DEMO_USERS = {
    "alice": 1_000,
    "bob": 1_000_000,
}


# 用 secrets 而不是 random：random 的亂數猜得出來，不能拿來當 Key
def generate_api_key() -> str:
    """Return a new random API key."""
    return API_KEY_PREFIX + secrets.token_hex(32)


# 資料庫只收到雜湊；Key 本身只在這裡交回去一次，之後沒有任何地方查得到
def seed_user(client: BaseClient, user_id: str, limit_micro_usd: int) -> str:
    """Store a new active API key and the monthly limit for the user, and return the key."""
    key = generate_api_key()
    key_item = {
        "key_hash": {"S": hash_api_key(key)},
        "user_id": {"S": user_id},
        "status": {"S": "active"},
    }
    client.put_item(TableName=API_KEYS_TABLE, Item=key_item)
    limit_item = {
        "user_id": {"S": user_id},
        "period": {"S": LIMIT_SORT_KEY},
        "limit_micro_usd": {"N": str(limit_micro_usd)},
    }
    client.put_item(TableName=QUOTAS_TABLE, Item=limit_item)
    return key


# 直接執行這個檔時才塞資料；Key 只印這一次，要當場抄下來
if __name__ == "__main__":
    client = make_dynamodb_client()
    create_tables(client)
    for user_id, limit_micro_usd in DEMO_USERS.items():
        key = seed_user(client, user_id, limit_micro_usd)
        print(f"{user_id}: {key}")