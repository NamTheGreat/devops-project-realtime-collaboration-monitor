"""
test_webhook_endpoint.py — Integration tests for the webhook API endpoints.

Uses httpx AsyncClient with the FastAPI TestClient to verify signature
validation, event processing, and the recent events endpoint.
"""

import hashlib
import hmac
import json
import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "main", "backend"))

# Set env vars before importing the app
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")

from main import app

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "test-data")
SECRET = "test-secret"


def _sign_payload(payload_bytes: bytes) -> str:
    """Generate a valid HMAC-SHA256 signature for a payload."""
    return "sha256=" + hmac.new(SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()


def _load_sample(filename: str) -> dict:
    with open(os.path.join(DATA_DIR, filename), "r") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_webhook_invalid_signature():
    """POST /webhook with invalid signature should return 403."""
    payload = json.dumps({"test": True}).encode()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": "sha256=invalid",
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_valid_push_event():
    """POST /webhook with valid signature should return 200 and acknowledge."""
    payload_dict = _load_sample("sample_push_event.json")
    payload_bytes = json.dumps(payload_dict).encode()
    sig = _sign_payload(payload_bytes)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/webhook",
            content=payload_bytes,
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "received"
    assert data["event_type"] == "push"


@pytest.mark.asyncio
async def test_webhook_unsupported_event_type():
    """POST /webhook with unknown event type should still return 200 (graceful handling)."""
    payload = json.dumps({"sender": {"login": "bot"}, "repository": {"full_name": "test/repo"}}).encode()
    sig = _sign_payload(payload)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "unknown_event",
                "Content-Type": "application/json",
            },
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_check():
    """GET / should return the health check response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["service"] == "git-collaboration-monitor"


@pytest.mark.asyncio
async def test_recent_events_endpoint():
    """GET /events/recent should return a list."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/events/recent")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
