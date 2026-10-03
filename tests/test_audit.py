"""Tests for the audit helpers."""

import json

from app.audit import append_audit, hash_prompt, make_summary


def test_hash_is_64_hex_chars():
    result = hash_prompt("Say hi", b"test-key")

    assert len(result) == 64


def test_same_input_gives_same_hash():
    first = hash_prompt("Say hi", b"test-key")
    second = hash_prompt("Say hi", b"test-key")

    assert first == second


def test_different_key_gives_different_hash():
    first = hash_prompt("Say hi", b"test-key")
    second = hash_prompt("Say hi", b"other-key")

    assert first != second


def test_summary_keeps_short_text():
    result = make_summary("Say hi")
    assert result == "Say hi"


def test_summary_cuts_long_text_to_50_chars():
    result = make_summary("a" * 80)
    assert len(result) == 50


def test_append_audit_writes_one_json_line(tmp_path):
    path = tmp_path / "audit.jsonl"
    record = {"request_id": "r1", "summary": "Say hi"}

    append_audit(record, path)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == record


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