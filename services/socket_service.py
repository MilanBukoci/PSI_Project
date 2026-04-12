"""
services/socket_service.py – WebSocket stub for later implementation.

Replace the body of each method with real socket.io / websockets logic
when the backend is ready.
"""

import logging

log = logging.getLogger(__name__)


class SocketService:
    """
    Stub WebSocket service.
    All methods are no-ops until a real server is available.
    """

    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        self._connected = False
        self._callbacks: dict[str, list] = {}

    # ── Connection lifecycle ──────────────────────────────────────────────────

    def connect(self) -> None:
        """Open the WebSocket connection."""
        log.info("[SocketService] connect() – stub, not yet implemented")
        self._connected = False   # stays False until real impl

    def disconnect(self) -> None:
        """Close the WebSocket connection."""
        log.info("[SocketService] disconnect() – stub")
        self._connected = False

    # ── Event subscription ────────────────────────────────────────────────────

    def on(self, event: str, callback) -> None:
        """Register a callback for a named socket event."""
        self._callbacks.setdefault(event, []).append(callback)
        log.debug("[SocketService] on('%s') registered", event)

    def off(self, event: str, callback=None) -> None:
        """Unregister a callback (or all callbacks for an event)."""
        if callback is None:
            self._callbacks.pop(event, None)
        else:
            self._callbacks.get(event, []).remove(callback)

    # ── Emitting events ───────────────────────────────────────────────────────

    def emit(self, event: str, data: dict | None = None) -> None:
        """Send an event to the server."""
        log.info("[SocketService] emit('%s', %s) – stub", event, data)
        # TODO: send via websockets / socket.io

    # ── Order-specific helpers (semantic API) ─────────────────────────────────

    def subscribe_shipment_status(self, shipment_id: str, callback) -> None:
        """Listen for real-time status updates on a specific order."""
        self.on(f"shipment_status:{shipment_id}", callback)
        self.emit("subscribe_shipment", {"shipment_id": shipment_id})

    def submit_shipment(self, shipment_data: dict) -> None:
        """Push a new order to the server."""
        self.emit("create_shipment", shipment_data)

    # ── Internal dispatcher ───────────────────────────────────────────────────

    def _dispatch(self, event: str, data) -> None:
        """Called by the receive loop when a message arrives."""
        for cb in self._callbacks.get(event, []):
            cb(data)
