"""
user_screens/step4_confirm.py – Krok 4: Potvrdenie objednávky (UC03).
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp

from user_screens.base_screen import BaseScreen
from theme import Colors, StepIndicator, RoundedButton


class Step4ConfirmScreen(BaseScreen):
    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "home"

    def build_content(self):
        ca = self.content_area
        ca.add_widget(StepIndicator(current_step=4,
                                    size_hint_y=None, height=dp(54)))

        ca.add_widget(Label(size_hint_y=None, height=dp(20)))

        # Zelený kruh s potvrdením úspešnej objednávky
        check_wrap = BoxLayout(size_hint_y=None, height=dp(90))
        check_lbl = Label(
            text="OK",
            font_size=dp(44),
            color=Colors.WHITE,
            bold=True,
        )
        with check_lbl.canvas.before:
            Color(*Colors.SUCCESS_GRN)
            self._check_bg = Ellipse(pos=check_lbl.pos, size=check_lbl.size)
        check_lbl.bind(pos=self._upd_check, size=self._upd_check)
        check_wrap.add_widget(check_lbl)
        ca.add_widget(check_wrap)

        ca.add_widget(Label(
            text="[b]Objednávka vytvorená[/b]",
            markup=True,
            font_size=dp(20),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(34),
        ))

        ca.add_widget(Label(
            text="Platba bola úspešne spracovaná.",
            font_size=dp(13),
            color=Colors.MID_GRAY,
            size_hint_y=None,
            height=dp(22),
        ))

        # Odznak s číslom objednávky
        shipment = self.app.shipment_service.current_shipment
        id_box = BoxLayout(size_hint_y=None, height=dp(36),
                           padding=[dp(60), dp(4)])
        id_lbl = Label(
            text=shipment.id,
            font_size=dp(13),
            bold=True,
            color=Colors.DARK_TEXT,
        )
        with id_lbl.canvas.before:
            Color(*Colors.LIGHT_GRAY)
            self._id_bg = RoundedRectangle(pos=id_lbl.pos,
                                           size=id_lbl.size,
                                           radius=[dp(6)])
        id_lbl.bind(pos=self._upd_id, size=self._upd_id)
        id_box.add_widget(id_lbl)
        ca.add_widget(id_box)

        ca.add_widget(Label(
            text="Potvrdenie sme odoslali na váš email.\nKuriér prevezme balík do 24 hodín.",
            font_size=dp(13),
            color=Colors.DARK_TEXT,
            halign="center",
            size_hint_y=None,
            height=dp(50),
        ))

        ca.add_widget(Label(size_hint_y=1))

        # Tlačidlo návratu na domovskú obrazovku
        home_btn = RoundedButton(
            text="Domov",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(48),
        )
        home_btn.bind(on_release=lambda *_: self.go_to("home", "right"))
        ca.add_widget(home_btn)

    def _upd_check(self, w, *_):
        self._check_bg.pos  = w.pos
        self._check_bg.size = w.size

    def _upd_id(self, w, *_):
        self._id_bg.pos  = w.pos
        self._id_bg.size = w.size

    def on_enter(self):
        super().on_enter()
        # Prihlásenie na odber aktualizácií stavu zásielky cez socket stub
        shipment = self.app.shipment_service.current_shipment
        self.app.socket_service.subscribe_shipment_status(
            shipment.id,
            self._on_status_update,
        )

    def _on_status_update(self, data):
        """Zavolané pri push notifikácii o zmene stavu zo servera (stub)."""
        pass