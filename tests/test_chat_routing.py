"""Tests for routing on POST /v1/chat: which model is called, and what the audit log says about it."""

import json

import pytest
from fastapi.testclient import TestClient

import app.main
from app.config import GatewayConfig, ModelConfig, RoutingConfig
from app.main import app as gateway
from app.main import get_audit_path, get_client, get_config, get_dynamodb, get_hmac_key, get_quota, get_user_id
from tests.fakes import FakeDynamoDB, make_fake_client

# 測試用的設定：模型名稱故意不用正式的，主程式偷用寫死的名稱時才會被抓到
# 門檻設成 18 個字，測試的句子才不用寫到 300 字
TEST_CONFIG = GatewayConfig(
    routing=RoutingConfig(cheap_model="small", strong_model="big", min_chars=18, keywords=["debug"]),
    models={
        "small": ModelConfig(reasoning_effort="none", max_completion_tokens=100, input_price=100_000, output_price=500_000),
        "big": ModelConfig(reasoning_effort="low", max_completion_tokens=200, input_price=2_000_000, output_price=10_000_000),
    },
)


# 每個測試跑完都把換掉的領用窗口還原：這個檔換掉了設定，不還原的話會影響到別的測試檔
@pytest.fixture(autouse=True)
def restore_dependencies():
    """Remove every dependency override after each test in this file."""
    yield
    gateway.dependency_overrides.clear()


# 把領用窗口換成假的，設定換成上面那一份；回傳：測試用戶端、筆記本、稽核檔位置、假的資料庫
def make_routing_test_client(tmp_path, config=TEST_CONFIG):
    """Swap the real dependencies for fakes and return what tests need."""
    fake_client, completions = make_fake_client()
    audit_path = tmp_path / "audit.jsonl"
    database = FakeDynamoDB()
    gateway.dependency_overrides[get_client] = lambda: fake_client
    gateway.dependency_overrides[get_hmac_key] = lambda: b"test-key"
    gateway.dependency_overrides[get_audit_path] = lambda: audit_path
    gateway.dependency_overrides[get_user_id] = lambda: "alice"
    gateway.dependency_overrides[get_quota] = lambda: (1_000_000, 0)
    gateway.dependency_overrides[get_dynamodb] = lambda: database
    gateway.dependency_overrides[get_config] = lambda: config
    return TestClient(gateway), completions, audit_path, database


# 讀出稽核檔的最後一筆
def read_audit(audit_path):
    """Return the last audit record as a dict."""
    lines = audit_path.read_text(encoding="utf-8").splitlines()
    return json.loads(lines[-1])


# S05 的前半：短、沒有關鍵字的問題交給便宜模型，而且不思考
def test_chat_sends_simple_message_to_the_cheap_model(tmp_path):
    client, completions, _, _ = make_routing_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert completions.last_request["model"] == "small"
    assert completions.last_request["reasoning_effort"] == "none"
    assert response.json()["model"] == "small"


# S05 的後半：含關鍵字的問題交給強模型，思考量用強模型自己的設定
def test_chat_sends_keyword_message_to_the_strong_model(tmp_path):
    client, completions, _, _ = make_routing_test_client(tmp_path)

    response = client.post("/v1/chat", json={"message": "Please debug it"})

    assert response.status_code == 200
    assert completions.last_request["model"] == "big"
    assert completions.last_request["reasoning_effort"] == "low"
    assert response.json()["model"] == "big"


# 夠長的問題也交給強模型（門檻 18 個字，這一句 20 個字）
def test_chat_sends_long_message_to_the_strong_model(tmp_path):
    client, completions, _, _ = make_routing_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "a" * 20})

    assert completions.last_request["model"] == "big"


# 稽核要說得出為什麼選這顆模型：便宜模型記 default
def test_chat_audit_records_route_for_the_cheap_model(tmp_path):
    client, _, audit_path, _ = make_routing_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "Say hi"})

    record = read_audit(audit_path)
    assert record["route_reason"] == "default"
    assert record["routed_model"] == "small"


# 強模型的理由要分得出是關鍵字還是長度
def test_chat_audit_records_route_for_the_strong_model(tmp_path):
    client, _, audit_path, _ = make_routing_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "Please debug it"})
    keyword_record = read_audit(audit_path)
    client.post("/v1/chat", json={"message": "a" * 20})
    length_record = read_audit(audit_path)

    assert keyword_record["route_reason"] == "keyword"
    assert keyword_record["routed_model"] == "big"
    assert length_record["route_reason"] == "length"
    assert length_record["routed_model"] == "big"


# 路由看的是遮罩後的內容：原文 19 個字（達到門檻 18），遮罩後 "Call [PHONE] now" 只有 16 個字
def test_chat_routes_on_the_masked_message(tmp_path):
    client, completions, audit_path, _ = make_routing_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "Call 0912345678 now"})

    assert completions.last_request["model"] == "small"
    assert read_audit(audit_path)["route_reason"] == "default"


# S06：成本用實際呼叫的那顆模型的單價。假的模型回報 13 / 11 個 token，強模型是 13 x 2 + 11 x 10 = 136
def test_chat_charges_the_price_of_the_routed_model(tmp_path):
    client, _, audit_path, database = make_routing_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "Please debug it"})

    record = read_audit(audit_path)
    charged = database.updates[-1]["ExpressionAttributeValues"][":amount"]["N"]
    assert record["cost_micro_usd"] == 136
    assert charged == "136"


# 同樣的 token 數，便宜模型是 7：兩顆模型各用各的單價
def test_chat_charges_the_cheap_price_for_a_simple_message(tmp_path):
    client, _, audit_path, database = make_routing_test_client(tmp_path)

    client.post("/v1/chat", json={"message": "Say hi"})

    record = read_audit(audit_path)
    charged = database.updates[-1]["ExpressionAttributeValues"][":amount"]["N"]
    assert record["cost_micro_usd"] == 7
    assert charged == "7"


# ---- 以下是「路由選到的模型沒有設定」：正常情況下啟動時就擋掉了，這是防萬一的路 ----

# 壞掉的設定：路由的強模型叫 ghost，但 models 裡沒有它
# 這份設定是直接組出來的，沒有經過 load_config 的檢查，所以做得出這種「不該存在」的狀態
BROKEN_CONFIG = GatewayConfig(
    routing=RoutingConfig(cheap_model="small", strong_model="ghost", min_chars=18, keywords=["debug"]),
    models={
        "small": ModelConfig(reasoning_effort="none", max_completion_tokens=100, input_price=100_000, output_price=500_000),
    },
)


# 查不到模型設定：回 500 與固定的訊息，而且訊息不能透露是哪一顆模型
def test_chat_returns_500_when_the_routed_model_has_no_settings(tmp_path):
    client, _, _, _ = make_routing_test_client(tmp_path, BROKEN_CONFIG)

    response = client.post("/v1/chat", json={"message": "Please debug it"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "ghost" not in response.text


# 查不到就不呼叫模型，也不扣錢：資料庫只收到事前那一次「加 0」
def test_chat_spends_nothing_when_the_routed_model_has_no_settings(tmp_path):
    client, completions, _, database = make_routing_test_client(tmp_path, BROKEN_CONFIG)

    response = client.post("/v1/chat", json={"message": "Please debug it"})

    # 先確認請求真的是被這條路擋下的，下面兩個「沒發生」才有意義
    assert response.status_code == 500
    assert completions.last_request is None
    amounts = [update["ExpressionAttributeValues"][":amount"]["N"] for update in database.updates]
    assert amounts == ["0"]


# 這個請求要留下稽核紀錄：查得到是誰、路由選了什麼、失敗的類別
def test_chat_audits_the_request_when_the_routed_model_has_no_settings(tmp_path):
    client, _, audit_path, _ = make_routing_test_client(tmp_path, BROKEN_CONFIG)

    response = client.post("/v1/chat", json={"message": "Please debug it"})

    assert response.status_code == 500
    record = read_audit(audit_path)
    assert record["user_id"] == "alice"
    assert record["status"] == "error"
    assert record["error_type"] == "ModelNotConfiguredError"
    assert record["routed_model"] == "ghost"
    assert record["route_reason"] == "keyword"
    assert "cost_micro_usd" not in record


# 同一份壞掉的設定，走便宜模型的請求不受影響：只擋該擋的
def test_chat_still_serves_the_cheap_model_when_only_the_strong_one_is_missing(tmp_path):
    client, completions, _, _ = make_routing_test_client(tmp_path, BROKEN_CONFIG)

    response = client.post("/v1/chat", json={"message": "Say hi"})

    assert response.status_code == 200
    assert completions.last_request["model"] == "small"


# 模型和思考量只能來自設定：主程式不能再留寫死的常數，否則改設定檔時會有兩個地方要改
def test_main_keeps_no_hard_coded_model():
    assert not hasattr(app.main, "MODEL")
    assert not hasattr(app.main, "REASONING_EFFORT")
