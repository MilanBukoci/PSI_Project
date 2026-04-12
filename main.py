"""
Zippy – UC03: Vytvorenie objednávky / Odoslanie balíka
OOP-compliant Kivy application with socket stubs.
"""

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from screens.home import HomeScreen
from screens.step1_package import Step1PackageScreen
from screens.step2_addresses import Step2AddressesScreen
from screens.step3_payment import Step3PaymentScreen
from screens.step4_confirm import Step4ConfirmScreen
from services.socket_service import SocketService
from services.shipment_service import ShipmentService

# ── Teammate screen imports go here ──────────────────────────────────────────
# Tomáš  (UC01): from screens.uc01_redirect import UC01RedirectScreen
# Adam   (UC02): from screens.uc02_assign  import UC02AssignScreen
# Milan  (UC04): from screens.uc04_deliver import UC04DeliverScreen
# Importing the screen file automatically registers it on HomeScreen.
# -----------------------------------------------------------------------------

Window.size = (400, 700)

KV = """
#:import SlideTransition kivy.uix.screenmanager.SlideTransition

ScreenManager:
    HomeScreen:
        name: 'home'
    Step1PackageScreen:
        name: 'step1'
    Step2AddressesScreen:
        name: 'step2'
    Step3PaymentScreen:
        name: 'step3'
    Step4ConfirmScreen:
        name: 'step4'

    # Tomáš (UC01) — add: UC01RedirectScreen: / name: 'uc01_redirect'
    # Adam  (UC02) — add: UC02AssignScreen:   / name: 'uc02_assign'
    # Milan (UC04) — add: UC04DeliverScreen:  / name: 'uc04_deliver'
"""

class ZippyApp(App):


    def build(self):
        self.title = "Zippy"

        self.socket_service = SocketService()
        self.shipment_service = ShipmentService()

        self.socket_service.connect()

        return Builder.load_string(KV)

    def on_stop(self):
        self.socket_service.disconnect()


if __name__ == "__main__":
    ZippyApp().run()