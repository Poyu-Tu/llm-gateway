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


# 算出 prompt 的 HMAC 指紋；沒有金鑰就無法用字典攻擊猜回原文（D4）
def hash_prompt(text: str, key: bytes) -> str:
    """Return the HMAC-SHA256 of the prompt, so the audit log never stores the text."""
    bytes_text = text.encode("utf-8")
    hmac_text = hmac.new(key, bytes_text, hashlib.sha256)
    return hmac_text.hexdigest()


# 個資遮罩：內容會送出 AWS 到供應商那邊，個資要在離開前先換掉
def mask(text: str) -> str:
    """Replace personal data with a category label before the text leaves the gateway."""
    email_result = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    result = re.sub(PHONE_PATTERN, "[PHONE]", email_result)
    return result


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