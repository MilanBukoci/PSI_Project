"""
models/shipment.py – Order and Address data classes.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import uuid


@dataclass
class PackageDetails:
    size_x: float = 0.0
    size_y: float = 0.0
    size_z: float = 0.0
    weight: float = 0.0
    contents: str = ""
    special_instructions: str = ""


@dataclass
class Address:
    first_name: str = ""
    last_name: str = ""
    street: str = ""
    postal_code: str = ""


@dataclass
class Shipment:
    id: str                          = field(default_factory=lambda: f"ZP-{uuid.uuid4().hex[:8].upper()}")
    package: PackageDetails          = field(default_factory=PackageDetails)
    sender: Address                  = field(default_factory=Address)
    recipient: Address               = field(default_factory=Address)
    payment_method: str              = "card"
    status: str                      = "pending"
    route: str                       = "NOT SPECIFIED"
    delivery_days: int               = 2
    price: float                     = 4.99
    assigned_courier_id: str | None  = None
    delivery_date: date | None       = None

    # ── UC04 courier delivery fields ──────────────────────────────────────────
    pin: str = ""
    phone: str = ""
    section: str = ""
    rack: str = ""
    police: str = ""
    size: str = ""

    def summary_lines(self):
        return [
            ("Rozmery",   f"{self.package.size_x}x{self.package.size_y}x{self.package.size_z} cm"),
            ("Hmotnosť",  f"{self.package.weight} kg"),
            ("Trasa",     self.route),
            ("Doručenie", f"{self.delivery_days} dni"),
        ]
