"""
user_screens/step2_addresses.py – Krok 2: Adresy odosielateľa a príjemcu (UC03).
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from user_screens.base_screen import BaseScreen
from theme import Colors, StepIndicator, RoundedButton, ZippyInput


class AddressColumn(BoxLayout):
    """Jeden stĺpec adresy (Odosielateľ alebo Príjemca) so štyrmi poľami."""

    def __init__(self, title, bg_color, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6),
                         padding=[dp(8), dp(8)], **kwargs)
        # Farebné pozadie stĺpca — oranžové pre odosielateľa, sivé pre príjemcu
        with self.canvas.before:
            Color(*bg_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(10)])
        self.bind(pos=self._draw, size=self._draw)

        title_lbl = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            font_size=dp(13),
            color=Colors.DARK_TEXT,
            size_hint_y=None,
            height=dp(22),
        )
        self.add_widget(title_lbl)

        self.inp_first  = self._field("Meno")
        self.inp_last   = self._field("Priezvisko")
        self.inp_street = self._field("Ulica")
        self.inp_psc    = self._field("PSČ")

    def _field(self, hint):
        # Každé pole má label nad sebou a ZippyInput pod ním
        lbl = Label(text=hint, font_size=dp(11), color=Colors.DARK_TEXT,
                    size_hint_y=None, height=dp(16), halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        self.add_widget(lbl)
        inp = ZippyInput(hint_text="")
        self.add_widget(inp)
        return inp

    def _draw(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def get_data(self):
        """Vráti slovník s hodnotami polí na uloženie do ShipmentService."""
        return {
            "first_name":  self.inp_first.text,
            "last_name":   self.inp_last.text,
            "street":      self.inp_street.text,
            "postal_code": self.inp_psc.text,
        }


class Step2AddressesScreen(BaseScreen):
    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "home"

    def build_content(self):
        ca = self.content_area
        ca.add_widget(StepIndicator(current_step=2,
                                    size_hint_y=None, height=dp(54)))

        scroll = ScrollView(size_hint_y=1)
        inner = BoxLayout(orientation="vertical", spacing=dp(10),
                          size_hint_y=None, padding=[0, dp(4)])
        inner.bind(minimum_height=inner.setter("height"))

        # Dvojstĺpcové rozloženie: odosielateľ vľavo, príjemca vpravo
        cols = BoxLayout(orientation="horizontal", spacing=dp(10),
                         size_hint_y=None, height=dp(310))
        self.sender_col = AddressColumn(
            "ODOSIELATEĽ",
            bg_color=(0.996, 0.851, 0.502, 1),  # soft orange
        )
        self.recipient_col = AddressColumn(
            "PRÍJEMCA",
            bg_color=Colors.LIGHT_GRAY,
        )
        cols.add_widget(self.sender_col)
        cols.add_widget(self.recipient_col)
        inner.add_widget(cols)

        scroll.add_widget(inner)
        ca.add_widget(scroll)
        ca.add_widget(self._nav_buttons())

    def _nav_buttons(self):
        row = BoxLayout(orientation="horizontal", spacing=dp(12),
                        size_hint_y=None, height=dp(48))
        back = RoundedButton(text="<- Späť", bg_color=Colors.MID_GRAY,
                             size_hint_x=0.4)
        back.bind(on_release=lambda *_: self.go_to("step1", "right"))

        nxt = RoundedButton(text="Pokračovať ->", bg_color=Colors.ORANGE,
                            size_hint_x=0.6)
        nxt.bind(on_release=self._on_next)

        row.add_widget(back)
        row.add_widget(nxt)
        return row

    def _on_next(self, *_):
        # Uloženie adries do ShipmentService — nastaví aj trasu pre krok 3
        self.app.shipment_service.save_addresses(
            sender=self.sender_col.get_data(),
            recipient=self.recipient_col.get_data(),
        )
        self.go_to("step3")