from app.auth import hash_api_key, extract_bearer_token


# abc 的 SHA-256 是公開的標準答案：演算法用錯或多加了東西都對不上
def test_hash_api_key_matches_known_sha256():
    result = hash_api_key("abc")

    assert result == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# 只差一個字的兩把 Key 要算出不同的雜湊：函式沒用到傳進來的 Key 就會被抓到
def test_hash_api_key_gives_different_hashes_for_different_keys():
    first = hash_api_key("gw_aaa")
    second = hash_api_key("gw_aab")

    assert first != second


# 正常情況：拿得到 Key，而且前綴拿得乾淨（多一個字或少一個字都對不上）
def test_extract_bearer_token_returns_key_after_prefix():
    result = extract_bearer_token("Bearer gw_abc")
    
    assert result == "gw_abc"


# 沒帶標頭時拿到的是 None，不能讓程式當掉
def test_extract_bearer_token_returns_none_without_header():
    result = extract_bearer_token(None)

    assert result is None


# 不是 Bearer 開頭的不收，例如帳號密碼用的 Basic
def test_extract_bearer_token_rejects_other_scheme():
    result = extract_bearer_token("Basic gw_abc")

    assert result is None


# 有前綴但後面是空的，不能交回空字串去查資料庫
def test_extract_bearer_token_rejects_empty_key():
    result = extract_bearer_token("Bearer ")

    assert result is None