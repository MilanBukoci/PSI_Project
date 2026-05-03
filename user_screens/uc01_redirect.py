"""
Obrazovky UC01 – Presmerovanie zásielky používateľom.

Hlavný scenár: zadanie čísla zásielky, zobrazenie detailu, zmena adresy (vzdialenosť,
región, doplatok, notifikácie kuriér/dispečer) alebo alternatíva – zmena dátumu doručenia.
Logika stavov a výpočtov je v triede ShipmentService (súbor services/shipment_service.py).
"""
from datetime import date
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from theme import Colors, RoundedButton, ZippyInput
from user_screens.base_screen import BaseScreen
from user_screens.home import HomeScreen


class _UC01PopupMixin:
    """Spoločné okná pre potvrdenia a jednoduché správy v rámci UC01."""

    def _open_confirm_popup(self, title: str, message: str, on_confirm, confirm_text: str = "Potvrdiť"):
        """Dialóg Potvrdiť/Zrušiť pred zápisom zmeny (napr. potvrdenie zmeny adresy)."""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        lbl = Label(text=message, halign="center", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        content.add_widget(lbl)

        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(42))
        cancel_btn = RoundedButton(text="Zrušiť", bg_color=Colors.MID_GRAY)
        ok_btn = RoundedButton(text=confirm_text, bg_color=Colors.ORANGE)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(ok_btn)
        content.add_widget(btn_row)

        popup = Popup(title=title, content=content, size_hint=(0.88, 0.36), auto_dismiss=False)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())
        ok_btn.bind(on_release=lambda *_: self._confirm_and_close(popup, on_confirm))
        popup.open()

    @staticmethod
    def _confirm_and_close(popup: Popup, on_confirm):
        popup.dismiss()
        on_confirm()

    def _message_popup(self, title: str, message: str):
        """Informačné okno po úspechu alebo pri nutnosti najprv zaplatiť doplatok."""
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        lbl = Label(text=message, halign="center", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        content.add_widget(lbl)

        ok_btn = RoundedButton(text="OK", bg_color=Colors.ORANGE, size_hint_y=None, height=dp(42))
        content.add_widget(ok_btn)
        popup = Popup(title=title, content=content, size_hint=(0.88, 0.3), auto_dismiss=False)
        ok_btn.bind(on_release=popup.dismiss)
        popup.open()


class UC01RedirectScreen(BaseScreen):
    """
    UC01 – prvá obrazovka: zadanie čísla zásielky z potvrdenia objednávky.

    Po nájdení záznamu uloží výber do atribútu aplikácie uc01_selected_id a otvorí detail.
    """

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc01_redirect"

    def on_enter(self):
        super().on_enter()
        self.shipment_id_input.text = ""
        self.error_label.text = ""

    def build_content(self):
        """Zostavenie formulára na vyhľadanie zásielky podľa čísla zásielky."""
        ca = self.content_area
        ca.add_widget(Label(size_hint_y=None, height=dp(30)))
        main_lbl = Label(
            text="Zadajte číslo Vašej zásielky",
            font_size=dp(14),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(28),
            halign="center",
        )
        main_lbl.bind(size=main_lbl.setter("text_size"))
        ca.add_widget(main_lbl)
        self.shipment_id_input = ZippyInput(hint_text="napr. ZP-20260323-8841", size_hint_y=None, height=dp(42))
        ca.add_widget(self.shipment_id_input)

        show_btn = RoundedButton(
            text="Zobraziť podrobnosti",
            bg_color=Colors.MID_GRAY,
            size_hint_y=None,
            height=dp(40),
        )
        show_btn.bind(on_release=self._on_show_details)
        ca.add_widget(show_btn)

        self.error_label = Label(
            text="",
            font_size=dp(12),
            color=Colors.ERROR_RED,
            size_hint_y=None,
            height=dp(24),
            halign="center",
        )
        self.error_label.bind(size=self.error_label.setter("text_size"))
        ca.add_widget(self.error_label)
        ca.add_widget(Label(size_hint_y=1))

    def _on_show_details(self, *_):
        """Skontroluje vstup a presmeruje na obrazovku detailu zásielky, ak záznam existuje."""
        shipment_id = self.shipment_id_input.text.strip().upper()
        shipment = self.app.shipment_service.get_redirect_shipment(shipment_id)
        if not shipment:
            self.error_label.text = "Zásielka nebola nájdená."
            return

        self.app.uc01_selected_id = shipment["id"]
        self.app.uc01_return_screen = "uc01_redirect"
        self.go_to("uc01_detail")


class UC01RedirectDetailScreen(BaseScreen, _UC01PopupMixin):
    """
    UC01 – druhá obrazovka: zobrazenie údajov zásielky a tlačidlá „Zmeniť“ pri adrese a dátume.

    Pri stave „Na ceste“ sa akcie skryjú (zhoda s obmedzením zmeny počas doručovania).
    Pri doplatku za iný región sa najprv vyžaduje platba, potom zápis novej adresy cez službu zásielok.
    """

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc01_redirect"

    def on_enter(self):
        super().on_enter()
        # Po zaplatení doplatku: uložená nová adresa a PSČ, kým sa neuloží trvalá zmena v službe zásielok.
        self._pending_address_change: tuple[str, str] | None = None
        self._refresh_data()

    def build_content(self):
        """Hlavička s návratom, riadky údajov a sekcia platby."""
        ca = self.content_area

        back_btn = RoundedButton(
            text="<",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(36), dp(30)),
        )
        back_btn.bind(on_release=self._on_back)
        ca.add_widget(back_btn)

        self.error_label = Label(
            text="",
            font_size=dp(12),
            color=Colors.ERROR_RED,
            size_hint_y=None,
            height=dp(44),
            halign="center",
            valign="middle",
        )
        self.error_label.bind(size=lambda inst, _: setattr(inst, "text_size", (inst.width, None)))

        self.id_value = self._line_with_value("Číslo zásielky:")
        self.address_value, self.address_btn = self._line_with_action("Adresa doručenia:", self._on_edit_address)
        self.date_value, self.date_btn = self._line_with_action("Dátum doručenia:", self._on_edit_date)
        self.status_value = self._line_with_value("Stav zásielky:")
        self.payment_value, self.payment_btn = self._line_with_action(
            "Platba:",
            self._on_pay_surcharge,
            button_text="Zaplatiť",
        )

        ca.add_widget(Label(size_hint_y=1))
        ca.add_widget(self.error_label)

    def _line_with_value(self, title: str) -> Label:
        """Jeden riadok UI: popisok + hodnota."""
        row = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_y=None, height=dp(48))
        title_lbl = Label(text=title, font_size=dp(12), color=Colors.DARK_TEXT, halign="left", size_hint_y=None, height=dp(18))
        title_lbl.bind(size=title_lbl.setter("text_size"))
        value = Label(text="-", font_size=dp(12), color=Colors.MID_GRAY, halign="left", size_hint_y=None, height=dp(24))
        value.bind(size=value.setter("text_size"))
        row.add_widget(title_lbl)
        row.add_widget(value)
        self.content_area.add_widget(row)
        return value

    def _line_with_action(self, title: str, on_press, button_text: str = "Zmeniť") -> tuple[Label, RoundedButton]:
        """Riadok s tlačidlom (napr. „Zmeniť“ pri adrese alebo dátume podľa UC01)."""
        row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))
        left = BoxLayout(orientation="vertical", spacing=dp(2))
        title_lbl = Label(text=title, font_size=dp(12), color=Colors.DARK_TEXT, halign="left", size_hint_y=None, height=dp(18))
        title_lbl.bind(size=title_lbl.setter("text_size"))
        value = Label(text="-", font_size=dp(12), color=Colors.MID_GRAY, halign="left", size_hint_y=None, height=dp(24))
        value.bind(size=value.setter("text_size"))
        left.add_widget(title_lbl)
        left.add_widget(value)

        btn = RoundedButton(text=button_text, bg_color=Colors.MID_GRAY, size_hint=(None, None), size=(dp(74), dp(28)))
        btn.bind(on_release=on_press)
        row.add_widget(left)
        row.add_widget(btn)
        self.content_area.add_widget(row)
        return value, btn

    def _refresh_data(self):
        """Načíta zásielku zo služby, zobrazí stav a podľa pravidiel presmerovania a stavu „Na ceste“ zobrazí alebo skryje akcie."""
        shipment_id = getattr(self.app, "uc01_selected_id", "")
        shipment = self.app.shipment_service.get_redirect_shipment(shipment_id)
        if not shipment:
            self.error_label.text = "Zásielka nebola nájdená."
            return

        self.current_shipment = shipment
        can_redirect, message = self.app.shipment_service.can_redirect_shipment(shipment)
        self.error_label.text = "" if can_redirect else message
        # „Na ceste“ – v UI sa berie ako obdoba „už sa nedá meniť“.
        in_transit = shipment.get("status", "").strip().lower() == "na ceste"

        self.id_value.text = shipment["id"]
        self.address_value.text = f"{shipment['address']} ({shipment['postal_code']})"
        self.date_value.text = shipment["delivery_date"].strftime("%d.%m.%Y")
        self.status_value.text = shipment["status"]
        if in_transit:
            self.address_btn.disabled = True
            self.address_btn.opacity = 0
            self.address_btn.size = (0, dp(28))
            self.date_btn.disabled = True
            self.date_btn.opacity = 0
            self.date_btn.size = (0, dp(28))
        else:
            self.address_btn.disabled = False
            self.address_btn.opacity = 1
            self.address_btn.size = (dp(74), dp(28))
            self.date_btn.disabled = False
            self.date_btn.opacity = 1
            self.date_btn.size = (dp(74), dp(28))

        pending = shipment.get("pending_surcharge", 0.0)
        amount_due = shipment.get("amount_due", 0.0)
        payment_status = shipment.get("payment_status", "nezaplatená")
        if payment_status != "zaplatená":
            payable_amount = float(pending) if pending > 0 else float(amount_due)
            self.payment_value.text = f"nezaplatená ({payable_amount:.2f} EUR)"
            self.payment_btn.disabled = False
            self.payment_btn.opacity = 1
            self.payment_btn.size = (dp(74), dp(28))
        else:
            self.payment_value.text = payment_status
            self.payment_btn.disabled = True
            self.payment_btn.opacity = 0
            self.payment_btn.size = (0, dp(28))

    def _on_back(self, *_):
        """Návrat na obrazovku uloženú pri otvorení detailu (domov alebo vyhľadávanie zásielky)."""
        target = getattr(self.app, "uc01_return_screen", "uc01_redirect")
        self.go_to(target, "right")

    def _on_edit_address(self, *_):
        """
        Hlavný scenár zmeny adresy: dialóg, vyhodnotenie vzdialenosti a regiónu v službe,
        prípadne doplatok a potvrdenie.

        Ak je doplatok kladný, uloží novú adresu dočasne a používateľ musí najprv zaplatiť.
        """
        can_redirect, message = self.app.shipment_service.can_redirect_shipment(self.current_shipment)
        if not can_redirect:
            self.error_label.text = message
            return
        if self.current_shipment.get("status") == "Doručuje sa":
            self.error_label.text = "Zásielka je práve doručovaná, adresu už nie je možné zmeniť."
            return

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        addr_input = ZippyInput(hint_text="Nová adresa")
        psc_input = ZippyInput(hint_text="Nové PSČ")
        content.add_widget(Label(text="Zadajte novú adresu", size_hint_y=None, height=dp(20)))
        content.add_widget(addr_input)
        content.add_widget(psc_input)

        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(40))
        cancel_btn = RoundedButton(text="Zrušiť", bg_color=Colors.MID_GRAY, size_hint_x=0.45)
        btn = RoundedButton(text="Zmeniť", bg_color=Colors.BLUE, size_hint_x=0.55)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(btn)
        content.add_widget(btn_row)
        popup = Popup(title="Zmena adresy", content=content, size_hint=(0.88, 0.38), auto_dismiss=False)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())

        def submit(*_):
            new_address = addr_input.text.strip()
            new_postal = psc_input.text.strip()
            if not new_address or not new_postal:
                popup.dismiss()
                self.error_label.text = "Zadajte novú adresu aj PSČ."
                return

            evaluation = self.app.shipment_service.evaluate_redirect_address(self.current_shipment, new_postal)
            if not evaluation.get("ok"):
                popup.dismiss()
                self.error_label.text = evaluation.get("reason", "Adresa nie je dostupná.")
                return

            surcharge = evaluation["surcharge"]
            self.app.shipment_service.prepare_redirect_surcharge(self.current_shipment["id"], surcharge)
            popup.dismiss()
            if surcharge > 0:
                self._pending_address_change = (new_address, new_postal)
                self._message_popup(
                    "Vyžaduje sa platba",
                    f"Nová vzdialenosť: {evaluation['distance_km']} km\n"
                    f"Poplatok: {surcharge:.2f} EUR\n"
                    "Najprv kliknite na tlačidlo Zaplatiť.",
                )
                self._refresh_data()
                return

            self._confirm_address_change(new_address, new_postal, surcharge_paid=True)

        btn.bind(on_release=submit)
        popup.open()

    def _confirm_address_change(self, new_address: str, new_postal: str, surcharge_paid: bool):
        """Medzikrok: explicitné potvrdenie zmeny adresy pred volaním služby."""
        self._open_confirm_popup(
            "Potvrdenie",
            "Naozaj chcete zmeniť adresu doručenia?",
            on_confirm=lambda: self._apply_address_change(new_address, new_postal, surcharge_paid),
            confirm_text="Zmeniť",
        )

    def _apply_address_change(self, new_address: str, new_postal: str, surcharge_paid: bool):
        """Zápis adresy cez službu zásielok a odoslanie upozornení kuriérovi alebo dispečerovi."""
        result = self.app.shipment_service.apply_redirect_address(
            shipment_id=self.current_shipment["id"],
            new_address=new_address,
            new_postal_code=new_postal,
            surcharge_paid=surcharge_paid,
        )
        if not result["ok"]:
            self.error_label.text = result["message"]
            return

        for role in result.get("notify_roles", ["customer"]):
            if role == "customer":
                msg = f"Upozornenie: Zásielka {self.current_shipment['id']} – adresa doručenia bola úspešne zmenená."
            elif role == "dispatcher":
                # Upozornenie pre dispečing (interný identifikátor roly v notifikačnej službe).
                msg = (
                    f"Upozornenie: Zásielka {self.current_shipment['id']} – adresa doručenia bola zmenená "
                    "a bol vygenerovaný doplatok, je potrebné preplánovanie."
                )
            else:
                msg = f"Upozornenie: Zásielka {self.current_shipment['id']} – adresa doručenia bola zmenená."
            self.app.notification_service.push(role, msg)

        self._message_popup("Hotovo", "Zmena adresy úspešná")
        self._refresh_data()

    def _on_edit_date(self, *_):
        """Alternatívny scenár UC01: zmena dátumu (validácia v službe, notifikácia kuriérovi)."""
        can_redirect, message = self.app.shipment_service.can_redirect_shipment(self.current_shipment)
        if not can_redirect:
            self.error_label.text = message
            return
        if self.current_shipment.get("status") == "Doručuje sa":
            self.error_label.text = "Zásielka je práve doručovaná, dátum už nie je možné zmeniť."
            return

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        date_input = ZippyInput(hint_text="YYYY-MM-DD")
        content.add_widget(Label(text="Zadajte nový dátum", size_hint_y=None, height=dp(20)))
        content.add_widget(date_input)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(40))
        cancel_btn = RoundedButton(text="Zrušiť", bg_color=Colors.MID_GRAY, size_hint_x=0.45)
        btn = RoundedButton(text="Zmeniť", bg_color=Colors.BLUE, size_hint_x=0.55)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(btn)
        content.add_widget(btn_row)
        popup = Popup(title="Zmena dátumu", content=content, size_hint=(0.85, 0.3), auto_dismiss=False)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())

        def submit(*_):
            try:
                new_date = date.fromisoformat(date_input.text.strip())
            except ValueError:
                popup.dismiss()
                self.error_label.text = "Dátum musí byť vo formáte YYYY-MM-DD."
                return

            result = self.app.shipment_service.apply_delivery_date_change(self.current_shipment["id"], new_date)
            if not result["ok"]:
                popup.dismiss()
                self.error_label.text = result["message"]
                return

            popup.dismiss()
            for role in result.get("notify_roles", ["customer", "courier"]):
                if role == "customer":
                    msg = f"Upozornenie: Zásielka {self.current_shipment['id']} – dátum doručenia bol úspešne zmenený."
                else:
                    msg = f"Upozornenie: Zásielka {self.current_shipment['id']} – bol zmenený dátum doručenia."
                self.app.notification_service.push(role, msg)
            self._message_popup("Hotovo", "Zmena dátumu úspešná")
            self._refresh_data()

        btn.bind(on_release=submit)
        popup.open()

    def _on_pay_surcharge(self, *_):
        """Úhrada doplatku; ak je po platbe pripravená zmena adresy, dokončí sa zápis v jednom kroku."""
        result = self.app.shipment_service.mark_redirect_payment_paid(self.current_shipment["id"])
        if not result["ok"]:
            self.error_label.text = result["message"]
            return

        if self._pending_address_change:
            new_address, new_postal = self._pending_address_change
            self._pending_address_change = None
            self._apply_address_change(new_address, new_postal, surcharge_paid=True)
            return

        self._message_popup("Platba", "Poplatok úspešne zaplatený")
        self._refresh_data()

# Registrácia karty na domovskej obrazovke.
HomeScreen.register_action("", "Presmerovať", "Moju zásielku", "uc01_redirect")