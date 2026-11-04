import hashlib

from botocore.client import BaseClient

from app.db import API_KEYS_TABLE

# Authorization 標頭的固定開頭；結尾的空格是前綴的一部分
BEARER_PREFIX = "Bearer "


# 資料庫只存 Key 的雜湊：整張表被搬走也拿不到能用的 Key；Key 是長亂數，不用另外加金鑰
def hash_api_key(key: str) -> str:
    """Return the SHA-256 hex digest of an API key, the only form the key is stored in."""
    bytes_text = key.encode("utf-8")    # 文字轉成位元組（bytes），hashlib 只吃位元組。直接丟字串進去會 TypeError
    result = hashlib.sha256(bytes_text) # 丟進 SHA-256 標準演算法，同樣輸入一定得到同樣輸出
    return result.hexdigest()   # 轉成 64 個 0～9、a～f 的字，存進 DynamoDB 是字串，好比對，也好印出來看


# 格式不對一律交回 None，由呼叫的人統一回 401；不在這裡分辨是哪一種不對
def extract_bearer_token(header: str | None) -> str | None:
    """Return the key from an Authorization header, or None when it is missing or malformed."""
    if header is None:  # 沒標頭就回 None，一定要放第一個：None 沒有 .startswith()，順序反過來會直接當掉
        return None
    if not header.startswith(BEARER_PREFIX):    # .startswith() 是用來判斷字串是否以指定的字元或子字串開頭的方法，不是 Bearer 開頭就回 None	擋掉，Basic xxx 這類別的認證方式
        return None
    token = header[len(BEARER_PREFIX):] # 用切片 [7:] 拿掉前綴，len() 算長度，不寫死數字 7；冒號代表「從第 7 個字切到最後」
    if token == "": # 切完是空的就回 None，擋掉 "Bearer " 後面什麼都沒有的情況
        return None
    return token


# 查不到、被停用、狀態欄不存在，一律交回 None：呼叫的人分不出是哪一種，也就不會透露給外面
def find_user_id(client: BaseClient, key_hash: str) -> str | None:
    """Return the user id for an active API key hash, or None when the key must not be used."""
    # 強一致讀取：剛被停用的 Key 下一秒就要擋得住。有代價：同樣讀 4KB，強一致花的讀取單位是一般讀取（最終一致）的 2 倍。我們只在「決定放不放行」的三個地方用：這支、read_limit、read_used。
    # get_item：用主鍵直接拿一筆
    # {"S": key_hash} ：低階 client 要標註型別，S 是字串，boto3 的 client 不會自己猜型別
    # ConsistentRead=True：看正本，剛停用的 Key 下一個請求就要擋住
    response = client.get_item(TableName=API_KEYS_TABLE, Key={"key_hash": {"S": key_hash}}, ConsistentRead=True)
    if "Item" not in response:  # 回應沒有 Item 就回 None，查不到不會丟錯，只是回應裡少了 Item 這一格
        return None
    item = response["Item"]
    if "status" not in item:    # 沒有 status 就回 None，不知道狀態就當成不能用：寧可錯擋，不要錯放（fail closed）
        return None
    if item["status"]["S"] != "active": # 不是 active 就回 None，停用功能靠這兩行；停用的 Key 那一列刻意留著，之後才查得到它曾經是誰的
        return None
    return item["user_id"]["S"] # ["S"] 剝掉型別標籤，不剝的話回傳的是 {'S': 'alice'}，不是 'alice'