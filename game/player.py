from dataclasses import dataclass, field

from game.card import Card
from game.cell import Prototype


@dataclass
class Player:
    name: str
    color: tuple[int, int, int]
    prototype: Prototype = field(default_factory=Prototype)
    units: list[float] = field(default_factory=list)   # frozen kWh per built unit
    hand: list[Card] = field(default_factory=list)
    banked_kwh: float = 0.0
    farm_bonus: float = 0.0        # additive; total multiplier = 1.0 + farm_bonus
    skip_score: bool = False       # Grid Failure effect
    halved_turns: int = 0          # Dust Storm effect (turns remaining)
    blocked_areas: set[str] = field(default_factory=set)
    HAND_LIMIT: int = 6

    def total_output(self) -> float:
        """kWh earned per score phase (sum of all built units, modified by active effects)."""
        raw = sum(self.units)
        if self.halved_turns > 0:
            raw *= 0.5
        return raw * (1.0 + self.farm_bonus)

    def build_unit(self) -> float:
        """Snapshot the prototype's current output as a new frozen unit. Returns kWh."""
        kwh = self.prototype.kwh_output()
        self.units.append(kwh)
        return kwh

    def discard_top_hand_card(self) -> 'Card | None':
        return self.hand.pop(-1) if self.hand else None
