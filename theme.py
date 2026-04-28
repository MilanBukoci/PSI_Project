"""
theme.py – Zippy design tokens and reusable base widgets.
"""

import os

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp


# ── Colour palette ────────────────────────────────────────────────────────────
class Colors:
    BLUE        = (0.169, 0.169, 1.0, 1)       # #2B2BFF
    ORANGE      = (0.961, 0.651, 0.137, 1)     # #F5A623
    WHITE       = (1, 1, 1, 1)
    LIGHT_GRAY  = (0.94, 0.94, 0.94, 1)
    MID_GRAY    = (0.75, 0.75, 0.75, 1)
    DARK_TEXT   = (0.1, 0.1, 0.1, 1)
    ERROR_RED   = (0.95, 0.27, 0.27, 1)
    SUCCESS_GRN = (0.18, 0.8, 0.44, 1)
    NAV_BG      = (1, 1, 1, 1)
    STEP_INACTIVE = (0.8, 0.8, 0.8, 1)


# ── Typography helper ─────────────────────────────────────────────────────────
def make_label(text="", font_size=14, bold=False, color=None, **kwargs):
    color = color or Colors.DARK_TEXT
    lbl = Label(
        text=text,
        font_size=dp(font_size),
        bold=bold,
        color=color,
        **kwargs
    )
    return lbl


# ── Rounded button ────────────────────────────────────────────────────────────
class RoundedButton(Button):
    """A button with rounded corners and custom bg colour."""

    def __init__(self, bg_color=None, radius=dp(8), **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color or Colors.ORANGE
        self.radius = radius
        self.background_color = (0, 0, 0, 0)   # hide default bg
        self.color = Colors.WHITE
        self.bold = True
        self.font_size = dp(15)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.radius])

    def set_bg(self, color):
        self.bg_color = color
        self._draw()


# ── Styled text input ─────────────────────────────────────────────────────────
class ZippyInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("background_color", Colors.LIGHT_GRAY)
        kwargs.setdefault("foreground_color", Colors.DARK_TEXT)
        kwargs.setdefault("font_size", dp(14))
        kwargs.setdefault("padding", [dp(10), dp(8)])
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(40))
        super().__init__(**kwargs)

# --styled label--------------
class ZippyLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# ── Step indicator ────────────────────────────────────────────────────────────
class _StepCircle(Widget):
    def __init__(self, number, active, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(28), dp(28)))
        super().__init__(**kwargs)
        self.number = number
        self.active = active

        self._lbl = Label(
            text=str(number),
            font_size=dp(13),
            bold=True,
            color=Colors.WHITE,
        )
        self.add_widget(self._lbl)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        color = Colors.ORANGE if self.active else Colors.STEP_INACTIVE
        with self.canvas:
            Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self._lbl.center = self.center
        self._lbl.size = self.size


class StepIndicator(BoxLayout):
    STEPS = ["Balík", "Adresy", "Platba", "Potvrdenie"]

    def __init__(self, current_step=1, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(54))
        kwargs.setdefault("padding", [dp(12), dp(4)])
        kwargs.setdefault("spacing", dp(4))
        super().__init__(**kwargs)
        self.current_step = current_step
        self._build()

    def _build(self):
        self.clear_widgets()
        for i, label in enumerate(self.STEPS, start=1):
            col = BoxLayout(
                orientation="vertical",
                spacing=dp(2),
                size_hint_x=1,
            )
            active = (i == self.current_step)

            circle = _StepCircle(
                number=i,
                active=active,
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                pos_hint={"center_x": 0.5},
            )
            col.add_widget(circle)

            lbl = Label(
                text=label,
                font_size=dp(10),
                color=Colors.ORANGE if active else Colors.MID_GRAY,
                bold=active,
                size_hint_y=None,
                height=dp(14),
            )
            col.add_widget(lbl)
            self.add_widget(col)

            if i < len(self.STEPS):
                line = Widget(size_hint_x=0.3)

                def redraw(w, *_):
                    w.canvas.clear()
                    with w.canvas:
                        Color(*Colors.MID_GRAY)
                        Rectangle(
                            pos=(w.x, w.y + w.height - dp(14) - dp(1)),
                            size=(w.width, dp(2))
                        )

                line.bind(pos=redraw, size=redraw)
                self.add_widget(line)

# ── Bottom nav bar ────────────────────────────────────────────────────────────
class BottomNav(BoxLayout):
    NAV_ITEMS = [
        ("home.png", "Domov", "home"),
        ("search.png", "Sledovať", "uc01_redirect"),
        ("plan.png", "Naplánovať", None),
        ("user.png", "Profil", "profile"),
    ]

    def __init__(self, active="home", screen_manager=None, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(60))
        super().__init__(**kwargs)
        self.active = active
        self.sm = screen_manager

        with self.canvas.before:
            # White background
            Color(*Colors.WHITE)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            # Top border line
            Color(*Colors.MID_GRAY)
            self._border = Rectangle(pos=self.pos, size=(self.width, dp(1)))

        self.bind(pos=self._update_bg, size=self._update_bg)
        self._build()

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.pos = (self.x, self.top - dp(1))  # top edge
        self._border.size = (self.width, dp(1))

    def _build(self):
        for icon, label, target in self.NAV_ITEMS:
            btn = self._make_nav_btn(icon, label, target)
            self.add_widget(btn)

    def _make_nav_btn(self, icon_file, label, target):
        col = BoxLayout(orientation="vertical", padding=[0, dp(4)])
        is_active = (target == self.active)
        icon_path = os.path.join(os.path.dirname(__file__), "images", icon_file)

        icon_img = Image(
            source=icon_path,
            size_hint_y=None,
            height=dp(20),
            allow_stretch=True,
            keep_ratio=True,
            color=Colors.DARK_TEXT if is_active else Colors.MID_GRAY,
        )
        text_lbl = Label(
            text=label,
            font_size=dp(10),
            color=Colors.DARK_TEXT if is_active else Colors.MID_GRAY,
            bold=is_active,
        )
        col.add_widget(icon_img)
        col.add_widget(text_lbl)

        def on_press(instance, t=target):
            if t and self.sm:
                self.sm.current = t

        col.bind(on_touch_down=lambda w, touch:
        on_press(w) if w.collide_point(*touch.pos) else None)
        return col
