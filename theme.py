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
        kwargs.setdefault("size", (dp(28), dp(28)))  # keep square so it's a circle
        super().__init__(**kwargs)
        self.number = number
        self.active = active
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        color = Colors.ORANGE if self.active else Colors.STEP_INACTIVE
        with self.canvas:
            Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            Color(1, 1, 1, 1)
        lbl = Label(
            text=str(self.number),
            font_size=dp(12),
            bold=True,
            color=(1, 1, 1, 1),
            center=self.center,
            size=self.size,
        )
        # draw text via canvas
        from kivy.core.text import Label as CoreLabel
        core = CoreLabel(text=str(self.number), font_size=dp(12), bold=True)
        core.refresh()
        texture = core.texture
        tw, th = texture.size
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(
                texture=texture,
                pos=(self.center_x - tw/2, self.center_y - th/2),
                size=(tw, th)
            )



class StepIndicator(BoxLayout):
    STEPS = ["Balík", "Adresy", "Platba", "Potvrdenie"]

    def __init__(self, current_step=1, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(64))
        kwargs.setdefault("padding", [dp(16), dp(8)])
        kwargs.setdefault("spacing", dp(0))
        super().__init__(**kwargs)
        self.current_step = current_step
        self._circles = []
        self._build()
        self.bind(pos=self._draw_lines, size=self._draw_lines)

    def _build(self):
        self.clear_widgets()
        self._circles = []
        for i, label in enumerate(self.STEPS, start=1):
            col = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_x=1)
            active = (i == self.current_step)

            circle = _StepCircle(number=i, active=active,
                                 size_hint=(None, None), size=(dp(28), dp(28)),
                                 pos_hint={"center_x": 0.5})
            self._circles.append(circle)

            from kivy.uix.anchorlayout import AnchorLayout

            circle_wrap = AnchorLayout(
                anchor_x="center",
                anchor_y="center",
                size_hint_y=None,
                height=dp(28),
            )
            circle_wrap.add_widget(circle)
            col.add_widget(circle_wrap)

            lbl = Label(
                text=label,
                font_size=dp(10),
                color=Colors.ORANGE if active else Colors.MID_GRAY,
                bold=active,
                size_hint_y=None,
                height=dp(14),
                halign="center",
            )
            lbl.bind(size=lbl.setter("text_size"))
            col.add_widget(lbl)
            self.add_widget(col)


    def _draw_lines(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*Colors.WHITE)
            Rectangle(pos=self.pos, size=self.size)
        # draw lines between circles after they have positions
        from kivy.clock import Clock
        Clock.schedule_once(self._draw_lines_now, 0)

    def _draw_lines_now(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(*Colors.STEP_INACTIVE)
            for i in range(len(self._circles) - 1):
                c1 = self._circles[i]
                c2 = self._circles[i + 1]
                # line from right edge of c1 to left edge of c2, at circle center_y
                Rectangle(
                    pos=(c1.right, c1.center_y - dp(0.75)),
                    size=(c2.x - c1.right, dp(1.5))
                )

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
