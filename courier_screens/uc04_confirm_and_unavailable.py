"""
screens/uc04_confirm_delivery.py – PIN / signature confirmation screens.
screens/uc04_unavailable.py     – Customer unavailable (1st and 2nd miss).
"""

# ─────────────────────────────────────────────────────────────────────────────
#  uc04_confirm_delivery.py
# ─────────────────────────────────────────────────────────────────────────────

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App


from theme import Colors, RoundedButton, ZippyInput
from user_screens.base_screen import CourierBaseScreen as BaseScreen


class UC04ConfirmDeliveryScreen(BaseScreen):
    """
    Courier confirms delivery via PIN or signature.
    Two sub-modes toggled by buttons at the top.
    """

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def on_enter(self):
        super().on_enter()
        self._pin_input.text = ""
        self._pin_error.text = ""
        self._sig_input.text = ""

    def build_content(self):
        ca = self.content_area

        # Back button at the top
        back_btn = RoundedButton(
            text="<< Späť",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
        )
        back_btn.bind(on_release=lambda *_: self.go_to("uc04_detail", "right"))
        ca.add_widget(back_btn)  # spacer

        ca.add_widget(Label(
            text="[b]Potvrdenie prevzatia[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(30),
            halign="left",
        ))

        ca.add_widget(Label(size_hint_y=None, height=dp(8)))

        # ── PIN section ───────────────────────────────────────────────────────
        pin_section = BoxLayout(orientation="vertical", spacing=dp(8),
                                size_hint_y=None, height=dp(120))
        pin_section.bind(minimum_height=pin_section.setter("height"))

        pin_label = Label(
            text="PIN:",
            font_size=dp(14),
            bold=True,
            color=Colors.DARK_TEXT,
            halign="left",
            size_hint_y=None,
            height=dp(22),
        )
        pin_label.bind(size=pin_label.setter("text_size"))
        pin_section.add_widget(pin_label)

        self._pin_input = ZippyInput(
            hint_text="Zadajte PIN",
            input_filter="int",
            password=False,
        )
        pin_section.add_widget(self._pin_input)

        self._pin_error = Label(
            text="",
            font_size=dp(12),
            color=Colors.ERROR_RED,
            size_hint_y=None,
            height=dp(20),
        )
        pin_section.add_widget(self._pin_error)

        pin_confirm_btn = RoundedButton(
            text="Potvrdiť",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(44),
        )
        pin_confirm_btn.bind(on_release=self._on_pin_confirm)
        pin_section.add_widget(pin_confirm_btn)
        ca.add_widget(pin_section)

        # Divider
        ca.add_widget(Label(
            text="── alebo ──",
            font_size=dp(12),
            color=Colors.MID_GRAY,
            size_hint_y=None,
            height=dp(24),
        ))

        # ── Signature section ─────────────────────────────────────────────────
        sig_section = BoxLayout(orientation="vertical", spacing=dp(8),
                                size_hint_y=None, height=dp(120))
        sig_section.bind(minimum_height=sig_section.setter("height"))

        sig_label = Label(
            text="Podpis:",
            font_size=dp(14),
            bold=True,
            color=Colors.DARK_TEXT,
            halign="left",
            size_hint_y=None,
            height=dp(22),
        )
        sig_label.bind(size=sig_label.setter("text_size"))
        sig_section.add_widget(sig_label)

        # Signature input box (multiline text as placeholder for real canvas)
        self._sig_input = TextInput(
            hint_text="Podpíšte sa tu...",
            multiline=True,
            background_color=Colors.LIGHT_GRAY,
            foreground_color=Colors.DARK_TEXT,
            font_size=dp(13),
            size_hint_y=None,
            height=dp(60),
            padding=[dp(10), dp(8)],
        )
        sig_section.add_widget(self._sig_input)

        sig_confirm_btn = RoundedButton(
            text="Potvrdenie podpisom",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(44),
        )
        sig_confirm_btn.bind(on_release=self._on_sig_confirm)
        sig_section.add_widget(sig_confirm_btn)
        ca.add_widget(sig_section)

    def _on_pin_confirm(self, *_):
        app = App.get_running_app()
        pin = self._pin_input.text.strip()
        ok = app.uc04_service.confirm_delivery_pin(app.uc04_selected_id, pin)
        if ok:
            self._pin_error.text = ""
            self._go_next()
        else:
            self._pin_error.text = "Nesprávny PIN. Skúste znova."

    def _on_sig_confirm(self, *_):
        app = App.get_running_app()
        app.uc04_service.confirm_delivery_signature(app.uc04_selected_id)
        self._go_next()

    def _go_next(self):
        """After successful delivery, go to next pending shipment or uc04_list."""
        app = App.get_running_app()
        shipments = app.uc04_service.get_today_shipments()
        pending = [s for s in shipments if s["status"] not in ("Doručené", "Vrátenie", "Nedostupný")]
        if pending:
            app.uc04_selected_id = pending[0]["id"]
            self.go_to("uc04_detail")
        else:
            self.go_to("uc04_list", "right")


# ─────────────────────────────────────────────────────────────────────────────
#  uc04_unavailable.py
# ─────────────────────────────────────────────────────────────────────────────

class UC04Unavailable1Screen(BaseScreen):
    """First missed delivery — rescheduled."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def build_content(self):
        ca = self.content_area

        # Back button
        back_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))
        back_btn = RoundedButton(
            text="<< Späť",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
        )
        back_btn.bind(on_release=lambda *_: self.go_to("uc04_detail", "right"))
        back_row.add_widget(back_btn)
        back_row.add_widget(Label())
        ca.add_widget(back_row)

        ca.add_widget(Label(
            text="[b]Zákazník nedostupný[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(30),
        ))

        ca.add_widget(Label(size_hint_y=1))

        info_card = self._info_card(
            "Zákazník bol prvýkrát nedostupný.\nJeho doručenie bolo prepánované."
        )
        ca.add_widget(info_card)

        ca.add_widget(Label(size_hint_y=1))

        ok_btn = RoundedButton(
            text="OK",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(48),
        )
        ok_btn.bind(on_release=self._on_ok)
        ca.add_widget(ok_btn)

    def _info_card(self, message):
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(80),
            padding=[dp(16), dp(12)],
        )
        with card.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._card_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
        card.bind(
            pos=lambda w, *_: setattr(self._card_bg, "pos", w.pos),
            size=lambda w, *_: setattr(self._card_bg, "size", w.size),
        )
        lbl = Label(
            text=message,
            font_size=dp(13),
            color=Colors.DARK_TEXT,
            halign="center",
            valign="middle",
        )
        lbl.bind(size=lbl.setter("text_size"))
        card.add_widget(lbl)
        return card

    def _on_ok(self, *_):
        app = App.get_running_app()
        app.uc04_service.mark_unavailable(app.uc04_selected_id)
        shipments = app.uc04_service.get_today_shipments()
        pending = [s for s in shipments if s["status"] not in ("Doručené", "Vrátenie", "Nedostupný")]
        if pending:
            app.uc04_selected_id = pending[0]["id"]
            self.go_to("uc04_detail")
        else:
            self.go_to("uc04_route")


class UC04Unavailable2Screen(BaseScreen):
    """Second missed delivery — package must be returned to depot."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def build_content(self):
        ca = self.content_area

        back_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))
        back_btn = RoundedButton(
            text="<< Späť",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
        )
        back_btn.bind(on_release=lambda *_: self.go_to("uc04_detail", "right"))
        back_row.add_widget(back_btn)
        back_row.add_widget(Label())
        ca.add_widget(back_row)

        ca.add_widget(Label(
            text="[b]Zákazník nedostupný[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(30),
        ))

        ca.add_widget(Label(size_hint_y=1))

        info_card = self._info_card(
            "Zákazník bol nedostupný\nviackrát.\nJeho zásielku bude\npotrebné vrátiť do skladu."
        )
        ca.add_widget(info_card)

        ca.add_widget(Label(size_hint_y=1))

        ok_btn = RoundedButton(
            text="OK",
            bg_color=Colors.ERROR_RED,
            size_hint_y=None,
            height=dp(48),
        )
        ok_btn.bind(on_release=lambda *_: self._on_ok())
        ca.add_widget(ok_btn)

    def _on_ok(self, *_):
        app = App.get_running_app()
        app.uc04_service.mark_unavailable(app.uc04_selected_id)
        shipments = app.uc04_service.get_today_shipments()
        pending = [s for s in shipments if s["status"] not in ("Doručené", "Vrátenie")]
        if pending:
            self.go_to("uc04_route")
        else:
            self.go_to("uc04_list")

    def _info_card(self, message):
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(110),
            padding=[dp(16), dp(12)],
        )
        with card.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._card_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
        card.bind(
            pos=lambda w, *_: setattr(self._card_bg, "pos", w.pos),
            size=lambda w, *_: setattr(self._card_bg, "size", w.size),
        )
        lbl = Label(
            text=message,
            font_size=dp(13),
            color=Colors.DARK_TEXT,
            halign="center",
            valign="middle",
        )
        lbl.bind(size=lbl.setter("text_size"))
        card.add_widget(lbl)
        return card
