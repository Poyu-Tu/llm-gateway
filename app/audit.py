"""Audit helpers: prompt hashing, summary, and the audit log."""

import re
import hmac
import hashlib
import json
from pathlib import Path

# 摘要長度上限（D6）
SUMMARY_LENGTH = 50
# 信箱的形狀：名字 @ 網域 . 結尾
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
# 台灣手機的形狀：0 或 +886 開頭，接 9 和 8 個數字；左右不能再貼著數字
PHONE_PATTERN = r"(?<!\d)(\+886[- ]?|0)9\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)"
# 身分證字號的形狀：1 個字母、1 或 2、8 個數字；左右不能再貼著英數字
TW_ID_PATTERN = r"(?<![A-Za-z0-9])[A-Za-z][12]\d{8}(?![A-Za-z0-9])"
# 信用卡號的形狀：13 到 19 個數字，中間可以有空格或橫線；左右不能再貼著數字
CARD_PATTERN = r"(?<!\d)\d([- ]?\d){12,18}(?!\d)"


# 算出 prompt 的 HMAC 指紋；沒有金鑰就無法用字典攻擊猜回原文（D4）
def hash_prompt(text: str, key: bytes) -> str:
    """Return the HMAC-SHA256 of the prompt, so the audit log never stores the text."""
    bytes_text = text.encode("utf-8")
    hmac_text = hmac.new(key, bytes_text, hashlib.sha256)
    return hmac_text.hexdigest()


# 用檢查碼驗算是不是合法卡號，避免把訂單編號誤遮成信用卡
def luhn_valid(digits: str) -> bool:
    """Return True when the digits pass the Luhn checksum."""
    total = 0
    for index, ch in enumerate(reversed(digits)):
        num = int(ch)
        if index % 2 != 0:
            num = num * 2
            if num > 9:
                num = num - 9
        total = total + num

    if total % 10 == 0:
        return True
    else:
        return False


# 抓到像卡號的數字時先驗算，過了才遮，沒過就原樣放回去
def replace_card_if_valid(match: re.Match) -> str:
    """Return the card label when the digits pass Luhn, otherwise the original text."""
    found = match.group(0)
    digits = re.sub(r"[- ]", "", found)
    if luhn_valid(digits):
        return "[CARD]"
    else:
        return found


# 遮罩和類別由同一次處理算出來，兩邊才不會對不上（遮了沒記、記了沒遮）
def mask_and_detect(text: str) -> tuple[str, list[str]]:
    """Return the masked text together with the categories that were masked."""
    found_types = []
    email_result = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    if text != email_result:
        found_types.append("EMAIL")
    card_result = re.sub(CARD_PATTERN, replace_card_if_valid, email_result)
    if email_result != card_result:
        found_types.append("CARD")
    phone_result = re.sub(PHONE_PATTERN, "[PHONE]", card_result)
    if card_result != phone_result:
        found_types.append("PHONE")
    result = re.sub(TW_ID_PATTERN, "[TW_ID]", phone_result)
    if phone_result != result:
        found_types.append("TW_ID")
    return result, found_types


# 個資遮罩：內容會送出 AWS 到供應商那邊，個資要在離開前先換掉
def mask(text: str) -> str:
    """Replace personal data with a category label before the text leaves the gateway."""
    sentence_result, _ = mask_and_detect(text)
    return sentence_result


# 稽核只記「有哪幾類個資」，不記內容；類別來自實際遮罩的結果，不另外比對
def detect_pii_types(text: str) -> list[str]:
    """Return the categories of personal data found in the text, without the data itself."""
    _, list_result = mask_and_detect(text)
    return list_result


# 產生摘要：一定先遮罩、再截斷，順序不能反（E34）
def make_summary(text: str) -> str:
    """Mask first, then cut. Cutting first could split personal data and hide it from the mask."""
    masked = mask(text)
    summary = masked[:SUMMARY_LENGTH]
    return summary


# 寫入一筆稽核紀錄：用附加模式，不能覆蓋舊紀錄
def append_audit(record: dict, path: Path) -> None:
    """Append one record as a JSON line. Never overwrite earlier records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        text = json.dumps(record)
        f.write(text + "\n")