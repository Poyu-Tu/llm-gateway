"""Audit helpers: prompt hashing, summary, and the audit log."""

import hmac
import hashlib
import json
from pathlib import Path

# 摘要長度上限（D6）
SUMMARY_LENGTH = 50


# 算出 prompt 的 HMAC 指紋；沒有金鑰就無法用字典攻擊猜回原文（D4）
def hash_prompt(text: str, key: bytes) -> str:
    """Return the HMAC-SHA256 of the prompt, so the audit log never stores the text."""
    bytes_text = text.encode("utf-8")
    hmac_text = hmac.new(key, bytes_text, hashlib.sha256)
    return hmac_text.hexdigest()


# 個資遮罩：M1 是空殼，原樣回傳；M2 補上實作
def mask(text: str) -> str:
    """Placeholder for M1. M2 will mask personal data here."""
    return text


# 產生摘要：一定先遮罩、再截斷，順序不能反（E34）
def make_summary(text: str) -> str:
    """Mask first, then cut. Cutting first could split personal data and hide it from the mask."""
    masked = mask(text)
    summary = masked[:SUMMARY_LENGTH]
    return summary


# 寫入一筆稽核紀錄：用附加模式，不能覆蓋舊紀錄
def append_audit(record: dict, path: Path) -> None:
    """Append one record as a JSON line. Never overwirte earlier records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        text = json.dumps(record)
        f.write(text + "\n")