"""Audit helpers: prompt hashing, summary, and the audit log."""

import hmac
import hashlib
import json
from pathlib import Path

SUMMARY_LENGTH = 50


def hash_prompt(text: str, key: bytes) -> str:
    """Return the HMAC-SHA256 of the prompt, so the audit log never stores the text."""
    bytes_text = text.encode("utf-8")
    hmac_text = hmac.new(key, bytes_text, hashlib.sha256)
    return hmac_text.hexdigest()


def mask(text: str) -> str:
    """Placeholder for M1. M2 will mask personal data here."""
    return text


def make_summary(text: str) -> str:
    """Mask first, then cut. Cutting first could split personal data and hide it from the mask."""
    masked = mask(text)
    summary = masked[:SUMMARY_LENGTH]
    return summary


def append_audit(record: dict, path: Path) -> None:
    """Append one record as a JSON line. Never overwirte earlier records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        text = json.dumps(record)
        f.write(text + "\n")