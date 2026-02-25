"""
main.py — FastAPI application for the Real-time Git Collaboration Monitor.

Exposes endpoints for receiving GitHub webhooks, serving WebSocket connections,
retrieving recent events, and computing statistics. Uses Redis for persistence
and Pub/Sub for real-time broadcasting.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from processor import detect_conflicts, parse_event
from redis_client import close_redis, get_recent_events, get_redis, get_stats, publish_event
from websocket_manager import manager

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Redis connection pool and background Pub/Sub listener."""
    redis = await get_redis(host=REDIS_HOST, port=REDIS_PORT)
    logger.info("Redis connected at %s:%s", REDIS_HOST, REDIS_PORT)

    # Start the Redis → WebSocket bridge as a background task
    listener_task = asyncio.create_task(manager.start_redis_listener(redis))
    yield
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    await close_redis()
    logger.info("Redis connection closed")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Real-time Git Collaboration Monitor",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper — HMAC signature validation
# ---------------------------------------------------------------------------
def _verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify the X-Hub-Signature-256 header from GitHub.

    Args:
        payload_body: Raw request body bytes.
        signature: The signature header value (sha256=...).
        secret: The webhook secret string.

    Returns:
        True if the signature is valid.
    """
    if not secret:
        # If no secret configured, skip validation (dev mode)
        return True
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "running", "service": "git-collaboration-monitor"}


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str = Header(default="", alias="X-Hub-Signature-256"),
    x_github_event: str = Header(default="ping", alias="X-GitHub-Event"),
):
    """
    Receive and process a GitHub webhook payload.

    Validates the HMAC-SHA256 signature, parses the event, detects conflicts,
    publishes the result to Redis, and acknowledges receipt.
    """
    body = await request.body()

    # Signature validation
    if WEBHOOK_SECRET and not _verify_signature(body, x_hub_signature_256, WEBHOOK_SECRET):
        logger.warning("Invalid webhook signature received")
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)

    # Log incoming webhook
    repo_name = payload.get("repository", {}).get("full_name", "unknown")
    logger.info(
        "Webhook received | event=%s | repo=%s | time=%s",
        x_github_event,
        repo_name,
        datetime.now(timezone.utc).isoformat(),
    )

    # Parse and process the event
    event = parse_event(x_github_event, payload)

    # Conflict detection for push events
    if event["event_type"] == "push":
        recent = await get_recent_events(20)
        alert = detect_conflicts(event, recent)
        if alert:
            event["alert"] = alert
            logger.warning("Conflict detected: %s", alert["message"])

    # Publish to Redis (Pub/Sub + recent-events list)
    await publish_event(event)

    return {"status": "received", "event_type": x_github_event}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.

    On connect, sends the last 10 events immediately, then streams new events
    from Red Pub/Sub until the client disconnects.
    """
    recent = await get_recent_events(10)
    await manager.connect(websocket, recent_events=recent)
    try:
        while True:
            # Keep the connection alive; client doesn't send data
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@app.get("/events/recent")
async def recent_events():
    """Return the last 50 events from Redis."""
    events = await get_recent_events(50)
    return events


@app.get("/stats")
async def stats():
    """Return aggregated statistics for the dashboard."""
    return await get_stats()
