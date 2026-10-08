import hashlib

# Authorization 標頭的固定開頭；結尾的空格是前綴的一部分
BEARER_PREFIX = "Bearer "


# 資料庫只存 Key 的雜湊：整張表被搬走也拿不到能用的 Key；Key 是長亂數，不用另外加金鑰
def hash_api_key(key: str) -> str:
    """Return the SHA-256 hex digest of an API key, the only form the key is stored in."""
    bytes_text = key.encode("utf-8")
    result = hashlib.sha256(bytes_text)
    return result.hexdigest()


# 格式不對一律交回 None，由呼叫的人統一回 401；不在這裡分辨是哪一種不對
def extract_bearer_token(header: str | None) -> str | None:
    """Return the key from an Authorization header, or None when it is missing or malformed."""
    if header is None:
        return None
    if not header.startswith(BEARER_PREFIX):
        return None
    token = header[len(BEARER_PREFIX):]
    if token == "":
        return None
    return token