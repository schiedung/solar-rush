from dataclasses import dataclass, field

from game.card import Card
from game.cell import SolarCell


@dataclass
class Player:
    name: str
    color: tuple[int, int, int]
    farm: list[SolarCell] = field(default_factory=lambda: [SolarCell()])
    hand: list[Card] = field(default_factory=list)
    banked_kwh: float = 0.0
    farm_bonus: float = 0.0       # additive; total multiplier = 1.0 + farm_bonus
    skip_score: bool = False      # Grid Failure effect
    halved_turns: int = 0         # Dust Storm effect (turns remaining)
    blocked_areas: set[str] = field(default_factory=set)  # Patent Block
    HAND_LIMIT: int = 6

    def total_output(self) -> float:
        raw = sum(c.kwh_output() for c in self.farm)
        if self.halved_turns > 0:
            raw *= 0.5
        return raw * (1.0 + self.farm_bonus)

    def discard_top_hand_card(self) -> 'Card | None':
        if self.hand:
            return self.hand.pop(-1)
        return None
