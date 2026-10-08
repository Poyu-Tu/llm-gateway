from app.auth import hash_api_key


# abc 的 SHA-256 是公開的標準答案：演算法用錯或多加了東西都對不上
def test_hash_api_key_matches_known_sha256():
    result = hash_api_key("abc")

    assert result == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# 只差一個字的兩把 Key 要算出不同的雜湊：函式沒用到傳進來的 Key 就會被抓到
def test_hash_api_key_gives_different_hashes_for_different_keys():
    first = hash_api_key("gw_aaa")
    second = hash_api_key("gw_aab")

    assert first != second