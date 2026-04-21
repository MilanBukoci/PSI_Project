"""
user_screens/base_screen.py – Base class all Zippy user_screens inherit from.
"""
from kivy.graphics.svg import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App

from services.login_auth import AuthService
from theme import Colors, RoundedButton, BottomNav, ZippyInput, ZippyLabel


class LoginScreen(Screen):
    HEADER_HEIGHT = dp(80)
    NAV_HEIGHT    = dp(60)
    FAB_SIZE      = dp(52)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._root = FloatLayout()
        self.add_widget(self._root)

        self._main = BoxLayout(orientation="vertical",
                               size_hint=(1, 1), pos_hint={"x": 0, "y": 0})

        with self._main.canvas.before:
            Color(*Colors.WHITE)
            self._main_bg = Rectangle(pos=self._main.pos, size=self._main.size)
        self._main.bind(
            pos=lambda w, _: setattr(self._main_bg, 'pos', w.pos),
            size=lambda w, _: setattr(self._main_bg, 'size', w.size)
        )
        self._root.add_widget(self._main)

        self.content_area = BoxLayout(orientation="vertical",
                                      padding=[dp(16), dp(32)],
                                      spacing=dp(10))
        self.content_area.bind(minimum_height=self.content_area.setter("height"))
        self._main.add_widget(self.content_area)

        self._build_login()

        self.build_content()

    # ── Overrideable ──────────────────────────────────────────────────────────

    def build_content(self):
        """Subclasses populate self.content_area here."""
        pass

    def header_title(self) -> str:
        return "ZIPPY"

    def header_subtitle(self) -> str:
        return ""

    def active_nav(self) -> str:
        return "home"

    # ── Internal builders ─────────────────────────────────────────────────────

    def _build_header(self):
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=self.HEADER_HEIGHT,
            padding=[dp(16), dp(8)],
        )
        with header.canvas.before:
            Color(*Colors.BLUE)
            self._header_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self._upd_header, size=self._upd_header)

        # Logo row
        logo_row = BoxLayout(orientation="horizontal")
        logo_lbl = Label(
            text="[b]ZIPP[/b][color=f5a623]Y[/color]",
            markup=True,
            font_size=dp(22),
            color=Colors.WHITE,
            halign="left",
            size_hint_x=0.8,
        )
        logo_lbl.bind(size=logo_lbl.setter("text_size"))
        profile_btn = Label(text="PRF", font_size=dp(20), size_hint_x=0.2,
                            halign="right")
        profile_btn.bind(size=profile_btn.setter("text_size"))
        logo_row.add_widget(logo_lbl)
        logo_row.add_widget(profile_btn)
        header.add_widget(logo_row)

        sub = self.header_subtitle()
        if sub:
            sub_lbl = Label(
                text=sub,
                font_size=dp(12),
                color=(0.8, 0.9, 1, 1),
                halign="left",
                size_hint_y=None,
                height=dp(18),
            )
            sub_lbl.bind(size=sub_lbl.setter("text_size"))
            header.add_widget(sub_lbl)

        self._main.add_widget(header)

    def _upd_header(self, widget, *_):
        self._header_bg.pos  = widget.pos
        self._header_bg.size = widget.size


    def _on_fab(self, *_):
        self.app.shipment_service.new_shipment()
        self.go_to("step1")

    def on_enter(self):
        """Update nav manager reference once screen is active."""
        if hasattr(self, "_nav"):
            self._nav.sm = self.manager

    # ── Navigation helpers ────────────────────────────────────────────────────

    def go_to(self, screen_name: str, direction: str = "left"):
        self.manager.transition = __import__(
            "kivy.uix.screenmanager", fromlist=["SlideTransition"]
        ).SlideTransition(direction=direction)
        self.manager.current = screen_name

    @property
    def app(self):
        return App.get_running_app()

    def _build_login(self):
        login_window = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint=(0.8, None),
            height=dp(200),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=[0, Window.height * 0.4],
        )

        label = ZippyLabel(
            text="Prihlasovanie",
            color=Colors.BLUE,
            font_size=dp(20),
            size_hint_y=None,
            height=dp(40),
        )

        self.email = ZippyInput(hint_text="Email", size_hint_x=1)
        self.password = ZippyInput(hint_text="Heslo", size_hint_x=1, password=True)

        login_btn = RoundedButton(
            text="Prihlásiť sa",
            bg_color=Colors.ORANGE,
            size_hint_y=None,
            height=dp(44),
        )

        login_btn.bind(on_press=self._on_login_verify)

        self.error_label = ZippyLabel(text="", color=(1, 0, 0, 1), size_hint_y=None, height=dp(24))

        login_window.add_widget(label)
        login_window.add_widget(self.email)
        login_window.add_widget(self.password)
        login_window.add_widget(login_btn)

        self.content_area.add_widget(login_window)
        return login_window

    def _on_login_verify(self, *_):
        result = AuthService().login(self.email.text, self.password.text)

        if not result["success"]:
            self.error_label.text = result["error"]
            return

        if result["role"] == "customer":
            self.go_to("home")
        elif result["role"] == "courier":
            self.go_to("courier_home")
