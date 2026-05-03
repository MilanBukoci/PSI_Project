"""
UC02 – Pridelenie zásielky kuriérovi (workflow dispečera v Kivy).

Tok obrazoviek naväzuje na seba a stav drží App (vid. main.ZippyApp):
  1. Zoznam zásielok – výber jednej alebo viacerých pending zásielok, voliteľný filter.
  2. Výber kuriéra – karty so stavom; aj nedostupní ostávajú klikateľní → chybu vráti
     až servis po Potvrď (ukáže validácie ako v scenári).
  3. Potvrdenie – sumár, volanie UC02DispatcherService.assign_shipments, zobrazenie výsledku
     vrátane náhľadu „notifikácie“ kuriérovi pri úspechu.

Pri každom on_enter sa content prekresľuje zo service (žiadny samostatný cache v screene).
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.app import App

from theme import Colors, RoundedButton, ZippyLabel
from user_screens.base_screen import CourierBaseScreen as BaseScreen


# ═════════════════════════════════════════════════════════════════════════════
#  1. SHIPMENT LIST SCREEN
# ═════════════════════════════════════════════════════════════════════════════

class _ShipmentCheckRow(BoxLayout):
    """Jeden riadok v scroll liste: checkbox iba ak status pending (pridelené len čítajú info)."""

    def __init__(self, shipment: dict, on_check=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(82),
            padding=[dp(8), dp(6)],
            spacing=dp(8),
            **kwargs,
        )
        self._shipment = shipment
        self._on_check = on_check
        is_unassigned = shipment["status"] == "pending"

        # Background
        with self.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                         radius=[dp(10)])
        self.bind(pos=self._draw, size=self._draw)

        # Stĺpec výberu: pending → skutočný CheckBox; inak spacer kvôli zarovnaniu šírok.
        if is_unassigned:
            cb_box = BoxLayout(size_hint_x=None, width=dp(36))
            self.cb = CheckBox(
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                pos_hint={"center_y": 0.5},
                color=Colors.ORANGE,
            )
            self.cb.bind(active=lambda inst, val: self._toggle(val))
            cb_box.add_widget(self.cb)
            self.add_widget(cb_box)
        else:
            self.cb = None
            spacer = Widget(size_hint_x=None, width=dp(36))
            self.add_widget(spacer)

        # Info column
        info = BoxLayout(orientation="vertical", spacing=dp(2))

        # Row 1: ID + badge
        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        id_lbl = Label(text=shipment["id"], font_size=dp(11),
                       color=Colors.MID_GRAY, halign="left")
        id_lbl.bind(size=id_lbl.setter("text_size"))

        badge_text = "Nepridelená" if is_unassigned else "Pridelená"
        badge_color = Colors.ORANGE if is_unassigned else Colors.SUCCESS_GRN
        badge = Label(text=badge_text, font_size=dp(10), color=Colors.WHITE,
                      size_hint=(None, None), size=(dp(90), dp(18)))
        with badge.canvas.before:
            Color(*badge_color)
            self._badge_bg = RoundedRectangle(pos=badge.pos, size=badge.size,
                                               radius=[dp(5)])
        badge.bind(
            pos=lambda w, *_: setattr(self._badge_bg, "pos", w.pos),
            size=lambda w, *_: setattr(self._badge_bg, "size", w.size),
        )

        top.add_widget(id_lbl)
        top.add_widget(badge)
        info.add_widget(top)

        # Row 2: route
        route_lbl = Label(text=shipment["route"], font_size=dp(13), bold=True,
                          color=Colors.DARK_TEXT, halign="left",
                          size_hint_y=None, height=dp(20))
        route_lbl.bind(size=route_lbl.setter("text_size"))
        info.add_widget(route_lbl)

        # Row 3: recipient + weight
        bottom_text = f"Príjemca: {shipment['recipient']}  •  {shipment['weight']} kg"
        bot_lbl = Label(text=bottom_text, font_size=dp(11),
                        color=Colors.MID_GRAY, halign="left",
                        size_hint_y=None, height=dp(16))
        bot_lbl.bind(size=bot_lbl.setter("text_size"))
        info.add_widget(bot_lbl)

        self.add_widget(info)

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _toggle(self, is_active):
        if self._on_check:
            self._on_check(self._shipment["id"], is_active)


class UC02ShipmentListScreen(BaseScreen):
    """Krok 1 UC02: prehľad zásielok, výber id do množiny, navigácia na výber kuriéra."""

    def __init__(self, **kwargs):
        self._filter_unassigned = False
        self._selected_ids: set = set()
        super().__init__(**kwargs)

    def on_enter(self):
        super().on_enter()
        self._selected_ids.clear()  # pri návrate z ďalších krokov začať bez „visiacich“ výberov
        self.content_area.clear_widgets()
        self.build_content()

    def header_subtitle(self):
        return "DISPEČER – Správa zásielok"

    def build_content(self):
        ca = self.content_area

        # Title
        ca.add_widget(Label(
            text="[b]Správa zásielok[/b]", markup=True,
            font_size=dp(18), color=Colors.DARK_TEXT,
            size_hint_y=None, height=dp(30), halign="left",
        ))

        # Prepínač „všetky“ vs „len nepridelené“ — pri zmene sa resetuje výber (jednoduchší model).
        filter_row = BoxLayout(orientation="horizontal",
                               size_hint_y=None, height=dp(36),
                               spacing=dp(8))

        self._filter_btn = RoundedButton(
            text="Len nepridelené" if not self._filter_unassigned
                 else "Všetky zásielky",
            bg_color=Colors.BLUE,
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(34),
        )
        self._filter_btn.font_size = dp(12)
        self._filter_btn.bind(on_release=lambda *_: self._toggle_filter())

        count_svc = App.get_running_app().uc02_service
        unassigned_count = len(count_svc.get_unassigned_shipments())
        count_lbl = Label(
            text=f"Nepridelených: {unassigned_count}",
            font_size=dp(12), color=Colors.ORANGE, bold=True,
            size_hint_x=0.5, halign="right",
        )
        count_lbl.bind(size=count_lbl.setter("text_size"))

        filter_row.add_widget(self._filter_btn)
        filter_row.add_widget(count_lbl)
        ca.add_widget(filter_row)

        # Shipment list
        scroll = ScrollView(size_hint_y=1)
        col = BoxLayout(orientation="vertical", spacing=dp(8),
                        size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))

        svc = App.get_running_app().uc02_service
        shipments = (svc.get_unassigned_shipments() if self._filter_unassigned
                     else svc.get_all_shipments())

        for s in shipments:
            row = _ShipmentCheckRow(shipment=s, on_check=self._on_check)
            col.add_widget(row)

        scroll.add_widget(col)
        ca.add_widget(scroll)

        # Aktívna farba iba ak je niečo zaškrtnuté; text ukazuje počet vybratých ID.
        self._assign_btn = RoundedButton(
            text="Prideliť kuriérovi",
            bg_color=Colors.MID_GRAY,
            size_hint_y=None,
            height=dp(48),
        )
        self._assign_btn.bind(on_release=lambda *_: self._on_assign())
        ca.add_widget(self._assign_btn)

        # Logout
        logout = RoundedButton(
            text="Odhlásiť sa",
            bg_color=Colors.ERROR_RED,
            size_hint_y=None, height=dp(44),
        )
        logout.bind(on_release=lambda *_: self.go_to("login", "right"))
        ca.add_widget(logout)

    def _on_check(self, shipment_id: str, is_active: bool):
        if is_active:
            self._selected_ids.add(shipment_id)
        else:
            self._selected_ids.discard(shipment_id)
        # Update button colour
        has_selected = len(self._selected_ids) > 0
        self._assign_btn.set_bg(Colors.ORANGE if has_selected else Colors.MID_GRAY)
        sel_text = (f"Prideliť kuriérovi ({len(self._selected_ids)})"
                    if has_selected else "Prideliť kuriérovi")
        self._assign_btn.text = sel_text

    def _toggle_filter(self):
        self._filter_unassigned = not self._filter_unassigned
        self._selected_ids.clear()
        self.content_area.clear_widgets()
        self.build_content()

    def _on_assign(self):
        if not self._selected_ids:
            return
        app = App.get_running_app()
        app.uc02_selected_shipments = list(self._selected_ids)  # zdieľaný stav ďalších obrazoviek UC02
        self.go_to("uc02_courier_select")


# ═════════════════════════════════════════════════════════════════════════════
#  2. COURIER SELECT SCREEN
# ═════════════════════════════════════════════════════════════════════════════

class _CourierCard(BoxLayout):
    """Karta kuriéra: meno, stav práce/kapacity, vizuál vyťaženia, tlačidlo Vybrať."""

    def __init__(self, courier: dict, on_select=None, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(100),
            padding=[dp(12), dp(8)],
            spacing=dp(6),
            **kwargs,
        )
        self._courier = courier
        self._on_select = on_select
        available = courier["is_available"]
        is_full = courier["is_full"]

        # Nedostupní vizuálne splývajú — logika blokovania ostáva v servise pri potvrdení.
        bg_color = (0.85, 0.85, 0.85, 1) if not available else Colors.LIGHT_GRAY
        with self.canvas.before:
            Color(*bg_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                         radius=[dp(10)])
        self.bind(pos=self._draw, size=self._draw)

        # Row 1: name + availability badge
        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        name_lbl = Label(
            text=courier["name"],
            font_size=dp(15), bold=True,
            color=Colors.MID_GRAY if not available else Colors.DARK_TEXT,
            halign="left",
        )
        name_lbl.bind(size=name_lbl.setter("text_size"))

        if not available:
            status_text = "Nie je v práci"
            status_color = Colors.MID_GRAY
        elif is_full:
            status_text = "Plne vyťažený"
            status_color = Colors.ERROR_RED
        else:
            status_text = "Dostupný"
            status_color = Colors.SUCCESS_GRN

        badge = Label(text=status_text, font_size=dp(10), color=Colors.WHITE,
                      size_hint=(None, None), size=(dp(100), dp(18)))
        with badge.canvas.before:
            Color(*status_color)
            self._sbg = RoundedRectangle(pos=badge.pos, size=badge.size,
                                          radius=[dp(5)])
        badge.bind(
            pos=lambda w, *_: setattr(self._sbg, "pos", w.pos),
            size=lambda w, *_: setattr(self._sbg, "size", w.size),
        )

        top.add_widget(name_lbl)
        top.add_widget(badge)
        self.add_widget(top)

        # Row 2: load label
        load_text = f"Vyťaženosť: {courier['current_load']}/{courier['max_load']}"
        load_lbl = Label(text=load_text, font_size=dp(12),
                         color=Colors.MID_GRAY if not available else Colors.DARK_TEXT,
                         halign="left", size_hint_y=None, height=dp(16))
        load_lbl.bind(size=load_lbl.setter("text_size"))
        self.add_widget(load_lbl)

        # Row 3: progress bar
        bar_container = BoxLayout(size_hint_y=None, height=dp(14),
                                  padding=[0, dp(2)])
        bar_bg = Widget(size_hint_x=1)

        def draw_bar(w, *_):
            w.canvas.clear()
            ratio = courier["current_load"] / max(courier["max_load"], 1)
            ratio = min(ratio, 1.0)
            with w.canvas:
                # Background track
                Color(0.8, 0.8, 0.8, 1)
                RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(4)])
                # Fill
                if ratio > 0:
                    fill_color = (
                        Colors.ERROR_RED if ratio >= 1.0
                        else Colors.ORANGE if ratio > 0.7
                        else Colors.SUCCESS_GRN
                    )
                    Color(*fill_color)
                    RoundedRectangle(
                        pos=w.pos,
                        size=(w.width * ratio, w.height),
                        radius=[dp(4)],
                    )

        bar_bg.bind(pos=draw_bar, size=draw_bar)
        bar_container.add_widget(bar_bg)
        self.add_widget(bar_container)

        # Vždy „Vybrať“: používateľ môže doručiť nevhodného kuriéra na krok Potvrď a tam dostať jasnú hlášku.
        if not available:
            btn_color = Colors.MID_GRAY
            btn_text = "Vybrať (nie je v práci)"
        elif is_full:
            btn_color = Colors.ERROR_RED
            btn_text = "Vybrať (plne vyťažený)"
        else:
            btn_color = Colors.BLUE
            btn_text = "Vybrať"

        btn = RoundedButton(
            text=btn_text,
            bg_color=btn_color,
            size_hint_y=None,
            height=dp(32),
        )
        btn.font_size = dp(13)
        btn.bind(on_release=lambda *_: self._select())
        self.add_widget(btn)
        self.height = dp(130)

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _select(self):
        if self._on_select:
            self._on_select(self._courier)


class UC02CourierSelectScreen(BaseScreen):
    """Krok 2 UC02: zápis vybraného courier_id do App a prechod na sumár."""

    def on_enter(self):
        super().on_enter()
        self.content_area.clear_widgets()
        self.build_content()

    def header_subtitle(self):
        return "DISPEČER – Výber kuriéra"

    def build_content(self):
        ca = self.content_area
        app = App.get_running_app()

        count = len(app.uc02_selected_shipments)

        # Title
        ca.add_widget(Label(
            text=f"[b]Vybrané zásielky: {count}[/b]", markup=True,
            font_size=dp(16), color=Colors.DARK_TEXT,
            size_hint_y=None, height=dp(28), halign="left",
        ))

        ca.add_widget(Label(
            text="Vyberte kuriéra pre pridelenie:",
            font_size=dp(13), color=Colors.MID_GRAY,
            size_hint_y=None, height=dp(20), halign="left",
        ))

        # Courier list
        scroll = ScrollView(size_hint_y=1)
        col = BoxLayout(orientation="vertical", spacing=dp(10),
                        size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))

        svc = app.uc02_service
        for c in svc.get_couriers():
            card = _CourierCard(courier=c, on_select=self._on_courier_select)
            col.add_widget(card)

        scroll.add_widget(col)
        ca.add_widget(scroll)

        # Back button
        back = RoundedButton(
            text="Späť",
            bg_color=Colors.MID_GRAY,
            size_hint_y=None, height=dp(44),
        )
        back.bind(on_release=lambda *_: self.go_to("uc02_shipment_list", "right"))
        ca.add_widget(back)

    def _on_courier_select(self, courier: dict):
        app = App.get_running_app()
        app.uc02_selected_courier_id = courier["id"]
        self.go_to("uc02_confirm")


# ═════════════════════════════════════════════════════════════════════════════
#  3. CONFIRM ASSIGNMENT SCREEN
# ═════════════════════════════════════════════════════════════════════════════

class UC02ConfirmScreen(BaseScreen):
    """Krok 3 UC02: sumár výberov, jediné miesto kde sa volí assign_shipments na servise."""

    def on_enter(self):
        super().on_enter()
        self.content_area.clear_widgets()
        self.build_content()

    def header_subtitle(self):
        return "DISPEČER – Potvrdenie pridelenia"

    def build_content(self):
        ca = self.content_area
        app = App.get_running_app()
        svc = app.uc02_service

        # Title
        ca.add_widget(Label(
            text="[b]Potvrdenie pridelenia[/b]", markup=True,
            font_size=dp(18), color=Colors.DARK_TEXT,
            size_hint_y=None, height=dp(30), halign="left",
        ))

        # Zobrazí len položky, ktorých id sú stále v app.uc02_selected_shipments (plochý join so zoznamom zo servisu).
        ca.add_widget(Label(
            text="Vybrané zásielky:", font_size=dp(14), bold=True,
            color=Colors.BLUE, size_hint_y=None, height=dp(22), halign="left",
        ))

        shipment_ids = getattr(app, "uc02_selected_shipments", [])
        all_shipments = svc.get_all_shipments()
        for s in all_shipments:
            if s["id"] in shipment_ids:
                row = BoxLayout(orientation="horizontal",
                                size_hint_y=None, height=dp(38),
                                padding=[dp(8), dp(4)], spacing=dp(4))
                with row.canvas.before:
                    Color(*Colors.LIGHT_GRAY)
                    _rbg = RoundedRectangle(pos=row.pos, size=row.size,
                                             radius=[dp(6)])
                row.bind(
                    pos=lambda w, _, bg=_rbg: setattr(bg, "pos", w.pos),
                    size=lambda w, _, bg=_rbg: setattr(bg, "size", w.size),
                )

                id_lbl = Label(text=s["id"], font_size=dp(11),
                               color=Colors.MID_GRAY, halign="left",
                               size_hint_x=0.4)
                id_lbl.bind(size=id_lbl.setter("text_size"))

                route_lbl = Label(text=s["route"], font_size=dp(12),
                                  bold=True, color=Colors.DARK_TEXT,
                                  halign="left", size_hint_x=0.6)
                route_lbl.bind(size=route_lbl.setter("text_size"))

                row.add_widget(id_lbl)
                row.add_widget(route_lbl)
                ca.add_widget(row)

        # Kuriér podľa zapamätaného id; ak chýba, blok sa vynechá (edge case prázdnej relácie).
        ca.add_widget(Widget(size_hint_y=None, height=dp(10)))
        ca.add_widget(Label(
            text="Vybraný kuriér:", font_size=dp(14), bold=True,
            color=Colors.BLUE, size_hint_y=None, height=dp(22), halign="left",
        ))

        courier_id = getattr(app, "uc02_selected_courier_id", None)
        couriers = svc.get_couriers()
        courier_data = next((c for c in couriers if c["id"] == courier_id), None)

        if courier_data:
            c_row = BoxLayout(orientation="horizontal",
                              size_hint_y=None, height=dp(40),
                              padding=[dp(8), dp(4)])
            with c_row.canvas.before:
                Color(*Colors.LIGHT_GRAY)
                _cbg = RoundedRectangle(pos=c_row.pos, size=c_row.size,
                                         radius=[dp(6)])
            c_row.bind(
                pos=lambda w, _, bg=_cbg: setattr(bg, "pos", w.pos),
                size=lambda w, _, bg=_cbg: setattr(bg, "size", w.size),
            )

            name_lbl = Label(
                text=courier_data["name"], font_size=dp(14), bold=True,
                color=Colors.DARK_TEXT, halign="left", size_hint_x=0.6,
            )
            name_lbl.bind(size=name_lbl.setter("text_size"))

            load_lbl = Label(
                text=f"{courier_data['current_load']}/{courier_data['max_load']}",
                font_size=dp(12), color=Colors.MID_GRAY,
                halign="right", size_hint_x=0.4,
            )
            load_lbl.bind(size=load_lbl.setter("text_size"))

            c_row.add_widget(name_lbl)
            c_row.add_widget(load_lbl)
            ca.add_widget(c_row)

        # Po pokuse o pridelenie sa tu zobrazí buď úspešná správa, alebo slovenský text z result["message"].
        self._status_label = Label(
            text="", font_size=dp(13), color=Colors.DARK_TEXT,
            size_hint_y=None, height=dp(50),
            halign="center", valign="middle",
            text_size=(dp(350), None),
        )
        ca.add_widget(self._status_label)

        # Po úspechu sa rozšíri o náhľad kuriérskej „push“ správy (rovnaký obsah ako v servise).
        self._notif_box = BoxLayout(orientation="vertical",
                                    size_hint_y=None, height=0)
        ca.add_widget(self._notif_box)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(10),
                            size_hint_y=None, height=dp(48))

        back_btn = RoundedButton(
            text="Späť",
            bg_color=Colors.MID_GRAY,
            size_hint_x=0.4,
        )
        back_btn.bind(on_release=lambda *_: self.go_to("uc02_courier_select", "right"))

        self._confirm_btn = RoundedButton(
            text="Potvrdiť pridelenie",
            bg_color=Colors.ORANGE,
            size_hint_x=0.6,
        )
        self._confirm_btn.bind(on_release=lambda *_: self._on_confirm())

        btn_row.add_widget(back_btn)
        btn_row.add_widget(self._confirm_btn)
        ca.add_widget(btn_row)

    def _on_confirm(self):
        app = App.get_running_app()
        svc = app.uc02_service

        result = svc.assign_shipments(
            shipment_ids=app.uc02_selected_shipments,
            courier_id=app.uc02_selected_courier_id,
        )

        if result["ok"]:
            self._status_label.color = Colors.SUCCESS_GRN
            self._status_label.text = result["message"]

            # Mock UI zhodný s textom, ktorý servis uložil do histórie kuriéra.
            self._notif_box.clear_widgets()
            self._notif_box.height = dp(70)

            notif_lbl = Label(
                text=f"[b]Notifikácia kuriérovi:[/b]\n{result.get('courier_notification', '')}",
                markup=True, font_size=dp(12),
                color=Colors.BLUE,
                halign="center", valign="middle",
                size_hint_y=None, height=dp(50),
                text_size=(dp(350), None),
            )
            self._notif_box.add_widget(notif_lbl)

            # Pôvodné potvrdenie už nedáva zmysel; tlačidlo slúži na návrat do zoznamu zásielok.
            self._confirm_btn.text = "Hotovo"
            self._confirm_btn.set_bg(Colors.SUCCESS_GRN)
            self._confirm_btn.unbind(on_release=lambda *_: None)
            self._confirm_btn.bind(
                on_release=lambda *_: self.go_to("uc02_shipment_list", "right")
            )
        else:
            self._status_label.color = Colors.ERROR_RED
            self._status_label.text = result["message"]
