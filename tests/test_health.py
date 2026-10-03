"""Tests for the health check endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# 健康檢查要回 200 和 {"status": "ok"}
def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# 沒定義的路徑要回 404
def test_unknown_path_returns_404():
    """Only routes we define should be reachable."""
    response = client.get("/abc")
    assert response.status_code == 404