"""
Zippy – UC03: Vytvorenie objednávky / Odoslanie balíka
OOP-compliant Kivy application with socket stubs.
"""

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition

import login_screen
from services.uc04_delivery_service import UC04DeliveryService
from user_screens.home import HomeScreen
from user_screens.step1_package import Step1PackageScreen
from user_screens.step2_addresses import Step2AddressesScreen
from user_screens.step3_payment import Step3PaymentScreen
from user_screens.step4_confirm import Step4ConfirmScreen
from services.socket_service import SocketService
from services.shipment_service import ShipmentService

from courier_screens.uc04_shipment_list import UC04ShipmentListScreen
from courier_screens.uc04_pickup import UC04PickupScreen
from courier_screens.uc04_route_and_detail import UC04RouteScreen
from courier_screens.uc04_route_and_detail import UC04DetailScreen
from courier_screens.uc04_confirm_and_unavailable import UC04ConfirmDeliveryScreen
from courier_screens.uc04_confirm_and_unavailable import UC04Unavailable1Screen
from courier_screens.uc04_confirm_and_unavailable import UC04Unavailable2Screen

# ── Teammate screen imports go here ──────────────────────────────────────────
# Tomáš  (UC01): from user_screens.uc01_redirect import UC01RedirectScreen
# Adam   (UC02): from user_screens.uc02_assign  import UC02AssignScreen
# Importing the screen file automatically registers it on HomeScreen.
# -----------------------------------------------------------------------------

Window.size = (400, 700)

KV = """
#:import SlideTransition kivy.uix.screenmanager.SlideTransition

ScreenManager:
    LoginScreen:
        name: 'login'
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
        
    # ── UC04 (Milan) ──────────────────────────────────────────────────────────
    UC04ShipmentListScreen:
        name: 'uc04_list'
    UC04PickupScreen:
        name: 'uc04_pickup'
    UC04RouteScreen:
        name: 'uc04_route'
    UC04DetailScreen:
        name: 'uc04_detail'
    UC04ShipmentInfoScreen:
        name: 'uc04_shipment_info'
    UC04ConfirmDeliveryScreen:
        name: 'uc04_confirm'
    UC04Unavailable1Screen:
        name: 'uc04_unavailable_1'
    UC04Unavailable2Screen:
        name: 'uc04_unavailable_2'

    # Tomáš (UC01) — add: UC01RedirectScreen: / name: 'uc01_redirect'
    # Adam  (UC02) — add: UC02AssignScreen:   / name: 'uc02_assign'
"""

class ZippyApp(App):


    def build(self):
        self.title = "Zippy"

        self.socket_service = SocketService()
        self.shipment_service = ShipmentService()
        self.uc04_service = UC04DeliveryService()  # UC04
        # uc04_selected_id stores which shipment is currently being delivered
        self.uc04_selected_id: str | None = None

        self.socket_service.connect()

        return Builder.load_string(KV)

    def on_stop(self):
        self.socket_service.disconnect()


if __name__ == "__main__":
    ZippyApp().run()