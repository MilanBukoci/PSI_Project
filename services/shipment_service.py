import logging
from datetime import date, timedelta
from models.shipment import Shipment, PackageDetails, Address

log = logging.getLogger(__name__)


MOCK_ACTIVE_shipmentS = [
    {
        "id":     "ZP-20260323-8841",
        "route":  "Košice -> Ram K.",
        "status": "Na ceste",
        "color":  (0.18, 0.8, 0.44, 1),   # zelena
    },
    {
        "id":     "ZP-20260318-4412",
        "route":  "Žilina -> Tomaš H.",
        "status": "Čaká",
        "color":  (0.961, 0.651, 0.137, 1),  # oranzova
    },
]


class ShipmentService:
    """Handles order creation, validation, and (stub) submission."""

    def __init__(self):
        # Mock zásielok pre UC01 (presmerovanie / zmena dátumu príjemcom). Kľúčové polia:
        # status – vstupná podmienka (nie „Doručené“, nie blokovaný stav podľa can_redirect_*);
        # depot_region / PSČ – výpočet „rovnaký región“ vs. doplatok a notifikácie.
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

    # ── Menezment objednavok ──────────────────────────────────────────────

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
        s.first_name = sender.get("first_name", "")
        s.last_name = sender.get("last_name", "")
        s.street = sender.get("street", "")
        s.postal_code = sender.get("postal_code", "")

        r = self.current_shipment.recipient
        r.first_name = recipient.get("first_name", "")
        r.last_name = recipient.get("last_name", "")
        r.street = recipient.get("street", "")
        r.postal_code = recipient.get("postal_code", "")

        self.current_shipment.route = f"{s.postal_code[:2]} -> {r.first_name} {r.last_name}"
        log.debug("Addresses saved")

    def save_payment_method(self, method: str):
        self.current_shipment.payment_method = method

    def submit_shipment(self, simulate_failure=False) -> bool:
        shipment = self.current_shipment
        if simulate_failure:
            shipment.status = "failed"
            log.info("shipment %s – payment FAILED (simulated)", shipment.id)
            return False

        shipment.status = "paid"
        shipment.delivery_date = date.today() + timedelta(days=shipment.delivery_days)  # ← add this
        log.info("shipment %s submitted successfully", shipment.id)
        self._uc01_shipments[shipment.id] = {
            "id": shipment.id,
            "recipient_name": f"{shipment.recipient.first_name} {shipment.recipient.last_name}",
            "address": shipment.recipient.street,
            "postal_code": shipment.recipient.postal_code,
            "status": "Pripravuje sa",
            "depot_region": shipment.recipient.postal_code[:2],
            "delivery_date": shipment.delivery_date,
            "payment_status": "nezaplatená",
            "pending_surcharge": 0.0,
        }
        return True

    def get_active_shipments(self) -> list[dict]:
        status_colors = {
            "Na ceste": (0.18, 0.8, 0.44, 1),
            "Čaká": (0.961, 0.651, 0.137, 1),
            "Doručuje sa": (0.169, 0.169, 1.0, 1),
            "Doručené": (0.75, 0.75, 0.75, 1),
        }
        return [
            {
                "id": s["id"],
                "route": f"{s['depot_region']} -> {s['recipient_name']}",
                "status": s["status"],
                "color": status_colors.get(s["status"], (0.5, 0.5, 0.5, 1)),
            }
            for s in self._uc01_shipments.values()
        ]

    # UC01: Presmerovanie zásielky používateľom (zákazník / príjemca)

    def get_redirect_shipment(self, shipment_id: str) -> dict | None:
        """
        Načíta záznam zásielky pre obrazovky UC01 podľa čísla z objednávky.

        Vracia kópiu slovníka, aby rozhranie nemohlo priamo meniť interný stav bez služby.
        Ak číslo neexistuje alebo je prázdne, nevráti žiadny záznam.
        """
        if not shipment_id:
            return None
        record = self._uc01_shipments.get(shipment_id.strip().upper())
        if not record:
            return None
        return dict(record)

    def can_redirect_shipment(self, shipment: dict) -> tuple[bool, str]:
        """
        Kontrola vstupných podmienok UC01: či je ešte možné meniť doručovacie údaje.

        Blokuje zmeny pri stave „Na ceste“ a pri už doručenej zásielke.
        Pri úspechu vráti dvojicu (pravda, prázdny dôvod chyby).
        """
        status = shipment.get("status", "")
        if status == "Na ceste":
            return False, "Zmena doručovacích informácií nieje možná, keď je balík už na ceste."
        if status == "Doručené":
            return False, "Zásielka je už doručená, presmerovanie nie je možné."
        return True, ""

    def evaluate_redirect_address(self, shipment: dict, new_postal_code: str) -> dict:
        """
        Vyhodnotí novú adresu pri presmerovaní: vzdialenosť a „región“.

        Kľúčové časti:
        - overenie PSČ (minimálna dĺžka);
        - výpočet vzdialenosti – ak presahuje 550 km, služba nie je dostupná (výnimka);
        - porovnanie prvých dvoch číslic PSČ ako zjednodušenie „v dosahu pôvodného depa“
          oproti inému regiónu; pri zmene regiónu sa doplatok vypočíta pomocnou metódou.

        Vráti slovník: pri chybe dôvod v poli reason; pri úspechu aj vzdialenosť v km,
        príznak rovnakého regiónu a výšku doplatku.
        """
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

        # Prvé dve číslice PSČ: „v dosahu pôvodného depa“ (vetva A) vs. iný región (vetva B + doplatok).
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
        """
        Trvalo zapíše novú adresu doručenia po úspešnom priebehu UC01.

        Opätovne kontroluje existenciu zásielky, či je presmerovanie povolené, stav „Doručuje sa“
        a výsledok vyhodnotenia novej adresy. Ak je doplatok väčší ako nula, vyžaduje potvrdenú úhradu.
        Poznámku o informovaní kuriéra alebo dispečera uloží podľa toho, či ide o ten istý región.
        V odpovedi uvedie aj zoznam rolí pre notifikačnú službu (kuriér oproti dispečerovi pri doplatku).
        """
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
        """
        Validácia nového dátumu doručenia – alternatívny scenár UC01.

        Dátum nesmie byť v minulosti a nesmie presiahnuť jeden týždeň oproti referenčnému
        (aktuálny plánovaný dátum doručenia alebo dnes, podľa výpočtu základného dátumu v kóde).
        Ak je dátum v poriadku, nevráti text chyby; inak vráti správu pre používateľa.
        """
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
        """
        Zapíše nový dátum doručenia (alternatívny scenár UC01).

        Rovnaké vstupné obmedzenia ako pri adrese (vrátane stavu „Doručuje sa“).
        Po úspechu vráti text notifikácie pre kuriéra (v mocku sa upozornenie vždy odošle).
        """
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
        """
        Pripraví stav platby pred potvrdením zmeny adresy.

        Uloží vypočítaný doplatok do poľa čakajúceho doplatku a nastaví stav platby tak,
        aby rozhranie mohlo pred finálnym zápisom adresy vynútiť klik na „Zaplatiť“.
        """
        shipment = self._uc01_shipments.get(shipment_id.strip().upper())
        if not shipment:
            return
        shipment["pending_surcharge"] = round(surcharge, 2)
        shipment["payment_status"] = "nezaplatená" if surcharge > 0 else shipment.get("payment_status", "nezaplatená")

    def mark_redirect_payment_paid(self, shipment_id: str) -> dict:
        """
        Simuluje úhradu doplatku alebo neuhradenej sumy pred dokončením presmerovania.

        Po zaplatení môže rozhranie dokončiť zmenu adresy so zaplateným doplatkom.
        """
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

    # Pomocne funkcie

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _estimate_distance_km(code_a: str, code_b: str) -> int:
        """
        Zjednodušený odhad vzdialenosti medzi dvoma PSČ.

        Používa sa pri limite 550 km a pri výpočte doplatku; ide o zjednodušenú simuláciu, nie mapové API.
        """
        if code_a == code_b:
            return 5
        try:
            prefix_delta = abs(int(code_a[:2]) - int(code_b[:2]))
        except ValueError:
            prefix_delta = 12
        return 35 + prefix_delta * 42

    @staticmethod
    def _compute_surcharge(distance_km: int) -> float:
        """
        Vypočíta doplatok pri presmerovaní do iného „regiónu“.

        Pri krátkej vzdialenosti vráti 0; inak lineárna zložka nad prahom 120 km.
        """
        if distance_km <= 120:
            return 0.0
        return round(1.5 + (distance_km - 120) * 0.015, 2)
