"""
test_websocket_manager.py — Unit tests for the WebSocket manager module.

Tests connection management, broadcasting, and graceful disconnect handling.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "main", "backend"))

from websocket_manager import WebSocketManager


@pytest.fixture
def ws_manager():
    """Provide a fresh WebSocketManager instance for each test."""
    return WebSocketManager()


def _mock_websocket() -> AsyncMock:
    """Create a mock WebSocket with async accept/send methods."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestWebSocketManager:
    """Tests for the WebSocketManager class."""

    @pytest.mark.asyncio
    async def test_connect_adds_to_active(self, ws_manager):
        """Connecting a WebSocket should add it to the active set."""
        ws = _mock_websocket()
        await ws_manager.connect(ws)
        assert ws_manager.active_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes(self, ws_manager):
        """Disconnecting a WebSocket should remove it from the active set."""
        ws = _mock_websocket()
        await ws_manager.connect(ws)
        await ws_manager.disconnect(ws)
        assert ws_manager.active_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self, ws_manager):
        """Broadcasting should send a message to all connected clients."""
        ws1, ws2 = _mock_websocket(), _mock_websocket()
        await ws_manager.connect(ws1)
        await ws_manager.connect(ws2)
        await ws_manager.broadcast('{"test": true}')
        ws1.send_text.assert_called_once_with('{"test": true}')
        ws2.send_text.assert_called_once_with('{"test": true}')

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self, ws_manager):
        """Dead connections should be silently removed during broadcast."""
        ws_alive = _mock_websocket()
        ws_dead = _mock_websocket()
        ws_dead.send_text.side_effect = Exception("Connection lost")

        await ws_manager.connect(ws_alive)
        await ws_manager.connect(ws_dead)
        assert ws_manager.active_count == 2

        await ws_manager.broadcast('{"test": true}')
        assert ws_manager.active_count == 1

    @pytest.mark.asyncio
    async def test_connect_sends_recent_events(self, ws_manager):
        """On connect, recent events should be sent to the new client."""
        ws = _mock_websocket()
        recent = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        await ws_manager.connect(ws, recent_events=recent)
        assert ws.send_json.call_count == 3

    @pytest.mark.asyncio
    async def test_connect_limits_to_10_events(self, ws_manager):
        """On connect, at most 10 recent events should be sent."""
        ws = _mock_websocket()
        recent = [{"id": str(i)} for i in range(20)]
        await ws_manager.connect(ws, recent_events=recent)
        assert ws.send_json.call_count == 10
