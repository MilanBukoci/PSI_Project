"""
user_screens/base_screen.py – Base class all Zippy user_screens inherit from.
"""

import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.app import App

from theme import Colors, RoundedButton, BottomNav


class BaseScreen(Screen):
    """
    Provides the common shell:
      ┌──────────────────┐
      │   Blue Header    │
      ├──────────────────┤
      │   content_area   │  ← subclasses fill this
      ├──────────────────┤
      │    Bottom Nav    │
      └──────────────────┘
    Plus a floating orange + FAB button.
    """

    HEADER_HEIGHT = dp(80)
    NAV_HEIGHT    = dp(60)
    FAB_SIZE      = dp(58)

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

        self._build_header()

        # Step indicator slot — empty by default
        self.step_bar = BoxLayout(size_hint_y=None, height=0)


        self._main.add_widget(self.step_bar)

        self.content_area = BoxLayout(orientation="vertical",
                                      padding=[dp(16), dp(32)],
                                      spacing=dp(10))
        self.content_area.bind(minimum_height=self.content_area.setter("height"))
        self._main.add_widget(self.content_area)
        self._build_nav()
        self._build_fab()

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
        header_icon_path = os.path.join(os.path.dirname(__file__), "..", "images", "zippy_icon.png")
        profile_btn = Image(
            source=os.path.abspath(header_icon_path),
            size_hint=(None, None),
            size=(dp(70), dp(70)),
            allow_stretch=True,
            keep_ratio=True,
        )
        icon_wrap = FloatLayout(size_hint_x=0.28)
        profile_btn.pos_hint = {"right": 0.98, "center_y": 0.36}
        icon_wrap.add_widget(profile_btn)
        logo_row.add_widget(logo_lbl)
        logo_row.add_widget(icon_wrap)
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

    def _build_nav(self):
        nav = BottomNav(active=self.active_nav(),
                        screen_manager=self.manager)
        nav.size_hint_y = None
        nav.height = self.NAV_HEIGHT
        self._main.add_widget(nav)
        # Keep reference so we can pass manager after it's set
        self._nav = nav

    def _build_fab(self):
        fab = RoundedButton(
            text="",
            bg_color=Colors.ORANGE,
            radius=dp(29),
            size_hint=(None, None),
            size=(self.FAB_SIZE, self.FAB_SIZE),
            pos_hint={"center_x": 0.5},
            font_size=dp(32),
        )
        fab.bold = True
        fab.color = Colors.WHITE
        fab.pos_hint = {"center_x": 0.5, "top": 0.118}  # adjust to move up/down
        plus_icon_path = os.path.join(os.path.dirname(__file__), "..", "images", "plus.png")
        plus_icon_path = os.path.abspath(plus_icon_path)
        with fab.canvas.after:
            Color(1, 1, 1, 0.9)
            self._fab_outline = Line(rounded_rectangle=(fab.x, fab.y, fab.width, fab.height, dp(29)), width=dp(1.4))
        self._fab_icon = Image(
            source=plus_icon_path,
            size_hint=(None, None),
            size=(dp(22), dp(22)),
            allow_stretch=True,
            keep_ratio=True,
        )
        fab.add_widget(self._fab_icon)
        fab.bind(pos=self._update_fab_outline, size=self._update_fab_outline)
        fab.bind(pos=self._update_fab_icon, size=self._update_fab_icon)
        fab.bind(on_release=self._on_fab)
        self._root.add_widget(fab)
        self._fab = fab
        self._update_fab_icon(fab)

    def _update_fab_outline(self, widget, *_):
        self._fab_outline.rounded_rectangle = (
            widget.x,
            widget.y,
            widget.width,
            widget.height,
            dp(29),
        )

    def _update_fab_icon(self, widget, *_):
        icon_size = dp(22)
        self._fab_icon.size = (icon_size, icon_size)
        self._fab_icon.pos = (
            widget.x + (widget.width - icon_size) / 2,
            widget.y + (widget.height - icon_size) / 2,
        )

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


class CourierBaseScreen(BaseScreen):
    """Base screen pre kuriérske obrazovky — bez nav baru a FAB."""

    def _build_nav(self):
        pass  # kuriér nemá bottom nav

    def _build_fab(self):
        pass