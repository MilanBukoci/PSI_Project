"""
models/courier.py – Courier data class. Used by UC02 (Adam) and UC04 (Milan).
"""

from dataclasses import dataclass, field


@dataclass
class Courier:
    id: str
    name: str
    is_available: bool = True
    current_load: int = 0        # number of shipments currently assigned
    max_load: int = 10           # UC02 uses this to check if courier is full