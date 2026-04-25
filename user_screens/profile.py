from kivy.metrics import dp

from theme import Colors, RoundedButton
from user_screens.base_screen import BaseScreen


class ProfileScreen(BaseScreen):
    def active_nav(self):
        return "profile"

    def build_content(self):
        self.content_area.add_widget(RoundedButton(
            text="Odhlásiť sa",
            bg_color=Colors.ERROR_RED,
            size_hint_y=None,
            height=dp(48),
            on_release=self._on_logout,
        ))

    def _on_logout(self, *_):
        self.app.user_role = None
        self.app.user_name = ""
        self.go_to("login", "right")
