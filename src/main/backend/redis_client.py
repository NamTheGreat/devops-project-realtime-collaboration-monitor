"""
redis_client.py — Async Redis client for the Git Collaboration Monitor.

Handles publishing events to Redis Pub/Sub, storing recent events in a list,
and computing aggregated statistics. Includes retry logic for resilience.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Module-level Redis connection pool and client
_redis: Optional[aioredis.Redis] = None

CHANNEL_NAME = "git-events"
RECENT_EVENTS_KEY = "recent-events"
MAX_RECENT_EVENTS = 100


async def get_redis(
    host: str = "localhost",
    port: int = 6379,
    max_connections: int = 10,
) -> aioredis.Redis:
    """
    Get or create the global async Redis client.

    Args:
        host: Redis server hostname.
        port: Redis server port.
        max_connections: Maximum pool connections.

    Returns:
        An async Redis client instance.
    """
    global _redis
    if _redis is None:
        pool = aioredis.ConnectionPool.from_url(
            f"redis://{host}:{port}",
            max_connections=max_connections,
            decode_responses=True,
        )
        _redis = aioredis.Redis(connection_pool=pool)
    return _redis


async def close_redis() -> None:
    """Close the global Redis connection pool."""
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


async def _retry(coro_factory, retries: int = 3, delay: float = 1.0):
    """
    Execute an async callable with retry logic.

    Args:
        coro_factory: A zero-argument callable that returns an awaitable.
        retries: Number of retry attempts.
        delay: Seconds between retries.

    Returns:
        The result of the coroutine.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        try:
            return await coro_factory()
        except Exception as exc:
            last_exc = exc
            logger.warning("Redis operation failed (attempt %d/%d): %s", attempt + 1, retries, exc)
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


async def publish_event(event: Dict[str, Any]) -> None:
    """
    Publish an event to the Redis Pub/Sub channel and persist it in the recent-events list.

    Args:
        event: The normalized event dictionary.
    """
    r = await get_redis()
    payload = json.dumps(event)

    async def _do():
        pipe = r.pipeline()
        pipe.publish(CHANNEL_NAME, payload)
        pipe.lpush(RECENT_EVENTS_KEY, payload)
        pipe.ltrim(RECENT_EVENTS_KEY, 0, MAX_RECENT_EVENTS - 1)
        await pipe.execute()

    await _retry(_do)
    logger.info("Published event %s to Redis", event.get("id", "unknown"))


async def get_recent_events(count: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch the most recent events from the Redis list.

    Args:
        count: Number of events to retrieve.

    Returns:
        List of event dictionaries (newest first).
    """
    r = await get_redis()

    async def _do():
        raw = await r.lrange(RECENT_EVENTS_KEY, 0, count - 1)
        return [json.loads(item) for item in raw]

    return await _retry(_do)


async def get_stats() -> Dict[str, Any]:
    """
    Compute aggregated statistics from recent events.

    Returns:
        Dict with total_events_today, active_contributors,
        branches_modified, and conflict_alerts counts.
    """
    r = await get_redis()

    async def _do():
        raw = await r.lrange(RECENT_EVENTS_KEY, 0, MAX_RECENT_EVENTS - 1)
        events = [json.loads(item) for item in raw]

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        one_hour_ago = now - timedelta(hours=1)

        total_today = 0
        contributors_hour: set = set()
        branches_today: set = set()
        conflict_count = 0

        for ev in events:
            try:
                ts = datetime.fromisoformat(ev.get("timestamp", ""))
            except (ValueError, TypeError):
                continue

            if ts >= today_start:
                total_today += 1
                branch = ev.get("branch", "")
                if branch:
                    branches_today.add(branch)
                if ev.get("alert"):
                    conflict_count += 1

            if ts >= one_hour_ago:
                contributors_hour.add(ev.get("actor", ""))

        return {
            "total_events_today": total_today,
            "active_contributors": len(contributors_hour),
            "branches_modified": len(branches_today),
            "conflict_alerts": conflict_count,
        }

    return await _retry(_do)
