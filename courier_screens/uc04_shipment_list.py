"""
screens/uc04_shipment_list.py – UC04 Step 1: Today's shipments list.

Flow: uc04_list → uc04_pickup → uc04_route → uc04_detail
                                                  ↓
                                         uc04_confirm_delivery
                                         uc04_unavailable_1
                                         uc04_unavailable_2
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App

from theme import Colors, RoundedButton
from user_screens.base_screen import BaseScreen


class ShipmentListRow(BoxLayout):
    """One row in the today's shipments list."""

    def __init__(self, shipment: dict, on_tap=None, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(80),
            padding=[dp(12), dp(8)],
            spacing=dp(2),
            **kwargs,
        )
        self._shipment = shipment
        self._on_tap = on_tap

        with self.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._draw, size=self._draw)

        # Row 1: ID + status badge
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        id_lbl = Label(
            text=shipment["id"],
            font_size=dp(11),
            color=Colors.MID_GRAY,
            halign="left",
        )
        id_lbl.bind(size=id_lbl.setter("text_size"))

        badge = Label(
            text=shipment["status"],
            font_size=dp(10),
            color=Colors.WHITE,
            size_hint=(None, None),
            size=(dp(100), dp(20)),
        )
        with badge.canvas.before:
            Color(*Colors.ORANGE)
            self._badge_bg = RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(6)])
        badge.bind(pos=self._redraw_badge, size=self._redraw_badge)
        self._badge = badge

        top_row.add_widget(id_lbl)
        top_row.add_widget(badge)
        self.add_widget(top_row)

        # Row 2: address
        addr_lbl = Label(
            text=shipment["address"],
            font_size=dp(14),
            bold=True,
            color=Colors.DARK_TEXT,
            halign="left",
            size_hint_y=None,
            height=dp(22),
        )
        addr_lbl.bind(size=addr_lbl.setter("text_size"))
        self.add_widget(addr_lbl)

        # Row 3: recipient
        recip_lbl = Label(
            text=f"Príjemca: {shipment['recipient']}",
            font_size=dp(12),
            color=Colors.MID_GRAY,
            halign="left",
            size_hint_y=None,
            height=dp(18),
        )
        recip_lbl.bind(size=recip_lbl.setter("text_size"))
        self.add_widget(recip_lbl)

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _redraw_badge(self, w, *_):
        status = self._shipment["status"]
        if status == "Doručené":
            color = Colors.SUCCESS_GRN
        elif status in ("Vrátenie", "Nedostupný"):
            color = Colors.ERROR_RED
        else:
            color = Colors.ORANGE
        w.canvas.before.clear()
        with w.canvas.before:
            Color(*color)
            RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(6)])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self._on_tap:
            self._on_tap(self._shipment)
            return True
        return super().on_touch_down(touch)


class UC04ShipmentListScreen(BaseScreen):
    """Shows today's assigned shipments and a 'Ďalej' button."""

    def on_enter(self):
        super().on_enter()
        # Rebuild list every time so statuses are up to date
        self.content_area.clear_widgets()
        self.build_content()

    def header_title(self):
        return "ZIPPY"

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def build_content(self):
        ca = self.content_area

        ca.add_widget(Label(
            text="[b]Dnešné zásielky[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(30),
            halign="left",
        ))

        scroll = ScrollView(size_hint_y=1)
        col = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
        )
        col.bind(minimum_height=col.setter("height"))

        svc = App.get_running_app().uc04_service
        for s in svc.get_today_shipments():
            row = ShipmentListRow(
                shipment=s,
                on_tap=self._on_shipment_tap,
            )
            col.add_widget(row)

        scroll.add_widget(col)
        ca.add_widget(scroll)

        next_btn = RoundedButton(
            text="Ďalej →",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(48),
        )
        next_btn.bind(on_release=lambda *_: self.go_to("uc04_pickup"))
        ca.add_widget(next_btn)

    def _on_shipment_tap(self, shipment: dict):
        """Tapping a row navigates to shipment detail."""
        app = App.get_running_app()
        app.uc04_selected_id = shipment["id"]
        self.go_to("uc04_detail")
