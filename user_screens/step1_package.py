"""
user_screens/step1_package.py – Krok 1: Rozmery a obsah balíka (UC03).
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

from user_screens.base_screen import BaseScreen
from services.validation import validate_package
from theme import Colors, StepIndicator, RoundedButton, ZippyInput, make_label, ZippyLabel


class Step1PackageScreen(BaseScreen):
    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "home"

    def build_content(self):
        # Indikátor krokov uzamknutý pod hlavičkou
        indicator = StepIndicator(current_step=1, size_hint_y=None, height=dp(54))
        self.step_bar.height = dp(54)
        self.step_bar.add_widget(indicator)

        ca = self.content_area
        ca.add_widget(self._section_label("Rozmery"))

        # Pomocný label s jednotkou cm za každým poľom
        def unit_label():
            return ZippyLabel(text="cm", font_size=dp(13), color=Colors.DARK_TEXT, size_hint_x=0.1)

        # Mriežka 6 stĺpcov: pole X, cm, pole Y, cm, pole Z, cm
        size_row = GridLayout(cols=6, spacing=dp(8),
                              size_hint_y=None, height=dp(40))
        self.inp_x = ZippyInput(hint_text="X", input_filter="int")
        self.inp_y = ZippyInput(hint_text="Y", input_filter="int")
        self.inp_z = ZippyInput(hint_text="Z", input_filter="int")
        size_row.add_widget(self.inp_x)
        size_row.add_widget(unit_label())
        size_row.add_widget(self.inp_y)
        size_row.add_widget(unit_label())
        size_row.add_widget(self.inp_z)
        size_row.add_widget(unit_label())
        ca.add_widget(size_row)

        # Hmotnosť — max 40 kg podľa validácie
        ca.add_widget(self._section_label("Hmotnosť"))
        weight_row = BoxLayout(orientation="horizontal", spacing=dp(6),
                               size_hint_y=None, height=dp(40))
        self.inp_weight = ZippyInput(hint_text="max: 40", input_filter="int")
        kg_lbl = Label(text="KG", font_size=dp(13), bold=True,
                       color=Colors.DARK_TEXT,
                       size_hint=(None, None), size=(dp(30), dp(40)))
        weight_row.add_widget(self.inp_weight)
        weight_row.add_widget(kg_lbl)
        ca.add_widget(weight_row)

        # Obsah balíka — voliteľné pole
        ca.add_widget(self._section_label("Obsah"))
        self.inp_contents = ZippyInput(hint_text="")
        ca.add_widget(self.inp_contents)

        # Špeciálne inštrukcie — voliteľné viacriadkové pole
        ca.add_widget(self._section_label("Špeciálne inštrukcie"))
        from kivy.uix.textinput import TextInput
        self.inp_instructions = TextInput(
            multiline=True,
            background_color=Colors.LIGHT_GRAY,
            foreground_color=Colors.DARK_TEXT,
            font_size=dp(13),
            size_hint_y=None,
            height=dp(80),
            padding=[dp(10), dp(8)],
        )
        ca.add_widget(self.inp_instructions)

        ca.add_widget(Label(size_hint_y=1))
        ca.add_widget(self._nav_buttons())

    def _section_label(self, text):
        lbl = Label(
            text=text,
            font_size=dp(13),
            bold=True,
            color=Colors.DARK_TEXT,
            halign="left",
            size_hint_y=None,
            height=dp(22),
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _nav_buttons(self):
        row = BoxLayout(orientation="horizontal", spacing=dp(12),
                        size_hint_y=None, height=dp(48))
        back_btn = RoundedButton(
            text="<- Späť",
            bg_color=Colors.MID_GRAY,
            size_hint_x=0.4,
        )
        back_btn.bind(on_release=lambda *_: self.go_to("home", "right"))

        next_btn = RoundedButton(
            text="Pokračovať ->",
            bg_color=Colors.ORANGE,
            size_hint_x=0.6,
        )
        next_btn.bind(on_release=self._on_next)

        container = BoxLayout(orientation="vertical", spacing=dp(12))
        # Chybová hláška validácie — skrytá kým nie je chyba
        self.lbl_error = ZippyLabel(text="", color=get_color_from_hex("#FF0000"),
                                    padding=[dp(10), dp(8)])
        row.add_widget(back_btn)
        row.add_widget(next_btn)
        container.add_widget(self.lbl_error)
        container.add_widget(row)
        return container

    def _on_next(self, *_):
        # Validácia vstupov pred uložením — chyba sa zobrazí inline
        error = validate_package(
            self.inp_x.text, self.inp_y.text,
            self.inp_z.text, self.inp_weight.text
        )
        if error:
            self.lbl_error.text = error
            return

        self.lbl_error.text = ""
        # Uloženie do ShipmentService a prechod na krok 2
        self.app.shipment_service.save_package_details(
            x=int(self.inp_x.text),
            y=int(self.inp_y.text),
            z=int(self.inp_z.text),
            weight=float(self.inp_weight.text),
            contents=self.inp_contents.text,
            instructions=self.inp_instructions.text,
        )
        self.go_to("step2")