"""Tests for scripts/show_audit.py."""

import pytest

from app.audit import write_audit
from scripts.create_tables import create_tables
from scripts.show_audit import read_audit
from tests.test_audit_store import make_record

# 這個檔的測試都要連 DynamoDB Local（考場，8002）
pytestmark = pytest.mark.integration


# 寫進去的那一筆，用單號查得回來，內容一模一樣
def test_read_audit_returns_the_record_written_by_write_audit(dynamodb):
    create_tables(dynamodb)
    record = make_record(request_id="r1")
    write_audit(dynamodb, record)

    assert read_audit(dynamodb, "r1") == record


# 查不到的單號回 None，不是報錯
def test_read_audit_returns_none_for_an_unknown_request_id(dynamodb):
    create_tables(dynamodb)

    assert read_audit(dynamodb, "no-such-request") is None
