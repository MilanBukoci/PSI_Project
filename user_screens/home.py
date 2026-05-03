"""
user_screens/home.py – Domovská obrazovka zákazníka.

Zobrazuje tagline, mriežku rýchlych akcií a zoznam aktívnych zásielok.
Ostatné UC registrujú svoje karty cez HomeScreen.register_action().
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp

from user_screens.base_screen import BaseScreen
from theme import Colors, RoundedButton, make_label


class QuickActionCard(BoxLayout):
    def __init__(self, icon, title, subtitle, target=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8),
                         spacing=dp(2), **kwargs)
        self.target = target

        # Sivé zaoblené pozadie karty
        with self.canvas.before:
            Color(*Colors.MID_GRAY)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(10)])
        self.bind(pos=self._draw, size=self._draw)

        self._title_lbl = Label(
            text=title,
            font_size=dp(18),
            bold=True,
            color=Colors.DARK_TEXT,
            halign="center",
            valign="middle",
            size_hint=(1, 1),
        )
        self._title_lbl.bind(size=self._title_lbl.setter("text_size"))
        self.add_widget(self._title_lbl)

    def _draw(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size


class ShipmentRow(BoxLayout):
    def __init__(self, shipment_id, route, status, dot_color, on_tap=None, **kwargs):
        super().__init__(orientation="horizontal",
                         size_hint_y=None, height=dp(44),
                         padding=[dp(8), dp(4)], spacing=dp(8), **kwargs)
        self.shipment_id = shipment_id
        self._on_tap = on_tap

        # Svetlosivé pozadie riadku zásielky
        with self.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(8)])
        self.bind(pos=self._draw, size=self._draw)

        # Farebná bodka zodpovedá stavu zásielky
        dot = Label(text="o", font_size=dp(14),
                    color=dot_color, size_hint_x=None, width=dp(20))
        col = BoxLayout(orientation="vertical", spacing=dp(1))
        id_lbl = Label(text=shipment_id, font_size=dp(12),
                       color=Colors.MID_GRAY, halign="left")
        id_lbl.bind(size=id_lbl.setter("text_size"))
        route_lbl = Label(text=route, font_size=dp(15), bold=True,
                          color=Colors.DARK_TEXT, halign="left")
        route_lbl.bind(size=route_lbl.setter("text_size"))
        col.add_widget(id_lbl)
        col.add_widget(route_lbl)

        # Farebný odznak stavu (napr. „Na ceste", „Čaká")
        badge = Label(
            text=status,
            font_size=dp(10),
            color=Colors.WHITE,
            size_hint=(None, None),
            size=(dp(70), dp(22)),
        )
        with badge.canvas.before:
            Color(*dot_color)
            RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(6)])
        badge.bind(pos=lambda w, *_: self._redraw_badge(w),
                   size=lambda w, *_: self._redraw_badge(w))

        self.add_widget(dot)
        self.add_widget(col)
        self.add_widget(badge)
        self._badge = badge

    def _draw(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def _redraw_badge(self, w):
        # Farba odznaku závisí od textu stavu — zelená pre „Na ceste", inak oranžová
        w.canvas.before.clear()
        with w.canvas.before:
            Color(*Colors.SUCCESS_GRN if "Na ceste" in w.text else Colors.ORANGE)
            RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(8)])

    def on_touch_down(self, touch):
        # Kliknutie na riadok otvorí detail zásielky cez UC01
        if self.collide_point(*touch.pos) and self._on_tap:
            self._on_tap(self.shipment_id)
            return True
        return super().on_touch_down(touch)


class HomeScreen(BaseScreen):
    # ── Register rýchlych akcií ───────────────────────────────────────────────
    # Každé UC môže pridať svoju kartu cez register_action().
    # Formát: (icon, title, subtitle, target_screen_name)
    _actions: list[tuple] = [
        ("", "Odoslať balík", "Vytvoriť objednávku", "step1"),
        ("", "Sledovať", "Zadajte číslo", "uc01_redirect"),
        ("", "Naplánovať", "Vyzdvihnutie", None),
    ]

    def on_enter(self):
        super().on_enter()
        # Pri každom vstupe sa obsah prekreslí — zobrazí aktuálne zásielky
        self.content_area.clear_widgets()
        self.build_content()

    @classmethod
    def register_action(cls, icon: str, title: str, subtitle: str, target: str):
        """
        Registruje kartu rýchlej akcie do domovskej mriežky.
        Volá sa na úrovni modulu v súbore príslušného UC.
        Príklad:
            HomeScreen.register_action("", "Doručiť", "Zobraziť trasu", "uc04_deliver")
        """
        # Ochrana pred duplikátmi pri opätovnom načítaní modulu
        entry = (icon, title, subtitle, target)
        if entry not in cls._actions:
            cls._actions.append(entry)

    # ── Obrazovka ─────────────────────────────────────────────────────────────

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "home"

    def build_content(self):
        ca = self.content_area

        # Tagline v modrej farbe značky
        tagline = Label(
            text="[b][color=2b2bff]Kam dnes\nposielame balík?[/color][/b]",
            markup=True,
            font_size=dp(22),
            size_hint_y=None,
            height=dp(60),
            halign="left",
            valign="middle",
        )
        tagline.bind(size=tagline.setter("text_size"))
        ca.add_widget(tagline)

        # Mriežka rýchlych akcií — postavená z registra _actions
        grid = GridLayout(cols=2, spacing=dp(10),
                          size_hint_y=None, height=dp(130))
        for icon, title, subtitle, target in self._actions:
            card = QuickActionCard(icon, title, subtitle, target=target)
            card.bind(on_touch_down=self._on_card_touch)
            grid.add_widget(card)
        ca.add_widget(grid)

        # Nadpis sekcie aktívnych zásielok
        ca.add_widget(Label(
            text="Aktívne zásielky",
            font_size=dp(14), bold=True,
            color=Colors.DARK_TEXT,
            size_hint_y=None, height=dp(24),
            halign="left",
        ))

        # Scrollovateľný zoznam zásielok z ShipmentService
        scroll = ScrollView(size_hint_y=1)
        shipments_col = BoxLayout(orientation="vertical", spacing=dp(8),
                                  size_hint_y=None)
        shipments_col.bind(minimum_height=shipments_col.setter("height"))

        for s in self.app.shipment_service.get_active_shipments():
            shipments_col.add_widget(ShipmentRow(
                shipment_id=s["id"],
                route=s["route"],
                status=s["status"],
                dot_color=s["color"],
                on_tap=self._on_active_shipment_tap,
            ))

        scroll.add_widget(shipments_col)
        ca.add_widget(scroll)

    def _on_card_touch(self, card, touch):
        # Navigácia na cieľovú obrazovku po kliknutí na kartu
        if card.collide_point(*touch.pos) and card.target:
            self.go_to(card.target)

    def _on_active_shipment_tap(self, shipment_id: str):
        # Otvorí UC01 detail pre vybranú zásielku; uloží návratovú obrazovku
        shipment = self.app.shipment_service.get_redirect_shipment(shipment_id)
        if not shipment:
            return
        self.app.uc01_selected_id = shipment_id
        self.app.uc01_return_screen = "home"
        self.go_to("uc01_detail")