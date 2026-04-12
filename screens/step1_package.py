"""
screens/step1_package.py – Step 1: Package dimensions & contents.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from screens.base_screen import BaseScreen
from theme import Colors, StepIndicator, RoundedButton, ZippyInput, make_label


class Step1PackageScreen(BaseScreen):
    def header_subtitle(self):
        return "COURIER SERVICES s.r.o."

    def active_nav(self):
        return "home"

    def build_content(self):
        # Lock step bar below header
        indicator = StepIndicator(current_step=1, size_hint_y=None, height=dp(54))
        self.step_bar.height = dp(54)
        self.step_bar.add_widget(indicator)

        # Rest goes into content_area as normal
        ca = self.content_area
        ca.add_widget(self._section_label("Rozmery"))

        size_row = GridLayout(cols=3, spacing=dp(8),
                              size_hint_y=None, height=dp(40))
        self.inp_x = ZippyInput(hint_text="X")
        self.inp_y = ZippyInput(hint_text="Y")
        self.inp_z = ZippyInput(hint_text="Z")
        size_row.add_widget(self.inp_x)
        size_row.add_widget(self.inp_y)
        size_row.add_widget(self.inp_z)
        ca.add_widget(size_row)

        # Hmotnosť
        ca.add_widget(self._section_label("Hmotnosť"))
        weight_row = BoxLayout(orientation="horizontal", spacing=dp(6),
                               size_hint_y=None, height=dp(40))
        self.inp_weight = ZippyInput(hint_text="")
        kg_lbl = Label(text="KG", font_size=dp(13), bold=True,
                       color=Colors.DARK_TEXT,
                       size_hint=(None, None), size=(dp(30), dp(40)))
        weight_row.add_widget(self.inp_weight)
        weight_row.add_widget(kg_lbl)
        ca.add_widget(weight_row)

        # Obsah
        ca.add_widget(self._section_label("Obsah"))
        self.inp_contents = ZippyInput(hint_text="")
        ca.add_widget(self.inp_contents)

        # Špeciálne inštrukcie
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

        # Spacer
        ca.add_widget(Label(size_hint_y=1))

        # Nav buttons
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

        row.add_widget(back_btn)
        row.add_widget(next_btn)
        return row

    def _on_next(self, *_):
        self.app.shipment_service.save_package_details(
            x=self.inp_x.text,
            y=self.inp_y.text,
            z=self.inp_z.text,
            weight=self.inp_weight.text,
            contents=self.inp_contents.text,
            instructions=self.inp_instructions.text,
        )
        self.go_to("step2")
