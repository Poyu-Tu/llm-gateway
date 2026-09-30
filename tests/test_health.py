"""Tests for the health check endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_path_returns_404():
    """Only routes we define should be reachable."""
    response = client.get("/abc")
    assert response.status_code == 404