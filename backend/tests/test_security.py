import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_security_headers_and_request_id(client):
    response = await client.get("/health", headers={"X-Request-ID": "test-request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-123"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


@pytest.mark.asyncio
async def test_rate_limit_returns_controlled_error(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_requests", 1)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)

    first = await client.post("/api/v1/auth/unknown-route")
    second = await client.post("/api/v1/auth/unknown-route")

    assert first.status_code == 404
    assert second.status_code == 429
    assert second.json()["detail"] == "Too many requests"
    assert second.json()["request_id"]
