"""Settings that matter once the gateway runs behind the load balancer."""

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_client

# FastAPI 預設會開的四個說明頁：列出所有 API 的路徑與欄位
API_DOCS_PATHS = ["/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"]


# get_client() 會記住第一次建好的連線；每個測試前後都清掉，前一個測試的連線不會被下一個拿到
@pytest.fixture(autouse=True)
def fresh_client():
    get_client.cache_clear()
    yield
    get_client.cache_clear()


# 說明頁一律關閉：使用者用不到，只會把 API 的地圖交給想攻擊的人
def test_api_docs_pages_are_turned_off():
    client = TestClient(app)

    for path in API_DOCS_PATHS:
        response = client.get(path)
        assert response.status_code == 404, path


# 關掉說明頁不能連健康檢查一起關掉：負載平衡器靠它判斷容器還活著
def test_health_check_still_answers():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# SDK 不自己重試：被限流時直接回 503 與 Retry-After，不在背後偷偷等到負載平衡器先斷線
def test_openai_client_does_not_retry(monkeypatch):
    # 建立連線物件只需要有一個值，不會真的連線
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    client = get_client()

    assert client.max_retries == 0


# 每次呼叫最多等 60 秒
def test_openai_client_gives_up_after_60_seconds(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    client = get_client()

    assert client.timeout == 60


# 整個程式共用一個連線：身分聯盟的通行證可用 1 小時，每個請求都新建就每次重換
def test_openai_client_is_shared(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")

    assert get_client() is get_client()
