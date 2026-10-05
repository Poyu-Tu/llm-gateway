"""Tests for the audit helpers."""

import json

from app.audit import append_audit, hash_prompt, make_summary, mask, luhn_valid


# 指紋長度固定是 64 個字元
def test_hash_is_64_hex_chars():
    result = hash_prompt("Say hi", b"test-key")

    assert len(result) == 64


# 同樣的文字和金鑰，指紋要一樣
def test_same_input_gives_same_hash():
    first = hash_prompt("Say hi", b"test-key")
    second = hash_prompt("Say hi", b"test-key")

    assert first == second


# 換一把金鑰，指紋就不同（HMAC 的重點）
def test_different_key_gives_different_hash():
    first = hash_prompt("Say hi", b"test-key")
    second = hash_prompt("Say hi", b"other-key")

    assert first != second


# 短文字要原樣保留
def test_summary_keeps_short_text():
    result = make_summary("Say hi")
    assert result == "Say hi"


# 長文字要截成 50 個字
def test_summary_cuts_long_text_to_50_chars():
    result = make_summary("a" * 80)
    assert len(result) == 50


# 寫一筆，檔案裡要剛好一行，而且讀得回來
def test_append_audit_writes_one_json_line(tmp_path):
    path = tmp_path / "audit.jsonl"
    record = {"request_id": "r1", "summary": "Say hi"}

    append_audit(record, path)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == record


# 連寫兩筆，兩筆都要在、順序正確（防止誤用覆寫模式）
def test_append_audit_keeps_earlier_records(tmp_path):
    path = tmp_path / "audit.jsonl"
    record1 = {"request_id": "r1", "summary": "Say hi"}
    record2 = {"request_id": "r2", "summary": "Say hi"}

    append_audit(record1, path)
    append_audit(record2, path)
    
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == record1
    assert json.loads(lines[1]) == record2


# 信箱要換成類別標籤，原文不能留在送出去的內容裡
def test_mask_replaces_email():
    email = "Contact me at amy@example.com please"

    result = mask(email)

    assert result == "Contact me at [EMAIL] please"


# 沒有個資的句子不能被動到（防止遮過頭）
def test_mask_keeps_text_without_personal_data():
    result = mask("Say hi")
    assert result == "Say hi"


# 手機號碼要換成類別標籤
def test_mask_replaces_mobile_phone():
    phone = "Call me at 0912345678 tonight"

    result = mask(phone)

    assert result == "Call me at [PHONE] tonight"


# 一般人常加橫線，也要抓得到
def test_mask_replaces_mobile_phone_with_dashes():
    phone = "Call me at 0912-345-678 tonight"

    result = mask(phone)

    assert result == "Call me at [PHONE] tonight"


# 國碼寫法也要抓得到
def test_mask_replaces_mobile_phone_with_country_code():
    phone = "Call me at +886912345678 tonight"

    result = mask(phone)

    assert result == "Call me at [PHONE] tonight"


# 長數字裡剛好含手機的樣子，不能誤遮
def test_mask_keeps_long_number():
    include = "Order 20260912345678 shipped"

    result = mask(include)

    assert result == "Order 20260912345678 shipped"


# 信箱開頭長得像手機時，整串算信箱（遮罩順序：先信箱、後手機）
def test_mask_treats_phone_like_email_as_email():
    like = "Mail 0912345678@example.com now"

    result = mask(like)

    assert result == "Mail [EMAIL] now"


# 身分證字號要換成類別標籤
def test_mask_replaces_tw_id():
    id_card = "My ID is A123456780 thanks"

    result = mask(id_card)

    assert result == "My ID is [TW_ID] thanks"


# 小寫開頭也要抓得到，使用者不一定會按大寫
def test_mask_replaces_lowercase_tw_id():
    id_card = "My ID is a123456780 thanks"

    result = mask(id_card)

    assert result == "My ID is [TW_ID] thanks"


# 前面多一個字母就是料號，不是身分證，不能誤遮
def test_mask_keeps_product_code():
    stock_num = "Part AB123456780 in stock"

    result = mask(stock_num)

    assert result == "Part AB123456780 in stock"


# 合法卡號（公開的測試卡號）要通過驗算
def test_luhn_accepts_valid_card_number():
    card = "4111111111111111"
    
    result = luhn_valid(card)

    assert result is True


# 最後一碼改掉，驗算就要不通過
def test_luhn_rejects_wrong_check_digit():
    card = "4111111111111112"

    result = luhn_valid(card)

    assert result is False


# 信用卡號要換成類別標籤
def test_mask_replaces_card_number():
    card = "Pay with 4111111111111111 today"

    result = mask(card)

    assert result == "Pay with [CARD] today"


# 卡片上是四碼一組，使用者常照著打空格
def test_mask_replaces_card_number_with_spaces():
    card = "Pay with 4111 1111 1111 1111 today"

    result = mask(card)

    assert result == "Pay with [CARD] today"


# 長得像卡號但驗算不過，就是一般編號，不能誤遮
def test_mask_keeps_number_failing_luhn():
    num = "Order 4111111111111112 shipped"

    result = mask(num)

    assert result == "Order 4111111111111112 shipped" 


# 手機跨在第 50 字前後時，摘要不能留下被切一半的號碼（先遮罩再截斷）
def test_summary_does_not_leak_split_phone():
    text = "a" * 45 + " 0912345678 end"

    result = make_summary(text)

    assert "0912" not in result