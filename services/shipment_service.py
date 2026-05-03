import logging
from datetime import date, timedelta
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
        self._uc01_shipments: dict[str, dict] = {
            "ZP-20260323-8841": {
                "id": "ZP-20260323-8841",
                "recipient_name": "Ram K.",
                "address": "Košice, Kováčska 7",
                "postal_code": "04001",
                "status": "Na ceste",
                "depot_region": "KE",
                "delivery_date": date.today() + timedelta(days=2),
                "payment_status": "nezaplatená",
                "amount_due": 4.99,
                "pending_surcharge": 0.0,
            },
            "ZP-20260318-4412": {
                "id": "ZP-20260318-4412",
                "recipient_name": "Tomaš H.",
                "address": "Žilina, Hurbanova 15",
                "postal_code": "01001",
                "status": "Čaká",
                "depot_region": "ZA",
                "delivery_date": date.today() + timedelta(days=3),
                "payment_status": "nezaplatená",
                "amount_due": 6.49,
                "pending_surcharge": 0.0,
            },
            "ZP-20260420-1200": {
                "id": "ZP-20260420-1200",
                "recipient_name": "Milan P.",
                "address": "Bratislava, Námestie 1",
                "postal_code": "81101",
                "status": "Doručené",
                "depot_region": "BA",
                "delivery_date": date.today() - timedelta(days=1),
                "payment_status": "zaplatená",
                "amount_due": 0.0,
                "pending_surcharge": 0.0,
            },
            "ZP-20260420-2201": {
                "id": "ZP-20260420-2201",
                "recipient_name": "Anna K.",
                "address": "Trnava, Študentská 12",
                "postal_code": "91701",
                "status": "Doručuje sa",
                "depot_region": "TT",
                "delivery_date": date.today(),
                "payment_status": "nezaplatená",
                "amount_due": 5.99,
                "pending_surcharge": 0.0,
            },
        }

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

    # ── UC01 redirect shipment by recipient ───────────────────────────────────

    def get_redirect_shipment(self, shipment_id: str) -> dict | None:
        if not shipment_id:
            return None
        record = self._uc01_shipments.get(shipment_id.strip().upper())
        if not record:
            return None
        return dict(record)

    def can_redirect_shipment(self, shipment: dict) -> tuple[bool, str]:
        status = shipment.get("status", "")
        if status == "Na ceste":
            return False, "Zmena doručovacích informácií nieje možná, keď je balík už na ceste."
        if status == "Doručené":
            return False, "Zásielka je už doručená, presmerovanie nie je možné."
        return True, ""

    def evaluate_redirect_address(self, shipment: dict, new_postal_code: str) -> dict:
        new_code = (new_postal_code or "").strip()
        old_code = shipment.get("postal_code", "").strip()

        if len(new_code) < 4:
            return {
                "ok": False,
                "reason": "Zadajte platné PSČ.",
            }

        distance_km = self._estimate_distance_km(old_code, new_code)
        if distance_km > 550:
            return {
                "ok": False,
                "reason": "Nová adresa je mimo rozsah služby (viac ako 550 km).",
                "distance_km": distance_km,
            }

        same_region = old_code[:2] == new_code[:2]
        surcharge = 0.0 if same_region else self._compute_surcharge(distance_km)
        return {
            "ok": True,
            "distance_km": distance_km,
            "same_region": same_region,
            "surcharge": surcharge,
        }

    def apply_redirect_address(
        self,
        shipment_id: str,
        new_address: str,
        new_postal_code: str,
        surcharge_paid: bool,
    ) -> dict:
        shipment = self._uc01_shipments.get(shipment_id.strip().upper())
        if not shipment:
            return {"ok": False, "message": "Zásielka neexistuje."}

        can_redirect, message = self.can_redirect_shipment(shipment)
        if not can_redirect:
            return {"ok": False, "message": message}
        if shipment.get("status") == "Doručuje sa":
            return {"ok": False, "message": "Zásielka je práve doručovaná, adresu už nie je možné zmeniť."}

        check = self.evaluate_redirect_address(shipment, new_postal_code)
        if not check.get("ok"):
            return {"ok": False, "message": check.get("reason", "Presmerovanie sa nepodarilo.")}

        surcharge = check.get("surcharge", 0.0)
        if surcharge > 0 and not surcharge_paid:
            return {"ok": False, "message": "Pred potvrdením je potrebné uhradiť doplatok."}

        shipment["address"] = new_address.strip()
        shipment["postal_code"] = new_postal_code.strip()
        shipment["pending_surcharge"] = 0.0
        shipment["payment_status"] = "zaplatená" if surcharge > 0 else shipment.get("payment_status", "nezaplatená")
        shipment["last_redirect_note"] = (
            "Kuriér bol informovaný o zmene trasy."
            if check.get("same_region")
            else "Dispečer bol informovaný o potrebe preplánovania trasy."
        )
        return {
            "ok": True,
            "message": "Adresa doručenia bola úspešne zmenená.",
            "notify": shipment["last_redirect_note"],
            "surcharge": surcharge,
            # Pri doplatku treba vedieť dispečera (rovnaký inbox ako obrazovka UC02NotificationsScreen).
            "notify_roles": ["customer", "dispatcher"] if surcharge > 0 else ["customer", "courier"],
        }

    def validate_new_delivery_date(self, new_date: date | None, reference_date: date | None = None) -> str | None:
        if new_date is None:
            return "Zadajte dátum doručenia."

        today = date.today()
        baseline = reference_date if reference_date and reference_date > today else today
        day_delta = (new_date - today).days
        if day_delta < 0:
            return "Dátum doručenia nemôže byť v minulosti."
        max_allowed = baseline + timedelta(days=7)
        if new_date > max_allowed:
            return "Dátum doručenia môže byť najviac o 7 dní."
        return None

    def apply_delivery_date_change(self, shipment_id: str, new_date: date) -> dict:
        shipment = self._uc01_shipments.get(shipment_id.strip().upper())
        if not shipment:
            return {"ok": False, "message": "Zásielka neexistuje."}

        can_redirect, message = self.can_redirect_shipment(shipment)
        if not can_redirect:
            return {"ok": False, "message": message}
        if shipment.get("status") == "Doručuje sa":
            return {"ok": False, "message": "Zásielka je práve doručovaná, dátum už nie je možné zmeniť."}

        error = self.validate_new_delivery_date(new_date, shipment.get("delivery_date"))
        if error:
            return {"ok": False, "message": error}

        shipment["delivery_date"] = new_date
        return {
            "ok": True,
            "message": "Dátum doručenia bol úspešne zmenený.",
            "notify": "Kuriér bol informovaný o zmene dátumu doručenia.",
            "notify_roles": ["customer", "courier"],
        }

    def prepare_redirect_surcharge(self, shipment_id: str, surcharge: float) -> None:
        shipment = self._uc01_shipments.get(shipment_id.strip().upper())
        if not shipment:
            return
        shipment["pending_surcharge"] = round(surcharge, 2)
        shipment["payment_status"] = "nezaplatená" if surcharge > 0 else shipment.get("payment_status", "nezaplatená")

    def mark_redirect_payment_paid(self, shipment_id: str) -> dict:
        shipment = self._uc01_shipments.get(shipment_id.strip().upper())
        if not shipment:
            return {"ok": False, "message": "Zásielka neexistuje."}

        amount = float(shipment.get("pending_surcharge", 0.0))
        if amount <= 0:
            amount = float(shipment.get("amount_due", 0.0))
        shipment["payment_status"] = "zaplatená"
        shipment["amount_due"] = 0.0
        if amount > 0:
            shipment["pending_surcharge"] = 0.0
            return {"ok": True, "message": f"Poplatok {amount:.2f} EUR bol úspešne zaplatený."}
        return {"ok": True, "message": "Platba bola úspešne zaevidovaná."}

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

    @staticmethod
    def _estimate_distance_km(code_a: str, code_b: str) -> int:
        if code_a == code_b:
            return 5
        try:
            prefix_delta = abs(int(code_a[:2]) - int(code_b[:2]))
        except ValueError:
            prefix_delta = 12
        return 35 + prefix_delta * 42

    @staticmethod
    def _compute_surcharge(distance_km: int) -> float:
        if distance_km <= 120:
            return 0.0
        return round(1.5 + (distance_km - 120) * 0.015, 2)
