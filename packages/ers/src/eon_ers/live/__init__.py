"""OVIC EON ERS Live Sensory Input Integration Package.

Provides local FastAPI WebSocket server, session management, zero-retention memory
pipeline, and responsive browser dashboard for real-time webcam and microphone input.
"""

from __future__ import annotations

from eon_ers.live.dashboard import get_dashboard_html
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.server import create_live_app

__all__ = [
    "LiveSessionManager",
    "create_live_app",
    "get_dashboard_html",
]
