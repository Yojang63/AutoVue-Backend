"""
WebSocket connection manager.

Why WebSockets over SSE here: the dashboard needs continuous low-latency
push (telemetry ticks every ~0.1-1s) AND we want a single channel that can
later carry control acknowledgements or bidirectional messages (e.g. a
future mobile app sending "pause" over the same socket instead of a
separate REST call). SSE is simpler but one-directional and less
consistently supported by older mobile WebViews; WebSockets are supported
everywhere we're likely to deploy this (browsers, React Native, Flutter)
and are the standard choice for this kind of live-telemetry dashboard.
"""
import logging
from fastapi import WebSocket

logger = logging.getLogger("obd_simulator.websocket")


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info("WebSocket client connected (%d total)", len(self.active))

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.info("WebSocket client disconnected (%d total)", len(self.active))

    async def broadcast_json(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


telemetry_manager = ConnectionManager()
log_manager = ConnectionManager()
