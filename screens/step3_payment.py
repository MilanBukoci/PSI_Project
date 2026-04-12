"""
screens/step3_payment.py – Step 3: Order summary + payment method selection.
Handles both the normal and payment-failed states.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.properties import StringProperty

from screens.base_screen import BaseScreen
from theme import Colors, StepIndicator, RoundedButton


PAYMENT_OPTIONS = [
    ("card",  "", "Platobná karta",  "Visa, Mastercard, Maestro"),
    ("gpay",  "G",  "Google Pay",      "Rýchla platba cez Google"),
    ("cash",  "", "Hotovosti",       "Kuriérovi"),
]


class PaymentOptionRow(BoxLayout):
    def __init__(self, key, icon, title, subtitle, selected=False, **kwargs):
        super().__init__(orientation="horizontal",
                         size_hint_y=None, height=dp(56),
                         padding=[dp(12), dp(6)], spacing=dp(10), **kwargs)
        self.key = key
        self._selected = selected
        self._draw_bg()
        self.bind(pos=lambda *_: self._draw_bg(),
                  size=lambda *_: self._draw_bg())

        # Radio circle
        self._radio = Label(
            text="●" if selected else "○",
            font_size=dp(16),
            color=Colors.DARK_TEXT,
            size_hint=(None, None),
            size=(dp(24), dp(40)),
        )

        # Icon
        icon_lbl = Label(text=icon, font_size=dp(18),
                         size_hint=(None, None), size=(dp(28), dp(40)))

        # Text
        text_col = BoxLayout(orientation="vertical", spacing=dp(1))
        t_lbl = Label(text=title, font_size=dp(13), bold=True,
                      color=Colors.DARK_TEXT, halign="left")
        t_lbl.bind(size=t_lbl.setter("text_size"))
        s_lbl = Label(text=subtitle, font_size=dp(11),
                      color=Colors.MID_GRAY, halign="left")
        s_lbl.bind(size=s_lbl.setter("text_size"))
        text_col.add_widget(t_lbl)
        text_col.add_widget(s_lbl)

        self.add_widget(self._radio)
        self.add_widget(icon_lbl)
        self.add_widget(text_col)

    def select(self):
        self._selected = True
        self._radio.text = "●"
        self._draw_bg()

    def deselect(self):
        self._selected = False
        self._radio.text = "○"
        self._draw_bg()

    def _draw_bg(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            if self._selected:
                Color(0.9, 0.9, 1.0, 1)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
                Color(*Colors.BLUE)
            else:
                Color(*Colors.LIGHT_GRAY)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])


class Step3PaymentScreen(BaseScreen):
    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "home"

    def build_content(self):
        ca = self.content_area
        ca.add_widget(StepIndicator(current_step=3,
                                    size_hint_y=None, height=dp(54)))

        scroll = ScrollView(size_hint_y=1)
        inner = BoxLayout(orientation="vertical", spacing=dp(8),
                          size_hint_y=None, padding=[0, dp(4)])
        inner.bind(minimum_height=inner.setter("height"))

        # Summary section
        inner.add_widget(self._bold_label("SÚHRN"))
        shipment = self.app.shipment_service.current_shipment
        for key, val in shipment.summary_lines():
            row = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(22))
            row.add_widget(Label(text=key, font_size=dp(13),
                                 color=Colors.MID_GRAY, halign="left"))
            row.add_widget(Label(text=val, font_size=dp(13),
                                 color=Colors.DARK_TEXT, halign="right"))
            inner.add_widget(row)

        # Total
        total_row = BoxLayout(orientation="horizontal",
                              size_hint_y=None, height=dp(28))
        total_row.add_widget(self._bold_label("SPOLU"))
        price_lbl = Label(text=f"{shipment.price:.2f} €",
                          font_size=dp(16), bold=True,
                          color=Colors.DARK_TEXT, halign="right")
        price_lbl.bind(size=price_lbl.setter("text_size"))
        total_row.add_widget(price_lbl)
        inner.add_widget(total_row)

        # Error banner (hidden by default)
        self._error_banner = self._make_error_banner()
        self._error_banner.opacity = 0
        inner.add_widget(self._error_banner)

        # Payment options
        inner.add_widget(self._bold_label("Spôsob platby"))
        self._option_rows = {}
        for key, icon, title, subtitle in PAYMENT_OPTIONS:
            row = PaymentOptionRow(key, icon, title, subtitle,
                                   selected=(key == "card"))
            row.bind(on_touch_down=self._on_option_touch)
            self._option_rows[key] = row
            inner.add_widget(row)

        scroll.add_widget(inner)
        ca.add_widget(scroll)
        ca.add_widget(self._nav_buttons())

    def _bold_label(self, text):
        lbl = Label(text=text, font_size=dp(14), bold=True,
                    color=Colors.DARK_TEXT,
                    size_hint_y=None, height=dp(22), halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _make_error_banner(self):
        banner = BoxLayout(orientation="horizontal",
                           size_hint_y=None, height=dp(40),
                           padding=[dp(10), dp(6)])
        with banner.canvas.before:
            Color(*Colors.ERROR_RED)
            self._banner_bg = RoundedRectangle(pos=banner.pos,
                                               size=banner.size,
                                               radius=[dp(8)])
        banner.bind(pos=self._upd_banner, size=self._upd_banner)
        lbl = Label(
            text="⚠  Platba zamietnutá. Skúste inú metódu\nalebo to zopakujte.",
            font_size=dp(12),
            color=Colors.WHITE,
            halign="left",
        )
        lbl.bind(size=lbl.setter("text_size"))
        banner.add_widget(lbl)
        return banner

    def _upd_banner(self, w, *_):
        self._banner_bg.pos  = w.pos
        self._banner_bg.size = w.size

    def _on_option_touch(self, widget, touch):
        if widget.collide_point(*touch.pos):
            for row in self._option_rows.values():
                row.deselect()
            widget.select()
            self.app.shipment_service.save_payment_method(widget.key)

    def _nav_buttons(self):
        row = BoxLayout(orientation="horizontal", spacing=dp(12),
                        size_hint_y=None, height=dp(48))
        back = RoundedButton(text="<- Späť", bg_color=Colors.MID_GRAY,
                             size_hint_x=0.4)
        back.bind(on_release=lambda *_: self.go_to("step2", "right"))

        self._next_btn = RoundedButton(text="Pokračovať ->",
                                       bg_color=Colors.ORANGE,
                                       size_hint_x=0.6)
        self._next_btn.bind(on_release=self._on_submit)
        row.add_widget(back)
        row.add_widget(self._next_btn)
        return row

    def _on_submit(self, *_):
        # Toggle simulate_failure=True to test the error banner
        success = self.app.shipment_service.submit_shipment(simulate_failure=False)

        if success:
            # Notify via socket stub
            shipment = self.app.shipment_service.current_shipment
            self.app.socket_service.submit_shipment({"shipment_id": shipment.id})
            self.go_to("step4")
        else:
            self._error_banner.opacity = 1
