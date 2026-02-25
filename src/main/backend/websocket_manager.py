"""
websocket_manager.py — WebSocket connection manager for the Git Collaboration Monitor.

Maintains a set of active WebSocket connections, handles broadcasting,
and runs a background Redis Pub/Sub listener to forward events to all
connected dashboard clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        """Initialize the manager with an empty connection set."""
        self._active_connections: Set[WebSocket] = set()

    @property
    def active_count(self) -> int:
        """Return the number of active connections."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket, recent_events: List[Dict[str, Any]] | None = None) -> None:
        """
        Accept a new WebSocket connection and send recent events.

        Args:
            websocket: The incoming WebSocket connection.
            recent_events: Optional list of recent events to send immediately.
        """
        await websocket.accept()
        self._active_connections.add(websocket)
        logger.info("WebSocket connected. Active connections: %d", self.active_count)

        # Send last 10 events so the dashboard isn't blank on connect
        if recent_events:
            for event in recent_events[:10]:
                try:
                    await websocket.send_json(event)
                except Exception:
                    break

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the active set.

        Args:
            websocket: The disconnected WebSocket.
        """
        self._active_connections.discard(websocket)
        logger.info("WebSocket disconnected. Active connections: %d", self.active_count)

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message string to all active WebSocket connections.
        Dead connections are silently removed.

        Args:
            message: JSON string to send to all clients.
        """
        dead: List[WebSocket] = []
        for ws in self._active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._active_connections.discard(ws)
            logger.debug("Removed dead WebSocket connection")

    async def start_redis_listener(self, redis_client) -> None:
        """
        Subscribe to the Redis Pub/Sub channel and broadcast received messages.

        This should be run as a background task on application startup.

        Args:
            redis_client: An async Redis client instance.
        """
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("git-events")
        logger.info("Redis Pub/Sub listener started on channel 'git-events'")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    await self.broadcast(data)
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled, unsubscribing...")
            await pubsub.unsubscribe("git-events")
            await pubsub.close()
        except Exception as exc:
            logger.error("Redis listener error: %s", exc)
            await pubsub.unsubscribe("git-events")
            await pubsub.close()


# Singleton instance used by the FastAPI application
manager = WebSocketManager()
