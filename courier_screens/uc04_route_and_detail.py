"""
screens/uc04_route.py – UC04 Step 3: Optimal route map + stop list.
screens/uc04_detail.py – UC04 Step 4: Single shipment detail + actions.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  uc04_route.py
# ─────────────────────────────────────────────────────────────────────────────

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.app import App
from kivy.uix.widget import Widget

from theme import Colors, RoundedButton
from user_screens.base_screen import BaseScreen


class SimpleMapWidget(Widget):
    """
    A placeholder map widget that draws a rough grid + route line.
    Replace with a real map library (e.g. kivy-garden.mapview) later.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.88, 0.92, 0.88, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Grid lines (streets)
            Color(1, 1, 1, 1)
            cols = 6
            rows = 5
            for i in range(1, cols):
                x = self.x + i * self.width / cols
                Line(points=[x, self.y, x, self.top], width=dp(1.5))
            for i in range(1, rows):
                y = self.y + i * self.height / rows
                Line(points=[self.x, y, self.right, y], width=dp(1.5))

            # Route line (mock path through stops)
            Color(*Colors.ERROR_RED)
            pts = [
                self.x + self.width * 0.15, self.y + self.height * 0.2,
                self.x + self.width * 0.35, self.y + self.height * 0.55,
                self.x + self.width * 0.55, self.y + self.height * 0.35,
                self.x + self.width * 0.75, self.y + self.height * 0.7,
                self.x + self.width * 0.88, self.y + self.height * 0.5,
            ]
            Line(points=pts, width=dp(2.5))

            # Stop markers
            Color(*Colors.BLUE)
            dot_r = dp(7)
            for i in range(0, len(pts), 2):
                cx, cy = pts[i], pts[i + 1]
                Ellipse(pos=(cx - dot_r, cy - dot_r), size=(dot_r * 2, dot_r * 2))


class UC04RouteScreen(BaseScreen):
    """Shows the optimised delivery route map and ordered stop list."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def build_content(self):
        ca = self.content_area

        ca.add_widget(Label(
            text="[b]Trasa[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(28),
            halign="left",
        ))

        # Map widget
        map_widget = SimpleMapWidget(size_hint_y=None, height=dp(200))
        ca.add_widget(map_widget)

        # Stop list label
        ca.add_widget(Label(
            text="ZOZNAM ZASTÁVOK:",
            font_size=dp(12),
            bold=True,
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(22),
            halign="left",
        ))

        svc = App.get_running_app().uc04_service
        stops_col = BoxLayout(orientation="vertical", spacing=dp(4),
                              size_hint_y=None)
        stops_col.bind(minimum_height=stops_col.setter("height"))

        for i, stop in enumerate(svc.get_route_stops(), start=1):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
            row.add_widget(Label(
                text=f"{i}.  {stop}",
                font_size=dp(13),
                color=Colors.DARK_TEXT,
                halign="left",
            ))
            stops_col.add_widget(row)

        ca.add_widget(stops_col)
        ca.add_widget(Label(size_hint_y=1))

        next_btn = RoundedButton(
            text="Ďalej →",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(48),
        )
        next_btn.bind(on_release=self._on_next)
        ca.add_widget(next_btn)

    def _on_next(self, *_):
        # Navigate to first undelivered shipment
        app = App.get_running_app()
        shipments = app.uc04_service.get_today_shipments()
        pending = [s for s in shipments if s["status"] not in ("Doručené", "Vrátenie")]
        if pending:
            app.uc04_selected_id = pending[0]["id"]
            self.go_to("uc04_detail")
        else:
            self.go_to("uc04_list", "right")


# ─────────────────────────────────────────────────────────────────────────────
#  uc04_detail.py  (in same file for brevity — split if preferred)
# ─────────────────────────────────────────────────────────────────────────────

class UC04DetailScreen(BaseScreen):
    """
    Shows full details of one shipment.
    Buttons: Zavolať zákazníkovi | Potvrdiť doručenie | Zákazník nedostupný
    """

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def on_enter(self):
        super().on_enter()
        # Rebuild content each time (shipment may have changed)
        self.content_area.clear_widgets()
        self.build_content()

    def build_content(self):
        ca = self.content_area
        app = App.get_running_app()
        shipment_id = getattr(app, "uc04_selected_id", None)
        shipment = app.uc04_service.get_shipment_by_id(shipment_id) if shipment_id else None

        if not shipment:
            ca.add_widget(Label(text="Zásielka nenájdená.", color=Colors.ERROR_RED))
            return

        # Back button row
        back_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))
        back_btn = RoundedButton(
            text="← Späť",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
        )
        back_btn.bind(on_release=lambda *_: self.go_to("uc04_route", "right"))
        back_row.add_widget(back_btn)
        back_row.add_widget(Label())  # spacer
        ca.add_widget(back_row)

        # Info card
        info_card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            padding=[dp(12), dp(10)],
            spacing=dp(6),
        )
        with info_card.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._info_bg = RoundedRectangle(pos=info_card.pos, size=info_card.size, radius=[dp(10)])
        info_card.bind(pos=self._upd_info, size=self._upd_info)

        def lbl(text, bold=False, color=None):
            l = Label(
                text=text,
                font_size=dp(13),
                bold=bold,
                color=color or Colors.DARK_TEXT,
                halign="left",
                size_hint_y=None,
                height=dp(20),
            )
            l.bind(size=l.setter("text_size"))
            return l

        info_card.add_widget(lbl(f"ID: {shipment['id']}", bold=True))
        info_card.add_widget(lbl(f"Adresa: {shipment['address']}"))
        info_card.add_widget(lbl(f"Príjemca: {shipment['recipient']}"))
        info_card.add_widget(lbl(f"Telefón: {shipment['phone']}"))
        ca.add_widget(info_card)

        ca.add_widget(Label(size_hint_y=None, height=dp(12)))

        # Action buttons
        call_btn = RoundedButton(
            text="📞  Zavolať zákazníkovi",
            bg_color=Colors.BLUE,
            size_hint_y=None,
            height=dp(48),
        )
        call_btn.bind(on_release=lambda *_: self._on_call(shipment))
        ca.add_widget(call_btn)

        deliver_btn = RoundedButton(
            text="✔  Potvrdiť doručenie",
            bg_color=Colors.SUCCESS_GRN,
            size_hint_y=None,
            height=dp(48),
        )
        deliver_btn.bind(on_release=lambda *_: self._on_deliver(shipment))
        ca.add_widget(deliver_btn)

        unavail_btn = RoundedButton(
            text="✖  Zákazník nedostupný",
            bg_color=Colors.ERROR_RED,
            size_hint_y=None,
            height=dp(48),
        )
        unavail_btn.bind(on_release=lambda *_: self._on_unavailable(shipment))
        ca.add_widget(unavail_btn)

    def _upd_info(self, w, *_):
        self._info_bg.pos = w.pos
        self._info_bg.size = w.size

    def _on_call(self, shipment):
        # In a real app: use Android/iOS tel: intent
        pass

    def _on_deliver(self, shipment):
        App.get_running_app().uc04_selected_id = shipment["id"]
        self.go_to("uc04_confirm")

    def _on_unavailable(self, shipment):
        app = App.get_running_app()
        count = app.uc04_service.mark_unavailable(shipment["id"])
        app.uc04_selected_id = shipment["id"]
        if count == 1:
            self.go_to("uc04_unavailable_1")
        else:
            self.go_to("uc04_unavailable_2")
