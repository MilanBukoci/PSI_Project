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
from user_screens.base_screen import CourierBaseScreen as BaseScreen, CourierBaseScreen


class SimpleMapWidget(Widget):
    """
    Vlastný widget pre zobrazenie mapy.
    Namiesto externej knižnice používa inštrukcie Canvasu na vykreslenie trasy.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Naviazanie (bind) prekresľovania na zmenu veľkosti alebo pozície widgetu.
        # Bez tohto by pri otočení displeja mapa zostala na starom mieste/v starom rozmere.
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        # Vyčistenie grafickej plochy pred každým prekreslením
        self.canvas.clear()
        with self.canvas:
            # Pozadie mapy
            Color(0.88, 0.92, 0.88, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Vykreslenie mriežky (simulácia ulíc)
            Color(1, 1, 1, 1)
            cols = 6
            rows = 5
            for i in range(1, cols):
                x = self.x + i * self.width / cols
                Line(points=[x, self.y, x, self.top], width=dp(1.5))
            for i in range(1, rows):
                y = self.y + i * self.height / rows
                Line(points=[self.x, y, self.right, y], width=dp(1.5))

            # Vykreslenie samotnej trasy (červená čiara)
            # Body sú počítané relatívne k rozmerom widgetu (0.0 až 1.0)
            Color(*Colors.ERROR_RED)
            pts = [
                self.x + self.width * 0.15, self.y + self.height * 0.2,
                self.x + self.width * 0.35, self.y + self.height * 0.55,
                self.x + self.width * 0.55, self.y + self.height * 0.35,
                self.x + self.width * 0.75, self.y + self.height * 0.7,
                self.x + self.width * 0.88, self.y + self.height * 0.5,
            ]
            Line(points=pts, width=dp(2.5))

            # Vykreslenie bodov (zastávok) na trase
            Color(*Colors.BLUE)
            dot_r = dp(7)
            for i in range(0, len(pts), 2):
                cx, cy = pts[i], pts[i + 1]
                # Ellipse s rovnakou šírkou a výškou vytvorí kruh
                Ellipse(pos=(cx - dot_r, cy - dot_r), size=(dot_r * 2, dot_r * 2))


class UC04RouteScreen(BaseScreen):
    """Obrazovka zobrazujúca optimalizovanú trasu a poradie zastávok."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def build_content(self):
        ca = self.content_area

        # Tlačidlo Späť s navigáciou na zoznam (animácia doprava)
        back_btn = RoundedButton(
            text="<< Späť",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
        )
        back_btn.bind(on_release=lambda *_: self.go_to("uc04_list", "right"))
        ca.add_widget(back_btn)

        ca.add_widget(Label(
            text="[b]Trasa[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(28),
            halign="left",
        ))

        # Pridanie nášho mapového widgetu s fixnou výškou 200dp
        map_widget = SimpleMapWidget(size_hint_y=None, height=dp(200))
        ca.add_widget(map_widget)

        ca.add_widget(Label(
            text="ZOZNAM ZASTÁVOK:",
            font_size=dp(12),
            bold=True,
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(22),
            halign="left",
        ))

        # Dynamické generovanie riadkov so zastávkami zo servisnej vrstvy
        svc = App.get_running_app().uc04_service
        stops_col = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        # Dôležité: minimum_height zabezpečí, že BoxLayout bude presne taký vysoký, koľko je v ňom zastávok
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
        # Prázdny label s size_hint_y=1 vytlačí obsah nahor a tlačidlo nadol
        ca.add_widget(Label(size_hint_y=1))

        next_btn = RoundedButton(
            text="Ďalej ->",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(48),
        )
        next_btn.bind(on_release=self._on_next)
        ca.add_widget(next_btn)

    def _on_next(self, *_):
        """Logika pre automatický výber ďalšej zásielky na doručenie."""
        app = App.get_running_app()
        shipments = app.uc04_service.get_today_shipments()

        # Filtrujeme zásielky, ktoré ešte čakajú na spracovanie
        pending = [s for s in shipments if s["status"] not in ("Doručené", "Vrátenie", "Nedostupný")]

        if pending:
            # Ak existujú čakajúce, vyberieme prvú v poradí a ideme na detail
            app.uc04_selected_id = pending[0]["id"]
            self.go_to("uc04_detail")
        else:
            # Ak nie sú čakajúce, skúsime tie, ktoré boli označené ako nedostupné (druhý pokus)
            pending_nedostupne = [s for s in shipments if s["status"] not in ("Doručené", "Vrátenie")]
            if pending_nedostupne:
                app.uc04_selected_id = pending_nedostupne[0]["id"]
                self.go_to("uc04_detail")
            else:
                # Ak je všetko vybavené, vrátime sa na zoznam
                self.go_to("uc04_list", "right")

# ─────────────────────────────────────────────────────────────────────────────
#  uc04_detail.py – Detail konkrétnej zásielky s akciami
# ─────────────────────────────────────────────────────────────────────────────

class UC04DetailScreen(BaseScreen):
    """Zobrazuje informácie o jednej zásielke a umožňuje kuriérovi vykonať akcie."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def on_enter(self):
        """Volá sa pri každom vstupe na obrazovku."""
        super().on_enter()
        # Vyčistíme a znova zostavíme obsah, aby sme mali istotu, že vidíme dáta správnej zásielky
        self.content_area.clear_widgets()
        self.build_content()

    def build_content(self):
        ca = self.content_area
        app = App.get_running_app()
        # Získanie ID vybranej zásielky z globálneho stavu aplikácie
        shipment_id = getattr(app, "uc04_selected_id", None)
        shipment = app.uc04_service.get_shipment_by_id(shipment_id) if shipment_id else None

        if not shipment:
            ca.add_widget(Label(text="Zásielka nenájdená.", color=Colors.ERROR_RED))
            return

        # Riadok pre tlačidlo Späť
        back_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))
        back_btn = RoundedButton(
            text="<< Späť",
            bg_color=Colors.MID_GRAY,
            size_hint=(None, None),
            size=(dp(90), dp(32)),
        )
        back_btn.bind(on_release=lambda *_: self.go_to("uc04_route", "right"))
        back_row.add_widget(back_btn)
        back_row.add_widget(Label())  # Spacer
        ca.add_widget(back_row)

        # Vizualizácia karty s informáciami pomocou BoxLayoutu a Canvasu
        info_card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            padding=[dp(12), dp(10)],
            spacing=dp(6),
        )
        with info_card.canvas.before:
            # Vykreslenie zaobleného pozadia pod kartou
            Color(*Colors.LIGHT_GRAY)
            self._info_bg = RoundedRectangle(pos=info_card.pos, size=info_card.size, radius=[dp(10)])

        # Prepojenie pozadia s rozmermi widgetu (aby sa hýbalo s ním)
        info_card.bind(pos=self._upd_info, size=self._upd_info)

        def lbl(text, bold=False, color=None):
            """Pomocná funkcia pre rýchle vytváranie labelov v karte."""
            l = Label(
                text=text,
                font_size=dp(13),
                bold=bold,
                color=color or Colors.DARK_TEXT,
                halign="left",
                size_hint_y=None,
                height=dp(20),
            )
            # Nastavenie text_size zabezpečí, že halign="left" bude fungovať správne
            l.bind(size=l.setter("text_size"))
            return l

        info_card.add_widget(lbl(f"ID: {shipment['id']}", bold=True))
        info_card.add_widget(lbl(f"Adresa: {shipment['address']}"))
        info_card.add_widget(lbl(f"Príjemca: {shipment['recipient']}"))
        info_card.add_widget(lbl(f"Telefón: {shipment['phone']}"))
        ca.add_widget(info_card)

        ca.add_widget(Label(size_hint_y=None, height=dp(12)))

        # Akčné tlačidlá pre kuriéra
        call_btn = RoundedButton(text="Zavolať zákazníkovi", bg_color=Colors.BLUE, size_hint_y=None, height=dp(48))
        call_btn.bind(on_release=lambda *_: self._on_call(shipment))
        ca.add_widget(call_btn)

        deliver_btn = RoundedButton(text="Potvrdiť doručenie", bg_color=Colors.SUCCESS_GRN, size_hint_y=None, height=dp(48))
        deliver_btn.bind(on_release=lambda *_: self._on_deliver(shipment))
        ca.add_widget(deliver_btn)

        unavail_btn = RoundedButton(text="Zákazník nedostupný", bg_color=Colors.ERROR_RED, size_hint_y=None, height=dp(48))
        unavail_btn.bind(on_release=lambda *_: self._on_unavailable(shipment))
        ca.add_widget(unavail_btn)

    def _upd_info(self, w, *_):
        """Aktualizuje grafické pozadie pri zmene okna."""
        self._info_bg.pos = w.pos
        self._info_bg.size = w.size

    def _on_deliver(self, shipment):
        """Prechod na obrazovku potvrdenia podpisu/prevzatia."""
        App.get_running_app().uc04_selected_id = shipment["id"]
        self.go_to("uc04_confirm")

    def _on_unavailable(self, shipment):
        """Logika pre riešenie nedostupnosti (rozlišuje prvý a druhý pokus)."""
        app = App.get_running_app()
        app.uc04_selected_id = shipment["id"]
        count = app.uc04_service.get_unavailable_count(shipment["id"])
        if count == 0:
            self.go_to("uc04_unavailable_1")  # Prvý pokus
        else:
            self.go_to("uc04_unavailable_2")  # Druhý pokus (vrátenie do skladu)


class UC04ShipmentInfoScreen(CourierBaseScreen):
    """Detailná informačná obrazovka so všetkými technickými údajmi o balíku."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "uc04_list"

    def on_enter(self):
        super().on_enter()
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

        back_btn = RoundedButton(text="<- Späť", bg_color=Colors.MID_GRAY, size_hint=(None, None), size=(dp(90), dp(32)))
        back_btn.bind(on_release=lambda *_: self.go_to("uc04_list", "right"))
        ca.add_widget(back_btn)

        ca.add_widget(Label(
            text=f"[b]Zásielka {shipment['id']}[/b]",
            markup=True,
            font_size=dp(16),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(28),
            halign="left",
        ))

        ca.add_widget(Label(size_hint_y=None, height=dp(8)))

        # Použitie ScrollView pre prípady, keď je dát viac než výška obrazovky
        scroll = ScrollView(size_hint_y=1)
        inner = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        # Dynamická výška podľa obsahu
        inner.bind(minimum_height=inner.setter("height"))

        # Pridávanie sekcií pomocou helper metódy pre čistotu kódu
        self._add_section(inner, "Príjemca", [
            ("Meno", shipment["recipient"]),
            ("Adresa", shipment["address"]),
            ("Telefón", shipment["phone"]),
        ])

        # Načítanie plného objektu zo servisnej vrstvy (obsahuje viac polí ako slovník v liste)
        obj = app.uc04_service.get_shipment_obj_by_id(shipment_id)
        if obj:
            self._add_section(inner, "Odosielateľ", [
                ("Meno", f"{obj.sender.first_name} {obj.sender.last_name}"),
                ("Adresa", f"{obj.sender.street}, {obj.sender.postal_code}"),
            ])

            self._add_section(inner, "Balík", [
                ("Obsah", obj.package.contents),
                ("Rozmery", f"{obj.package.size_x}x{obj.package.size_y}x{obj.package.size_z} cm"),
                ("Hmotnosť", f"{obj.package.weight} kg"),
                ("Veľkosť", shipment["size"]),
                ("Inštrukcie", obj.package.special_instructions or "—"),
            ])

            self._add_section(inner, "Sklad", [
                ("Sekcia", shipment["section"]),
                ("Regál", shipment["rack"]),
                ("Polica", shipment["police"]),
            ])

            self._add_section(inner, "Doručenie", [
                ("Status", shipment["status"]),
                ("Trasa", obj.route),
                ("Dátum", str(obj.delivery_date or "—")),
                ("Platba", obj.payment_method),
                ("Cena", f"{obj.price:.2f} €"),
            ])

        scroll.add_widget(inner)
        ca.add_widget(scroll)

    def _add_section(self, ca, title, rows):
        """
        Vytvorí vizuálny blok (sekciu) s nadpisom a dvojicami kľúč-hodnota.
        Zabezpečuje jednotný vzhľad informácií.
        """
        section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[dp(12), dp(10)],
            spacing=dp(4),
        )
        section.bind(minimum_height=section.setter("height"))

        # Kreslenie pozadia sekcie (svetlý RoundedRectangle)
        with section.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            bg = RoundedRectangle(pos=section.pos, size=section.size, radius=[dp(10)])

        # Zabezpečenie, aby pozadie sledovalo zmeny veľkosti sekcie
        section.bind(
            pos=lambda w, *_: setattr(bg, "pos", w.pos),
            size=lambda w, *_: setattr(bg, "size", w.size),
        )

        # Nadpis sekcie (napr. "Príjemca")
        title_lbl = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            font_size=dp(13),
            color=Colors.BLUE,
            halign="left",
            size_hint_y=None,
            height=dp(22),
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))
        section.add_widget(title_lbl)

        # Iteratívne pridávanie riadkov informácií (Kľúč: Hodnota)
        for key, val in rows:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
            k = Label(text=key, font_size=dp(12), color=Colors.MID_GRAY, halign="left", size_hint_x=0.4)
            k.bind(size=k.setter("text_size"))
            v = Label(text=str(val), font_size=dp(12), color=Colors.DARK_TEXT, halign="left", size_hint_x=0.6)
            v.bind(size=v.setter("text_size"))
            row.add_widget(k)
            row.add_widget(v)
            section.add_widget(row)

        ca.add_widget(section)
        ca.add_widget(Label(size_hint_y=None, height=dp(8)))  # Medzera medzi sekciami
