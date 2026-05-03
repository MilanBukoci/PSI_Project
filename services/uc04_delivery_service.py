"""
services/uc04_delivery_service.py – Business logic for UC04: Courier delivery.
Uses mock/hardcoded data until a real backend is connected.
"""

import logging
from datetime import date
from models.courier import Courier
from models.shipment import Shipment, PackageDetails, Address

log = logging.getLogger(__name__)

# ── Mock route order ──────────────────────────────────────────────────────────
# Zoznam zastávok v optimálnom poradí pre dnešnú trasu kuriéra
MOCK_ROUTE_ORDER = [
    "Hlavná 5",
    "Stará 5",
    "Nová 2",
    "...",
]

# ── Mock Shipment objects ─────────────────────────────────────────────────────
def _make_mock_shipments() -> list[Shipment]:
    """
        Vytvorí zoznam testovacích zásielok pri každom prihlásení kuriéra.
        Každá zásielka obsahuje informácie o príjemcovi, odosielateľovi,
        balíku a umiestnení v sklade (sekcia, regál, polica).
        V reálnej aplikácii by tieto dáta prišli zo servera.
        """
    return [
        Shipment(
            id="ZP-20260414-0001",
            package=PackageDetails(size_x=30, size_y=20, size_z=15, weight=2.5, contents="Elektronika"),
            sender=Address(first_name="Zippy", last_name="Sklad", street="Skladová 1", postal_code="91701"),
            recipient=Address(first_name="Ján", last_name="Novák", street="Hlavná 5", postal_code="91701"),
            status="Na vyzdvihnutie",
            route="Sklad -> Trnava, Hlavná 5",
            assigned_courier_id="123456",
            delivery_date=date.today(),
            pin="4782", phone="0900 123 456", section="B1", rack="01", police="04", size="L",
        ),
        Shipment(
            id="ZP-20260414-0002",
            package=PackageDetails(size_x=20, size_y=15, size_z=10, weight=1.2, contents="Oblečenie"),
            sender=Address(first_name="Zippy", last_name="Sklad", street="Skladová 1", postal_code="91701"),
            recipient=Address(first_name="Anna", last_name="Kováč", street="Nová 2", postal_code="91701"),
            status="Na vyzdvihnutie",
            route="Sklad -> Trnava, Nová 2",
            assigned_courier_id="123456",
            delivery_date=date.today(),
            section="A2", rack="03", police="02", size="M", phone="0911 222 333", pin="1193",
        ),
        Shipment(
            id="ZP-20260414-0003",
            package=PackageDetails(size_x=10, size_y=10, size_z=5, weight=0.5, contents="Knihy"),
            sender=Address(first_name="Zippy", last_name="Sklad", street="Skladová 1", postal_code="91701"),
            recipient=Address(first_name="Dávid", last_name="Kováč", street="Stará 5", postal_code="91701"),
            status="Na vyzdvihnutie",
            route="Sklad -> Trnava, Stará 5",
            assigned_courier_id="123456",
            delivery_date=date.today(),
            section="C3", rack="07", police="01", size="S", phone="0944 555 777", pin="9021",
        ),
        Shipment(
            id="ZP-20260414-0004",
            package=PackageDetails(size_x=50, size_y=40, size_z=30, weight=8.0, contents="Spotrebič"),
            sender=Address(first_name="Zippy", last_name="Sklad", street="Skladová 1", postal_code="91701"),
            recipient=Address(first_name="Marta", last_name="Slobodová", street="Hlavná 5", postal_code="91701"),
            status="Na vyzdvihnutie",
            route="Sklad -> Trnava, Hlavná 5",
            assigned_courier_id="123456",
            delivery_date=date.today(),
            section="B1", rack="02", police="03", size="XL", phone="0902 888 111", pin="3344",
        ),
        Shipment(
            id="ZP-20260414-0005",
            package=PackageDetails(size_x=15, size_y=10, size_z=8, weight=0.8, contents="Kozmetika"),
            sender=Address(first_name="Zippy", last_name="Sklad", street="Skladová 1", postal_code="91701"),
            recipient=Address(first_name="Ján", last_name="Kováč", street="Stará 2", postal_code="91701"),
            status="Na vyzdvihnutie",
            route="Sklad -> Trnava, Stará 2",
            assigned_courier_id="123456",
            delivery_date=date.today(),
            section="B1", rack="01", police="05", size="S", phone="0901 123 456", pin="4783",
        ),
]

def _shipment_to_dict(s: Shipment) -> dict:
    """
    Konvertuje Shipment objekt na jednoduchý slovník (dict).
    Screeny pracujú s dictmi kvôli jednoduchosti — nevyžadujú
    importovanie modelu Shipment do každého screen súboru.
    """
    return {
        "id":        s.id,
        "address":   f"{s.recipient.street}",
        "recipient": f"{s.recipient.first_name} {s.recipient.last_name}",
        "phone":     s.phone,
        "status":    s.status,
        "section":   s.section,
        "rack":      s.rack,
        "police":    s.police,
        "size":      s.size,
        "pin":       s.pin,
    }

class UC04DeliveryService:
    """
    Hlavná servisná trieda pre use case UC04 – doručenie zásielky kuriérom.
    Zodpovedá za správu zásielok, stavu kuriéra a logiku doručenia.
    Všetky screeny UC04 pristupujú k dátam výhradne cez túto triedu.
    """

    def __init__(self):
        # Zoznam dnešných zásielok ako Shipment objekty
        self._shipments: list[Shipment] = _make_mock_shipments()
        # Počítadlo pokusov o doručenie pre každú zásielku (shipment_id -> počet)
        self._unavailable_counts: dict[str, int] = {}   # shipment_id -> attempts
        # Aktuálne prihlásený kuriér (None kým sa kuriér neprihlási)
        self._courier: Courier | None = None

    # ── Shipment list ─────────────────────────────────────────────────────────

    def get_today_shipments(self) -> list[dict]:
        """Vráti všetky dnešné zásielky ako zoznam dictov pre screeny."""
        return [_shipment_to_dict(s) for s in self._shipments]

    def get_shipment_by_id(self, shipment_id: str) -> dict | None:
        """Vráti jednu zásielku ako dict podľa ID, alebo None ak neexistuje."""
        s = self._get_obj_by_id(shipment_id)
        return _shipment_to_dict(s) if s else None

    def get_shipment_obj_by_id(self, shipment_id: str) -> Shipment | None:
        """
        Vráti priamy Shipment objekt podľa ID.
        Ak potrebujeme prístup
        k celému modelu, nie len k dict reprezentácii.
        """
        return self._get_obj_by_id(shipment_id)

    def get_all_shipment_objs(self) -> list[Shipment]:
        """
        Vráti všetky Shipment objekty.
        """
        return self._shipments

    def _get_obj_by_id(self, shipment_id: str) -> Shipment | None:
        """Interná pomocná metóda — nájde Shipment objekt podľa ID."""
        for s in self._shipments:
            if s.id == shipment_id:
                return s
        return None

    # ── Courier ───────────────────────────────────────────────────────────────

    def set_courier(self, courier_id: str, name: str) -> None:
        """
        Inicializuje kuriéra pri prihlásení.
        is_available sa nastaví na False — kuriér je aktívny a pracuje.
        current_load sa nastaví na celkový počet dnešných zásielok.
        """
        self._courier = Courier(
            id=courier_id,
            name=name,
            is_available=False,
            current_load=len(self._shipments),
        )

    def get_courier(self) -> Courier | None:
        """Vráti aktuálneho kuriéra, alebo None ak nie je prihlásený."""
        return self._courier

    # ── Pickup ────────────────────────────────────────────────────────────────

    def confirm_pickup(self, index: int) -> None:
        """
        Označí jednu zásielku ako vyzdvihnutú zo skladu.
        Volaná po každom kliknutí na 'Potvrdiť vyzdvihnutie' v pickup screene.
        Index zodpovedá poradiu zásielky v zozname _shipments.
        """
        self._shipments[index].status = "Vyzdvihnutá"

    def all_picked_up(self) -> None:
        """
        Označí všetky vyzdvihnuté zásielky ako 'Na ceste'.
        Volaná keď kuriér potvrdí vyzdvihnutie poslednej zásielky
        a prechádza na obrazovku trasy.
        Zásielky ktoré nie sú 'Vyzdvihnutá' sa nemenia
        (napr. ak bola nejaká preskočená).
        """
        for s in self._shipments:
            if s.status == "Vyzdvihnutá":
                s.status = "Na ceste"
        log.info("UC04: All picked up, %d shipments", len(self._shipments))

    # ── Delivery ──────────────────────────────────────────────────────────────

    def confirm_delivery_pin(self, shipment_id: str, pin: str) -> bool:
        """
        Overí PIN zadaný zákazníkom a označí zásielku ako doručenú.
        Vráti True ak PIN sedí, False ak nie.
        Po úspešnom doručení aktualizuje záťaž kuriéra.
        """
        s = self._get_obj_by_id(shipment_id)
        if s and s.pin == pin.strip():
            s.status = "Doručené"
            self._update_courier_load()
            log.info("UC04: %s delivered via PIN", shipment_id)
            return True
        log.warning("UC04: Wrong PIN for %s", shipment_id)
        return False

    def confirm_delivery_signature(self, shipment_id: str) -> None:
        """
        Označí zásielku ako doručenú na základe podpisu zákazníka.
        Podpis sa overuje vizuálne kuriérom, nie programovo.
        Po doručení aktualizuje záťaž kuriéra.
        """
        s = self._get_obj_by_id(shipment_id)
        if s:
            s.status = "Doručené"
            self._update_courier_load()
            log.info("UC04: %s delivered via signature", shipment_id)

    # ── Unavailable customer ──────────────────────────────────────────────────

    def get_unavailable_count(self, shipment_id: str) -> int:
        """
        Vráti počet neúspešných pokusov o doručenie pre danú zásielku.
        Používa sa pred navigáciou na unavailable screen aby sme vedeli
        či ide o prvý alebo opakovaný pokus — bez inkrementovania.
        """
        return self._unavailable_counts.get(shipment_id, 0)

    def mark_unavailable(self, shipment_id: str) -> int:
        """
        Inkrementuje počítadlo nedostupnosti a aktualizuje status zásielky.
        Volaná až keď kuriér klikne OK na unavailable screene (nie hneď
        po kliknutí 'Zákazník nedostupný') — zabraňuje náhodnému inkrementovaniu.

        Návratová hodnota:
          1 = prvý pokus → zásielka sa preplánovuje (status: Nedostupný)
          2+ = opakovaný pokus → zásielka sa vracia do skladu (status: Vrátenie)
        """
        count = self._unavailable_counts.get(shipment_id, 0) + 1
        self._unavailable_counts[shipment_id] = count
        s = self._get_obj_by_id(shipment_id)
        if s:
            s.status = "Nedostupný" if count == 1 else "Vrátenie"
            # Záťaž kuriéra sa znižuje až keď je zásielka definitívne vrátená
            if count >= 2:
                self._update_courier_load()
        log.info("UC04: %s unavailable (attempt %d)", shipment_id, count)
        return count

    # ── Route ─────────────────────────────────────────────────────────────────

    def get_route_stops(self) -> list[str]:
        """
        Vráti optimalizovaný zoznam zastávok pre dnešnú trasu.
        V reálnej aplikácii by poradie vypočítal server podľa GPS súradníc.
        """
        return MOCK_ROUTE_ORDER

    # ── Helper ────────────────────────────────────────────────────────────────

    def _update_courier_load(self) -> None:
        """
        Aktualizuje stav kuriéra po každom dokončenom doručení.
        current_load = počet zásielok ktoré ešte čakajú na doručenie.
        is_available sa nastaví na True keď nie sú žiadne pending zásielky
        — signalizuje ostatným use casom že kuriér je voľný.
        """
        if not self._courier:
            return
        pending = [s for s in self._shipments
                   if s.status not in ("Doručené", "Vrátenie")]
        self._courier.current_load = len(pending)
        self._courier.is_available = len(pending) == 0