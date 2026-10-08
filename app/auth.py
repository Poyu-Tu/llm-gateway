import hashlib


# 資料庫只存 Key 的雜湊：整張表被搬走也拿不到能用的 Key；Key 是長亂數，不用另外加金鑰
def hash_api_key(key: str) -> str:
    """Return the SHA-256 hex digest of an API key, the only form the key is stored in."""
    bytes_text = key.encode("utf-8")
    result = hashlib.sha256(bytes_text)
    return result.hexdigest()