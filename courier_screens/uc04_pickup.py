"""
screens/uc04_pickup.py – UC04 Step 2: Confirm warehouse pickup.
Courier sees package details (section/rack/police/size) and confirms.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App


from theme import Colors, RoundedButton
from user_screens.base_screen import CourierBaseScreen as BaseScreen


class InfoCard(BoxLayout):
    """A card showing one package's warehouse location."""

    def __init__(self, shipment: dict, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            padding=[dp(12), dp(10)],
            spacing=dp(4),
            **kwargs,
        )
        with self.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._draw, size=self._draw)

        # Header row: shipment ID + size badge
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        id_lbl = Label(
            text=shipment["id"],
            font_size=dp(12),
            bold=True,
            color=Colors.DARK_TEXT,
            halign="left",
        )
        id_lbl.bind(size=id_lbl.setter("text_size"))
        size_lbl = Label(
            text=f"Veľkosť: {shipment['size']}",
            font_size=dp(11),
            color=Colors.MID_GRAY,
            halign="right",
        )
        size_lbl.bind(size=size_lbl.setter("text_size"))
        header.add_widget(id_lbl)
        header.add_widget(size_lbl)
        self.add_widget(header)

        # Address + recipient
        addr = Label(
            text=f"{shipment['address']}  •  {shipment['recipient']}",
            font_size=dp(12),
            color=Colors.MID_GRAY,
            halign="left",
            size_hint_y=None,
            height=dp(18),
        )
        addr.bind(size=addr.setter("text_size"))
        self.add_widget(addr)

        # Warehouse location pills
        loc_row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint_y=None, height=dp(30))
        for label, value in [
            ("SEKCIA", shipment["section"]),
            ("REGÁL",  shipment["rack"]),
            ("POLICA", shipment["police"]),
        ]:
            pill = self._pill(f"{label}: {value}")
            loc_row.add_widget(pill)
        self.add_widget(loc_row)

    def _pill(self, text):
        lbl = Label(
            text=text,
            font_size=dp(11),
            bold=True,
            color=Colors.WHITE,
            size_hint=(None, None),
            size=(dp(90), dp(26)),
        )
        with lbl.canvas.before:
            Color(*Colors.BLUE)
            self._pill_bg = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[dp(6)])

        def redraw(w, *_):
            w.canvas.before.clear()
            with w.canvas.before:
                Color(*Colors.BLUE)
                RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(6)])

        lbl.bind(pos=redraw, size=redraw)
        return lbl

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class UC04PickupScreen(BaseScreen):
    """Courier confirms pickup of each package one at a time."""

    _current_index = 0

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def on_enter(self):
        super().on_enter()
        self._shipments = App.get_running_app().uc04_service.get_today_shipments()
        self._show_current()

    def build_content(self):
        pass  # built dynamically in _show_current()

    def _show_current(self):
        ca = self.content_area
        ca.clear_widgets()

        total = len(self._shipments)
        idx = self._current_index

        if idx >= total:
            # All picked up — confirm all and proceed to route
            App.get_running_app().uc04_service.all_picked_up()
            self.go_to("uc04_route")
            return

        shipment = self._shipments[idx]

        # Back button at the top
        back_btn = RoundedButton(
            text="<< Späť",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
        )
        back_btn.bind(on_release=self._on_back)
        ca.add_widget(back_btn)

        # Progress indicator e.g. "Zásielka 2 / 4"
        progress_lbl = Label(
            text=f"Zásielka {self._current_index + 1} / {total}",
            font_size=dp(13),
            color=Colors.MID_GRAY,
            size_hint_y=None,
            height=dp(22),
            halign="left",
        )
        progress_lbl.bind(size=progress_lbl.setter("text_size"))
        ca.add_widget(progress_lbl)

        ca.add_widget(Label(
            text="[b]Vyzdvihnutie zásielky[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(30),
            halign="left",
        ))

        ca.add_widget(Label(size_hint_y=None, height=dp(12)))
        ca.add_widget(InfoCard(shipment=shipment))
        ca.add_widget(Label(size_hint_y=1))

        confirm_btn = RoundedButton(
            text="Potvrdiť vyzdvihnutie",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(48),
        )
        confirm_btn.bind(on_release=self._on_confirm)
        ca.add_widget(confirm_btn)

    def _on_back(self, *_):
        self.go_to("uc04_list", "right")

    def _on_confirm(self, *_):
        App.get_running_app().uc04_service.confirm_pickup(self._current_index)
        self._current_index += 1
        self._show_current()