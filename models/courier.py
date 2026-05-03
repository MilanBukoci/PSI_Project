"""
Courier – doménový model. UC02 používa is_available + current_load/max_load pri pridelení;
UC04 rieši doručovanie jedného kuriéra v ďalšom use case.
"""

from dataclasses import dataclass, field


@dataclass
class Courier:
    id: str
    name: str
    is_available: bool = True
    current_load: int = 0        # aktuálny počet zásielok; UC02 atomicky bump po úspešnom assign
    max_load: int = 10           # horný limit paralelných zásielok pri validácii UC02