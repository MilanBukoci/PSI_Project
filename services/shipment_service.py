"""
services/shipment_service.py – Business logic for creating and managing orders.
Uses mock data until a real backend is connected.
"""

import logging
from models.shipment import Shipment, PackageDetails, Address

log = logging.getLogger(__name__)


# ── Mock existing orders shown on the home screen ────────────────────────────
MOCK_ACTIVE_shipmentS = [
    {
        "id":     "ZP-20260323-8841",
        "route":  "Košice -> Ram K.",
        "status": "Na ceste",
        "color":  (0.18, 0.8, 0.44, 1),   # green
    },
    {
        "id":     "ZP-20260318-4412",
        "route":  "Žilina -> Tomaš H.",
        "status": "Čaká",
        "color":  (0.961, 0.651, 0.137, 1),  # orange
    },
]


class ShipmentService:
    """Handles order creation, validation, and (stub) submission."""

    def __init__(self):
        self._current_shipment: Shipment | None = None

    # ── Current order management ──────────────────────────────────────────────

    def new_shipment(self) -> Shipment:
        self._current_shipment = Shipment()
        return self._current_shipment

    @property
    def current_shipment(self) -> Shipment:
        if self._current_shipment is None:
            self._current_shipment = Shipment()
        return self._current_shipment

    def save_package_details(self, x, y, z, weight, contents, instructions):
        pkg = self.current_shipment.package
        pkg.size_x = self._to_float(x)
        pkg.size_y = self._to_float(y)
        pkg.size_z = self._to_float(z)
        pkg.weight = self._to_float(weight)
        pkg.contents = contents
        pkg.special_instructions = instructions
        log.debug("Package saved: %s", pkg)

    def save_addresses(self, sender: dict, recipient: dict):
        s = self.current_shipment.sender
        s.first_name   = sender.get("first_name", "")
        s.last_name    = sender.get("last_name", "")
        s.street       = sender.get("street", "")
        s.postal_code  = sender.get("postal_code", "")

        r = self.current_shipment.recipient
        r.first_name   = recipient.get("first_name", "")
        r.last_name    = recipient.get("last_name", "")
        r.street       = recipient.get("street", "")
        r.postal_code  = recipient.get("postal_code", "")
        log.debug("Addresses saved")

    def save_payment_method(self, method: str):
        self.current_shipment.payment_method = method

    def submit_shipment(self, simulate_failure=False) -> bool:
        """
        Mock submission. Returns True on success, False on failure.
        Set simulate_failure=True to test the error state.
        """
        shipment = self.current_shipment
        if simulate_failure:
            shipment.status = "failed"
            log.info("shipment %s – payment FAILED (simulated)", shipment.id)
            return False

        shipment.status = "paid"
        log.info("shipment %s submitted successfully", shipment.id)
        MOCK_ACTIVE_shipmentS.append({
            "id": shipment.id,
            "route": shipment.route,
            "status": "Pripravuje sa",
            "color": (0.961, 0.651, 0.137, 1),  # orange
        })
        return True

    def get_active_shipments(self) -> list[dict]:
        return MOCK_ACTIVE_shipmentS

    def redirect(self):
        pass

    def assign_courier(self, courier_id: str):
        pass

    def update_status(self, status: str):
        pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
