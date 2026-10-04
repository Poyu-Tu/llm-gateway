"""Tests for the audit helpers."""

import json

from app.audit import append_audit, hash_prompt, make_summary, mask


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