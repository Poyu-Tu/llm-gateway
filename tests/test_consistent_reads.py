"""Reads that decide who gets in must see the latest data (strongly consistent reads)."""

from app.auth import find_user_id
from app.quota import read_limit, read_used


# 測試道具：記下收到的每一次讀取，一律回「查不到」
# 練習場（DynamoDB Local）不管這個參數，所以只能檢查「有沒有帶」，證明不了雲端的行為
class RecordingDynamoDB:
    """Stands in for a DynamoDB client and records every get_item call."""

    def __init__(self):
        self.reads = []

    def get_item(self, **kwargs):
        self.reads.append(kwargs)
        return {}


# 查 Key：剛被停用的 Key 下一秒就要擋得住
def test_find_user_id_reads_the_latest_key_status():
    client = RecordingDynamoDB()

    find_user_id(client, "hash-a")

    assert len(client.reads) == 1
    assert client.reads[0]["ConsistentRead"] is True


# 查額度：剛調整的額度下一個請求就要生效
def test_read_limit_reads_the_latest_limit():
    client = RecordingDynamoDB()

    read_limit(client, "alice")

    assert len(client.reads) == 1
    assert client.reads[0]["ConsistentRead"] is True


# 查已用量：剛扣完的錢下一個請求就要看得到，不然會多放行一次
def test_read_used_reads_the_latest_usage():
    client = RecordingDynamoDB()

    read_used(client, "alice", "2026-10")

    assert len(client.reads) == 1
    assert client.reads[0]["ConsistentRead"] is True
