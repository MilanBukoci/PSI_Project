"""
services/uc02_dispatcher_service.py – Business logic for UC02: Dispatcher assigns
shipments to couriers.  Uses mock/hardcoded data until a real backend is connected.
"""

import logging
from models.courier import Courier
from models.shipment import Shipment, PackageDetails, Address

log = logging.getLogger(__name__)


# ── Mock unassigned shipments ─────────────────────────────────────────────────
def _make_mock_unassigned() -> list[Shipment]:
    """Shipments that have been created but not yet assigned to any courier."""
    return [
        Shipment(
            id="ZP-20260427-1001",
            package=PackageDetails(size_x=30, size_y=20, size_z=15, weight=2.5,
                                   contents="Elektronika"),
            sender=Address(first_name="Ján", last_name="Horváth",
                           street="Hlavná 12", postal_code="81101"),
            recipient=Address(first_name="Peter", last_name="Novák",
                              street="Obchodná 5", postal_code="81106"),
            status="pending",
            route="Bratislava, Hlavná 12 -> Obchodná 5",
        ),
        Shipment(
            id="ZP-20260427-1002",
            package=PackageDetails(size_x=20, size_y=15, size_z=10, weight=1.0,
                                   contents="Oblečenie"),
            sender=Address(first_name="Anna", last_name="Kováčová",
                           street="Štúrova 8", postal_code="91701"),
            recipient=Address(first_name="Mária", last_name="Slobodová",
                              street="Kollárova 3", postal_code="91701"),
            status="pending",
            route="Trnava, Štúrova 8 -> Kollárova 3",
        ),
        Shipment(
            id="ZP-20260427-1003",
            package=PackageDetails(size_x=50, size_y=40, size_z=30, weight=7.5,
                                   contents="Spotrebič"),
            sender=Address(first_name="Tomáš", last_name="Bielik",
                           street="Nám. SNP 1", postal_code="01001"),
            recipient=Address(first_name="Eva", last_name="Malá",
                              street="Hurbanova 22", postal_code="01001"),
            status="pending",
            route="Žilina, Nám. SNP 1 -> Hurbanova 22",
        ),
        Shipment(
            id="ZP-20260427-1004",
            package=PackageDetails(size_x=15, size_y=10, size_z=8, weight=0.6,
                                   contents="Knihy"),
            sender=Address(first_name="Lucia", last_name="Kráľová",
                           street="Mlynská 7", postal_code="04001"),
            recipient=Address(first_name="Dávid", last_name="Černák",
                              street="Kováčska 15", postal_code="04001"),
            status="pending",
            route="Košice, Mlynská 7 -> Kováčska 15",
        ),
        Shipment(
            id="ZP-20260427-1005",
            package=PackageDetails(size_x=25, size_y=18, size_z=12, weight=3.2,
                                   contents="Kozmetika"),
            sender=Address(first_name="Monika", last_name="Varga",
                           street="Štefánikova 3", postal_code="94901"),
            recipient=Address(first_name="Katarína", last_name="Balážová",
                              street="Pribinova 10", postal_code="94901"),
            status="pending",
            route="Nitra, Štefánikova 3 -> Pribinova 10",
        ),
        # Already assigned shipment for demonstration
        Shipment(
            id="ZP-20260426-0099",
            package=PackageDetails(size_x=20, size_y=15, size_z=10, weight=1.8,
                                   contents="Hračky"),
            sender=Address(first_name="Zippy", last_name="Sklad",
                           street="Skladová 1", postal_code="91701"),
            recipient=Address(first_name="Ján", last_name="Novák",
                              street="Hlavná 5", postal_code="91701"),
            status="pridelená",
            route="Sklad -> Trnava, Hlavná 5",
            assigned_courier_id="123456",
        ),
    ]


# ── Mock couriers ─────────────────────────────────────────────────────────────
def _make_mock_couriers() -> list[Courier]:
    return [
        Courier(id="123456", name="Marek Sloboda",
                is_available=True, current_load=5, max_load=10),
        Courier(id="654321", name="Tomáš Kováč",
                is_available=True, current_load=2, max_load=10),
        Courier(id="111111", name="Jana Malá",
                is_available=False, current_load=0, max_load=10),   # nie je v práci
        Courier(id="222222", name="Peter Horváth",
                is_available=True, current_load=10, max_load=10),   # plne vyťažený
    ]


class UC02DispatcherService:
    """Handles dispatcher workflow for UC02 – assigning shipments to couriers."""

    def __init__(self):
        self._shipments: list[Shipment] = _make_mock_unassigned()
        self._couriers: list[Courier] = _make_mock_couriers()
        self._notifications: dict[str, list[str]] = {}  # courier_id -> messages

    # ── Shipment queries ──────────────────────────────────────────────────────

    def get_all_shipments(self) -> list[dict]:
        """Return all shipments as dicts for screens."""
        return [self._to_dict(s) for s in self._shipments]

    def get_unassigned_shipments(self) -> list[dict]:
        """Return only shipments that have not been assigned yet."""
        return [self._to_dict(s) for s in self._shipments
                if s.assigned_courier_id is None and s.status == "pending"]

    # ── Courier queries ───────────────────────────────────────────────────────

    def get_couriers(self) -> list[dict]:
        """Return all couriers with their availability and load."""
        result = []
        for c in self._couriers:
            result.append({
                "id": c.id,
                "name": c.name,
                "is_available": c.is_available,
                "current_load": c.current_load,
                "max_load": c.max_load,
                "is_full": c.current_load >= c.max_load,
            })
        return result

    # ── Assignment ────────────────────────────────────────────────────────────

    def assign_shipments(
        self, shipment_ids: list[str], courier_id: str
    ) -> dict:
        """
        Assign selected shipments to the chosen courier.

        Returns dict with:
            ok: bool
            message: str
            assigned_count: int (on success)
        """
        # Find courier
        courier = self._get_courier(courier_id)
        if courier is None:
            return {"ok": False, "message": "Kuriér neexistuje."}

        # Alt. scenario 5.1 – courier not at work
        if not courier.is_available:
            return {
                "ok": False,
                "message": f"Kuriér {courier.name} nie je v práci. "
                           f"Vyberte iného kuriéra.",
            }

        # Exception – courier fully loaded
        remaining_capacity = courier.max_load - courier.current_load
        if remaining_capacity <= 0:
            # Notify dispatcher
            return {
                "ok": False,
                "message": f"Kuriér {courier.name} je plne vyťažený "
                           f"({courier.current_load}/{courier.max_load}). "
                           f"Zásielka nebude pridelená.",
            }

        # Check how many we can actually assign
        shipments_to_assign = []
        for sid in shipment_ids:
            s = self._get_shipment(sid)
            if s and s.assigned_courier_id is None:
                shipments_to_assign.append(s)

        if not shipments_to_assign:
            return {"ok": False, "message": "Žiadna platná nepridelená zásielka."}

        if len(shipments_to_assign) > remaining_capacity:
            return {
                "ok": False,
                "message": f"Kuriér {courier.name} má kapacitu len na "
                           f"{remaining_capacity} zásielok, ale vybraných je "
                           f"{len(shipments_to_assign)}.",
            }

        # ── Assign ────────────────────────────────────────────────────────────
        for s in shipments_to_assign:
            s.assigned_courier_id = courier.id
            s.status = "pridelená"
            log.info("UC02: Shipment %s assigned to courier %s", s.id, courier.id)

        courier.current_load += len(shipments_to_assign)

        # Notify courier (mock)
        note = (
            f"Máte {len(shipments_to_assign)} nových zásielok na doručenie. "
            f"Vaša trasa bola automaticky aktualizovaná."
        )
        self._notifications.setdefault(courier.id, []).append(note)

        return {
            "ok": True,
            "message": f"Úspešne pridelených {len(shipments_to_assign)} "
                       f"zásielok kuriérovi {courier.name}.",
            "assigned_count": len(shipments_to_assign),
            "courier_notification": note,
        }

    # ── Notifications ─────────────────────────────────────────────────────────

    def get_notifications(self, courier_id: str) -> list[str]:
        """Return pending notifications for a courier."""
        return self._notifications.get(courier_id, [])

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_shipment(self, shipment_id: str) -> Shipment | None:
        for s in self._shipments:
            if s.id == shipment_id:
                return s
        return None

    def _get_courier(self, courier_id: str) -> Courier | None:
        for c in self._couriers:
            if c.id == courier_id:
                return c
        return None

    @staticmethod
    def _to_dict(s: Shipment) -> dict:
        return {
            "id": s.id,
            "sender": f"{s.sender.first_name} {s.sender.last_name}",
            "sender_address": s.sender.street,
            "recipient": f"{s.recipient.first_name} {s.recipient.last_name}",
            "recipient_address": s.recipient.street,
            "route": s.route,
            "status": s.status,
            "weight": s.package.weight,
            "contents": s.package.contents,
            "assigned_courier_id": s.assigned_courier_id,
        }
