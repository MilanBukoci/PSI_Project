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
from services.uc02_dispatcher_service import UC02DispatcherService
from user_screens.home import HomeScreen
from user_screens.step1_package import Step1PackageScreen
from user_screens.step2_addresses import Step2AddressesScreen
from user_screens.step3_payment import Step3PaymentScreen
from user_screens.step4_confirm import Step4ConfirmScreen
from user_screens.uc01_redirect import (
    UC01RedirectScreen,
    UC01RedirectDetailScreen,
)
from user_screens.profile import ProfileScreen
from user_screens.notifications import NotificationsScreen
from services.socket_service import SocketService
from services.shipment_service import ShipmentService
from services.notification_service import NotificationService

from courier_screens.uc04_shipment_list import UC04ShipmentListScreen
from courier_screens.uc04_pickup import UC04PickupScreen
from courier_screens.uc04_route_and_detail import UC04RouteScreen
from courier_screens.uc04_route_and_detail import UC04DetailScreen
from courier_screens.uc04_confirm_and_unavailable import UC04ConfirmDeliveryScreen
from courier_screens.uc04_confirm_and_unavailable import UC04Unavailable1Screen
from courier_screens.uc04_confirm_and_unavailable import UC04Unavailable2Screen
from courier_screens.uc04_notifications import UC04NotificationsScreen

# ── UC02 (Adam) ──────────────────────────────────────────────────────────────
from dispatcher_screens.uc02_dispatcher import (
    UC02ShipmentListScreen,
    UC02CourierSelectScreen,
    UC02ConfirmScreen,
)
from dispatcher_screens.uc02_notifications import UC02NotificationsScreen
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
    ProfileScreen:
        name: 'profile'
    NotificationsScreen:
        name: 'notifications'
        
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
    UC04NotificationsScreen:
        name: 'uc04_notifications'

    UC01RedirectScreen:
        name: 'uc01_redirect'
    UC01RedirectDetailScreen:
        name: 'uc01_detail'
    # ── UC02 (Adam) ──────────────────────────────────────────────────────────
    UC02ShipmentListScreen:
        name: 'uc02_shipment_list'
    UC02CourierSelectScreen:
        name: 'uc02_courier_select'
    UC02ConfirmScreen:
        name: 'uc02_confirm'
    UC02NotificationsScreen:
        name: 'uc02_notifications'
"""

class ZippyApp(App):


    def build(self):
        self.title = "Zippy"

        self.socket_service = SocketService()
        self.shipment_service = ShipmentService()
        self.notification_service = NotificationService()
        self.uc04_service = UC04DeliveryService()  # UC04
        self.uc02_service = UC02DispatcherService()  # UC02
        # uc04_selected_id stores which shipment is currently being delivered
        self.uc04_selected_id: str | None = None
        self.uc04_return_screen: str = "uc04_list"
        self.uc01_selected_id: str | None = None
        self.uc01_return_screen: str = "uc01_redirect"
        # UC02 dispatcher state
        self.uc02_selected_shipments: list = []
        self.uc02_selected_courier_id: str | None = None
        self.uc02_return_screen: str = "uc02_shipment_list"
        self.user_name: str = ""

        self.socket_service.connect()

        return Builder.load_string(KV)

    def on_stop(self):
        self.socket_service.disconnect()


if __name__ == "__main__":
    ZippyApp().run()