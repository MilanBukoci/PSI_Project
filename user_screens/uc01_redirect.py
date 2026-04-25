from datetime import date
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from theme import Colors, RoundedButton, ZippyInput
from user_screens.base_screen import BaseScreen
from user_screens.home import HomeScreen


class _UC01PopupMixin:
    def _open_confirm_popup(self, title: str, message: str, on_confirm, confirm_text: str = "Potvrdiť"):
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
    """UC01 screen 1: vyhľadanie zásielky."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc01_redirect"

    def on_enter(self):
        super().on_enter()
        self.shipment_id_input.text = ""
        self.error_label.text = ""

    def build_content(self):
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
        shipment_id = self.shipment_id_input.text.strip().upper()
        shipment = self.app.shipment_service.get_redirect_shipment(shipment_id)
        if not shipment:
            self.error_label.text = "Zásielka nebola nájdená."
            return

        self.app.uc01_selected_id = shipment["id"]
        self.app.uc01_return_screen = "uc01_redirect"
        self.go_to("uc01_detail")


class UC01RedirectDetailScreen(BaseScreen, _UC01PopupMixin):
    """UC01 screen 2: detail zásielky + akcie zmeny."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc01_redirect"

    def on_enter(self):
        super().on_enter()
        self._refresh_data()

    def build_content(self):
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
            height=dp(24),
            halign="left",
        )
        self.error_label.bind(size=self.error_label.setter("text_size"))

        self.id_value = self._line_with_value("Číslo zásielky:")
        self.address_value, _ = self._line_with_action("Adresa doručenia:", self._on_edit_address)
        self.date_value, _ = self._line_with_action("Dátum doručenia:", self._on_edit_date)
        self.status_value = self._line_with_value("Stav zásielky:")
        self.payment_value, self.payment_btn = self._line_with_action(
            "Platba:",
            self._on_pay_surcharge,
            button_text="Zaplatiť",
        )

        ca.add_widget(self.error_label)
        ca.add_widget(Label(size_hint_y=1))

    def _line_with_value(self, title: str) -> Label:
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
        shipment_id = getattr(self.app, "uc01_selected_id", "")
        shipment = self.app.shipment_service.get_redirect_shipment(shipment_id)
        if not shipment:
            self.error_label.text = "Zásielka nebola nájdená."
            return

        self.current_shipment = shipment
        can_redirect, message = self.app.shipment_service.can_redirect_shipment(shipment)
        self.error_label.text = "" if can_redirect else message

        self.id_value.text = shipment["id"]
        self.address_value.text = f"{shipment['address']} ({shipment['postal_code']})"
        self.date_value.text = shipment["delivery_date"].strftime("%d.%m.%Y")
        self.status_value.text = shipment["status"]

        pending = shipment.get("pending_surcharge", 0.0)
        payment_status = shipment.get("payment_status", "nezaplatená")
        if payment_status != "zaplatená":
            if pending > 0:
                self.payment_value.text = f"nezaplatená ({pending:.2f} EUR)"
            else:
                self.payment_value.text = "nezaplatená"
            self.payment_btn.disabled = False
            self.payment_btn.opacity = 1
            self.payment_btn.size = (dp(74), dp(28))
        else:
            self.payment_value.text = payment_status
            self.payment_btn.disabled = True
            self.payment_btn.opacity = 0
            self.payment_btn.size = (0, dp(28))

    def _on_back(self, *_):
        target = getattr(self.app, "uc01_return_screen", "uc01_redirect")
        self.go_to(target, "right")

    def _on_edit_address(self, *_):
        can_redirect, message = self.app.shipment_service.can_redirect_shipment(self.current_shipment)
        if not can_redirect:
            self.error_label.text = message
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
        self._open_confirm_popup(
            "Potvrdenie",
            "Naozaj chcete zmeniť adresu doručenia?",
            on_confirm=lambda: self._apply_address_change(new_address, new_postal, surcharge_paid),
            confirm_text="Zmeniť",
        )

    def _apply_address_change(self, new_address: str, new_postal: str, surcharge_paid: bool):
        result = self.app.shipment_service.apply_redirect_address(
            shipment_id=self.current_shipment["id"],
            new_address=new_address,
            new_postal_code=new_postal,
            surcharge_paid=surcharge_paid,
        )
        if not result["ok"]:
            self.error_label.text = result["message"]
            return

        self._message_popup("Hotovo", "Zmena adresy úspešná")
        self._refresh_data()

    def _on_edit_date(self, *_):
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
            self._message_popup("Hotovo", "Zmena dátumu úspešná")
            self._refresh_data()

        btn.bind(on_release=submit)
        popup.open()

    def _on_pay_surcharge(self, *_):
        result = self.app.shipment_service.mark_redirect_payment_paid(self.current_shipment["id"])
        if not result["ok"]:
            self.error_label.text = result["message"]
            return

        self._message_popup("Platba", "Poplatok úspešne zaplatený")
        self._refresh_data()

HomeScreen.register_action("", "Presmerovať", "Moju zásielku", "uc01_redirect")