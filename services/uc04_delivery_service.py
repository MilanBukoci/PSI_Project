"""
services/uc04_delivery_service.py – Business logic for UC04: Courier delivery.
Uses mock/hardcoded data until a real backend is connected.
"""

import logging

from models.courier import Courier

log = logging.getLogger(__name__)


# ── Mock data ─────────────────────────────────────────────────────────────────

MOCK_TODAY_SHIPMENTS = [
    {
        "id": "ZP-20260414-0001",
        "address": "Trnava, Hlavná 5",
        "recipient": "Ján Novák",
        "phone": "0900 123 456",
        "status": "Na vyzdvihnutie",
        "section": "B1",
        "rack": "01",
        "police": "04",
        "size": "L",
        "pin": "4782",
    },
    {
        "id": "ZP-20260414-0002",
        "address": "Trnava, Nová 2",
        "recipient": "Anna Kováč",
        "phone": "0911 222 333",
        "status": "Na vyzdvihnutie",
        "section": "A2",
        "rack": "03",
        "police": "02",
        "size": "M",
        "pin": "1193",
    },
    {
        "id": "ZP-20260414-0003",
        "address": "Trnava, Stará 5",
        "recipient": "Dávid Kováč",
        "phone": "0944 555 777",
        "status": "Na vyzdvihnutie",
        "section": "C3",
        "rack": "07",
        "police": "01",
        "size": "S",
        "pin": "9021",
    },
    {
        "id": "ZP-20260414-0004",
        "address": "Trnava, Hlavná 5",
        "recipient": "Marta Slobodová",
        "phone": "0902 888 111",
        "status": "Na vyzdvihnutie",
        "section": "B1",
        "rack": "02",
        "police": "03",
        "size": "XL",
        "pin": "3344",
    },
    {
        "id": "ZP-20260414-0005",
        "address": "Trnava, Stará 2 ",
        "recipient": "Ján Kováč",
        "phone": "0901 123 456",
        "status": "Na vyzdvihnutie",
        "section": "B1",
        "rack": "01",
        "police": "05",
        "size": "S",
        "pin": "4783",
    },
]

# Optimised stop order for the route (indices into MOCK_TODAY_SHIPMENTS)
MOCK_ROUTE_ORDER = [
    "Hlavná 5",
    "Stará 5",
    "Nová 2",
    "...",
]

class UC04DeliveryService:
    """Handles courier delivery workflow for UC04."""

    def __init__(self):
        self._shipments = [dict(s) for s in MOCK_TODAY_SHIPMENTS]
        self._pickup_index = 0
        self._picked_up = False          # True after pickup confirmed
        self._current_index = 0          # which stop we're on
        self._unavailable_counts: dict[str, int] = {}   # shipment_id -> attempts
        self._courier: Courier | None = None

    # ── Shipment list ─────────────────────────────────────────────────────────

    def get_today_shipments(self) -> list[dict]:
        return self._shipments

    def get_shipment_by_id(self, shipment_id: str) -> dict | None:
        for s in self._shipments:
            if s["id"] == shipment_id:
                return s
        return None

    # ── Courier ───────────────────────────────────────────────────────────────

    def set_courier(self, courier_id: str, name: str) -> None:
        """Zavolá sa pri prihlásení kuriéra."""
        self._courier = Courier(
            id=courier_id,
            name=name,
            is_available=False,  # už pracuje
            current_load=len(self._shipments),
        )

    def get_courier(self) -> Courier | None:
        return self._courier

    # ── Pickup ────────────────────────────────────────────────────────────────

    def confirm_pickup(self, index: int) -> None:
        """Courier confirmed pickup of one package from warehouse."""
        s = self._shipments[index]
        s["status"] = "Vyzdvihnutá"

    def all_picked_up(self) -> None:
        """Courier started delivering."""

        self._picked_up = True
        for s in self._shipments:
            if s["status"] == "Vyzdvihnutá":
                s["status"] = "Na ceste"
            log.info("UC04: Pickup confirmed, %d shipments", len(self._shipments))

    # ── Delivery ──────────────────────────────────────────────────────────────

    def confirm_delivery_pin(self, shipment_id: str, pin: str) -> bool:
        """Returns True if PIN matches."""
        shipment = self.get_shipment_by_id(shipment_id)
        if shipment and shipment["pin"] == pin.strip():
            shipment["status"] = "Doručené"
            self._update_courier_load()
            log.info("UC04: %s delivered via PIN", shipment_id)
            return True
        log.warning("UC04: Wrong PIN for %s", shipment_id)
        return False

    def confirm_delivery_signature(self, shipment_id: str) -> None:
        """Signature was captured — mark as delivered."""
        shipment = self.get_shipment_by_id(shipment_id)
        if shipment:
            shipment["status"] = "Doručené"
            self._update_courier_load()
            log.info("UC04: %s delivered via signature", shipment_id)

    # ── Unavailable customer ──────────────────────────────────────────────────

    def mark_unavailable(self, shipment_id: str) -> int:
        """
        Increments unavailable counter.
        Returns the new attempt count (1 = first miss, 2+ = return to depot).
        """
        count = self._unavailable_counts.get(shipment_id, 0) + 1
        self._unavailable_counts[shipment_id] = count
        shipment = self.get_shipment_by_id(shipment_id)
        if shipment:
            shipment["status"] = "Nedostupný" if count == 1 else "Vrátenie"
            if count >= 2:
                self._update_courier_load()
        log.info("UC04: %s unavailable (attempt %d)", shipment_id, count)
        return count

    def get_unavailable_count(self, shipment_id: str) -> int:
        return self._unavailable_counts.get(shipment_id, 0)

    # ── Route ─────────────────────────────────────────────────────────────────

    def get_route_stops(self) -> list[str]:
        return MOCK_ROUTE_ORDER

    # ── Helper ────────────────────────────────────────────────────────────────

    def _update_courier_load(self) -> None:
        """Aktualizuje current_load a is_available podľa stavu zásielok."""
        if not self._courier:
            return
        pending = [s for s in self._shipments
                   if s["status"] not in ("Doručené", "Vrátenie")]
        self._courier.current_load = len(pending)
        self._courier.is_available = len(pending) == 0