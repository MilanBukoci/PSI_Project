from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle

from theme import Colors, RoundedButton
from user_screens.base_screen import CourierBaseScreen as BaseScreen


class UC04NotificationsScreen(BaseScreen):
    """Simple courier notifications screen."""

    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def on_enter(self):
        super().on_enter()
        self.content_area.clear_widgets()
        self.build_content()

    def build_content(self):
        ca = self.content_area

        title = Label(
            text="[b]Upozornenia kuriéra[/b]",
            markup=True,
            font_size=dp(18),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(30),
            halign="left",
        )
        title.bind(size=title.setter("text_size"))
        ca.add_widget(title)

        notifications = self.app.notification_service.get_for_role("courier")
        scroll = ScrollView(size_hint_y=1)
        col = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))

        if not notifications:
            empty = Label(
                text="Zatiaľ nemáte žiadne upozornenia.",
                font_size=dp(13),
                color=Colors.MID_GRAY,
                size_hint_y=None,
                height=dp(34),
                halign="center",
            )
            empty.bind(size=empty.setter("text_size"))
            col.add_widget(empty)
        else:
            for note in reversed(notifications):
                row = BoxLayout(
                    orientation="vertical",
                    spacing=dp(2),
                    size_hint_y=None,
                    height=dp(66),
                    padding=[dp(8), dp(6)],
                )
                with row.canvas.before:
                    Color(*Colors.LIGHT_GRAY)
                    bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(8)])
                row.bind(
                    pos=lambda w, _, bg=bg: setattr(bg, "pos", w.pos),
                    size=lambda w, _, bg=bg: setattr(bg, "size", w.size),
                )

                msg = Label(
                    text=note.get("message", ""),
                    font_size=dp(12),
                    color=Colors.DARK_TEXT,
                    halign="left",
                    valign="middle",
                )
                msg.bind(size=lambda inst, _: setattr(inst, "text_size", (inst.width, None)))
                stamp = Label(
                    text=note.get("created_at", ""),
                    font_size=dp(10),
                    color=Colors.MID_GRAY,
                    halign="right",
                    size_hint_y=None,
                    height=dp(14),
                )
                stamp.bind(size=stamp.setter("text_size"))
                row.add_widget(msg)
                row.add_widget(stamp)
                col.add_widget(row)

        scroll.add_widget(col)
        ca.add_widget(scroll)

        back_btn = RoundedButton(
            text="Späť",
            bg_color=Colors.MID_GRAY,
            size_hint_y=None,
            height=dp(42),
        )
        back_btn.bind(on_release=lambda *_: self.go_to(getattr(self.app, "uc04_return_screen", "uc04_list"), "right"))
        ca.add_widget(back_btn)
